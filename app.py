import os
import sys
import logging
import tempfile
import uuid
import traceback
import subprocess
import platform

import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify

from data_loader import load_dataset
from analyzer import analyze_dataset
from recommender import recommend_strategy

LOG_PATH = os.path.join(tempfile.gettempdir(), "alsr_app.log")
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info(f"Log file: {LOG_PATH}")


def _to_jsonable(obj):
    """Recursively convert numpy/pandas scalar types to plain Python types.

    The check_* modules return numpy int64/float64/bool_ values (e.g. class
    counts, correlation stats) straight out of pandas/numpy computations.
    Flask's default JSON encoder can't serialize those, so without this the
    /api/analyze response 500s on any dataset that actually trips a check
    (imbalance, missing values, etc.) — exactly the datasets this tool exists
    to flag.
    """
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return _to_jsonable(obj.tolist())
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def _base_dir():
    # When frozen by PyInstaller, bundled data lives under sys._MEIPASS
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


app = Flask(
    __name__,
    template_folder=os.path.join(_base_dir(), "templates"),
    static_folder=os.path.join(_base_dir(), "static"),
)


@app.errorhandler(Exception)
def handle_any_error(e):
    """Never let an unhandled exception fall through as an HTML page —
    the frontend expects JSON from every /api/* call."""
    tb = traceback.format_exc()
    logger.error(f"Unhandled exception: {e}\n{tb}")
    return jsonify({
        "status": "error",
        "message": f"{type(e).__name__}: {e}",
    }), 500
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "alsr_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory session store: token -> DataFrame
_SESSIONS = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    """Accept a dataset file, return its columns + a session token."""
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"status": "error", "message": "No file selected"}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".csv", ".xlsx", ".parquet"):
        return jsonify({"status": "error", "message": f"Unsupported file type '{ext}'"}), 400

    token = uuid.uuid4().hex
    temp_path = os.path.join(UPLOAD_DIR, f"{token}{ext}")
    file.save(temp_path)

    try:
        dataset = load_dataset(temp_path)
    except Exception as e:
        logger.exception("Failed to load dataset")
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    if dataset is None:
        return jsonify({"status": "error", "message": "Failed to parse dataset"}), 400

    _SESSIONS[token] = dataset

    return jsonify({
        "status": "success",
        "token": token,
        "filename": file.filename,
        "shape": list(dataset.shape),
        "columns": dataset.columns.tolist(),
        "preview": dataset.head(5).fillna("").astype(str).to_dict(orient="records"),
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get("token")
    target_column = payload.get("target_column")

    if not token or token not in _SESSIONS:
        return jsonify({"status": "error", "message": "Session expired. Please re-upload the dataset."}), 400
    if not target_column:
        return jsonify({"status": "error", "message": "Please select a target column."}), 400

    dataset = _SESSIONS[token]

    try:
        analysis_result = analyze_dataset(dataset, target_column)
    except Exception as e:
        logger.exception("Analysis failed")
        return jsonify({"status": "error", "message": str(e)}), 500

    if analysis_result.get("status") == "error":
        return jsonify({"status": "error", "message": analysis_result.get("message", "Analysis failed")}), 400

    response = {
        "status": "success",
        "dataset_info": {
            "shape": list(dataset.shape),
            "target_column": target_column,
        },
        "analysis": analysis_result,
        "recommendation": None,
    }

    if analysis_result["problems"]:
        try:
            rec = recommend_strategy(analysis_result["problems"])
        except Exception:
            logger.exception("recommend_strategy failed")
            rec = None
        if rec and rec.get("status") == "success":
            response["recommendation"] = rec

    return jsonify(_to_jsonable(response))


@app.route("/api/create-shortcut", methods=["POST"])
def create_shortcut():
    """Create a Desktop shortcut on request (the 'Desktop Shortcut' button in the UI).

    This is independent of the Inno Setup installer's own optional desktop-icon
    task — it lets someone add a shortcut at any time, straight from the running
    app, without reinstalling. Windows only (uses the WScript.Shell COM object
    via PowerShell, which ships with every Windows install — no extra
    dependency needed, so it keeps working in the frozen .exe).
    """
    if platform.system() != "Windows":
        return jsonify({
            "status": "error",
            "message": "Desktop shortcuts are only supported on Windows.",
        }), 400

    try:
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop_dir, exist_ok=True)
        shortcut_path = os.path.join(desktop_dir, "Active Learning Strategy Recommender.lnk")

        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            # Packaged .exe: the shortcut just launches the exe directly, and
            # already carries whatever icon was baked in at build time.
            target = sys.executable
            arguments = ""
            working_dir = os.path.dirname(sys.executable)
            icon_path = sys.executable
        else:
            # Running from source: launch via the same interpreter + desktop.py.
            target = sys.executable
            script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "desktop.py")
            arguments = f'"{script}"'
            working_dir = os.path.dirname(os.path.abspath(__file__))
            icon_candidate = os.path.join(_base_dir(), "icon.ico")
            icon_path = icon_candidate if os.path.exists(icon_candidate) else sys.executable

        ps_script = (
            '$WshShell = New-Object -ComObject WScript.Shell\n'
            f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")\n'
            f'$Shortcut.TargetPath = "{target}"\n'
            f"$Shortcut.Arguments = '{arguments}'\n"
            f'$Shortcut.WorkingDirectory = "{working_dir}"\n'
            f'$Shortcut.IconLocation = "{icon_path}"\n'
            '$Shortcut.Save()\n'
        )

        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            logger.error(f"Shortcut creation failed: {result.stderr}")
            return jsonify({
                "status": "error",
                "message": "Couldn't create the shortcut. Check the log file for details.",
            }), 500

        logger.info(f"Desktop shortcut created at {shortcut_path}")
        return jsonify({
            "status": "success",
            "message": "Desktop shortcut created.",
        })
    except Exception as e:
        logger.exception("Failed to create desktop shortcut")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
