# Active Learning Strategy Recommender

A desktop app that looks at a dataset, checks it for common problems (class
imbalance, missing values, outliers, etc.), and recommends which active
learning strategy to use.

This guide is in two parts: **installing and using the app** (for anyone who
just wants to run it) and **building it** (for whoever is producing the
installer — needs a Windows machine and some developer tools).

---

## Installing the app

You'll be given one file: **`ActiveLearningRecommender-Setup.exe`**. That's
the entire installer — nothing else needs to be installed first.

1. **Get the file onto your Windows computer.** Save it wherever's convenient
   (Downloads is fine).
2. **Double-click `ActiveLearningRecommender-Setup.exe`.**
3. Windows may show a blue screen that says *"Windows protected your PC."*
   This is normal — it shows up for any new installer that hasn't been
   digitally signed yet, not just this one. Click **More info**, then click
   **Run anyway**.

   *(If your antivirus flags it too, that's the same reason — the program
   itself is safe, it's just unsigned.)*
4. Click through the installer: **Next → Next → Install → Finish**. On the
   step that asks about shortcuts, tick **"Create a desktop shortcut"** if
   you'd like one (you can always add it later — see below).
5. When it finishes, the app opens automatically. You can also find it later
   under **Start Menu → Active Learning Strategy Recommender**, or on your
   Desktop if you ticked that box.

That's it — no Python, no extra downloads, nothing else to set up.

### Using the app

1. Drag a dataset file (`.csv`, `.xlsx`, or `.parquet`) onto the upload box,
   or click it to browse for one.
2. Pick the **target column** — the column you're trying to predict — from
   the dropdown.
3. Click **Run Analysis & Strategy Recommendation**.
4. The right-hand side fills in with what was found (a checklist of 5 common
   dataset problems) and which strategy is recommended.

Everything runs on your own computer — the dataset never leaves your machine.

### Adding a desktop shortcut later

Didn't tick the shortcut box during install, or deleted it by accident? Open
the app and click the **"Desktop Shortcut"** button near the top right. It
adds one immediately — no need to reinstall.

### If something looks broken

- **The window opens but the layout looks broken, cramped, or like an old
  version of Internet Explorer:** your computer is missing the free
  **Microsoft Edge WebView2 Runtime**. Most Windows 10/11 machines already
  have it, but some work/managed computers don't. Install it from
  <https://developer.microsoft.com/en-us/microsoft-edge/webview2/> (look for
  "Evergreen Bootstrapper") and reopen the app. If it's genuinely missing,
  the app will actually pop up a message telling you this itself.
- **"Run Analysis" shows an error message:** that's expected behavior for a
  bad file or an unsupported column — read the message, it explains what to
  fix. If it looks like a garbled technical error instead, see
  *Reporting a problem* below.

### Uninstalling

Use **Settings → Apps → Active Learning Strategy Recommender → Uninstall**
(or the entry in **Add or Remove Programs**), same as any other Windows app.

### Reporting a problem

If something crashes or behaves strangely, the app keeps a log file at:

```
%TEMP%\alsr_app.log
```

(Type that path into the Windows Explorer address bar, or paste it into Run
— <kbd>Win</kbd>+<kbd>R</kbd>.) Send that file along when reporting the issue.

---

## Building it (for whoever produces the installer)

Everything below is for turning the source code in this folder into the
`ActiveLearningRecommender-Setup.exe` that end users install. This step
**must be done on a Windows machine** — PyInstaller builds for whatever OS
it's run on, it can't cross-compile a Windows `.exe` from Linux/macOS (a
Windows VM works fine if that's all you have).

### One-time setup

1. Install **Python 3.10–3.12** (make sure it's on PATH).
2. Install **[Inno Setup](https://jrsoftware.org/isdl.php)** — free, used to
   build the installer wrapper. Optional: skip this if you only want the
   plain `.exe` with no installer.

### Build steps

1. Copy this whole `desktop_app` folder onto the Windows machine.
2. Double-click **`build_exe.bat`** (or run it from a terminal). It creates a
   virtual environment, installs dependencies, and runs PyInstaller using
   `build.spec`, which bundles `templates/`, `static/` (fonts included), the
   app icon, and the sklearn/scipy imports the checks rely on.
3. Your standalone executable appears at `dist\ActiveLearningRecommender.exe`.
   This alone is enough to hand out — no installer required — but it won't
   have Start Menu/Desktop shortcuts or an uninstaller.
4. If Inno Setup is installed, `build_exe.bat` also produces
   `Output\ActiveLearningRecommender-Setup.exe` automatically (or open
   `installer.iss` in the Inno Setup Compiler and click Compile). **This is
   the file to hand out** — it's what the "Installing the app" section above
   walks through.

For silent/mass rollout (e.g. via SCCM/Intune), the installer supports the
standard Inno Setup silent flags:
```
ActiveLearningRecommender-Setup.exe /VERYSILENT /SUPPRESSMSGBOXES
```

### Running it locally without building anything

Useful while developing — no PyInstaller step needed:

```bash
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python desktop.py
```

This opens the native window pointed at the app. To check the UI in a
regular browser instead, run `python app.py` and visit
`http://127.0.0.1:5000`.

### Build notes / troubleshooting

- `pywebview` uses the Edge WebView2 runtime on Windows (ships with Windows
  10/11; missing on some older or locked-down machines — see the WebView2
  note in the end-user section above).
- First run of the built `.exe` takes a few seconds to unpack (onefile mode
  extracts to a temp folder each launch). Trade a single `.exe` for instant
  startup by switching `build.spec` to `--onedir` mode instead, if you'd
  rather have a folder of files — ask if you want this pre-configured.
- Antivirus/SmartScreen flagging the unsigned `.exe` on first run is normal
  for unsigned freeware; code-signing is a separate (paid) step if you want
  to remove that warning for end users.
- If `/api/analyze` ever returns a garbled error like `Unexpected token
  '<'...`, that means the server hit an unhandled crash and returned an HTML
  error page instead of JSON — check `%TEMP%\alsr_app.log` for the full
  Python traceback.

### File map

```
desktop_app/
├── app.py                 # Flask app + API (upload/analyze/shortcut endpoints)
├── desktop.py             # pywebview native window launcher (exe entry point)
├── analyzer.py             \
├── recommender.py           } your original logic, unmodified
├── data_loader.py            /
├── check_*.py                /
├── templates/index.html   # UI shell
├── static/css/style.css   # design tokens + styles
├── static/js/app.js       # upload / analyze / render logic
├── static/fonts/          # self-hosted Space Grotesk, Inter, IBM Plex Mono
├── icon.ico                # app icon, used by build.spec + installer.iss
├── requirements.txt
├── build.spec              # PyInstaller config
├── installer.iss           # Inno Setup installer script
└── build_exe.bat           # one-click Windows build script
```

### What changed in this pass

- **UI restyle** — "Dataset Diagnostics" instrument-panel look (sage/forest
  palette, subtle technical grid background, status pills). The 5-check
  diagnostic matrix (HD / IMB / MISS / OUT / RED) now renders live from
  whatever `analyzer.py` actually returns for the loaded dataset (PASS /
  FLAGGED / ERROR per check, with the real metric — imbalance ratio,
  redundant-pair count, duplicate-row count, etc.) instead of placeholder
  values. The upload/analyze request contract against `app.py` is unchanged.
- **App icon** — `icon.ico`, a bold bar-chart mark that stays legible down to
  16×16, wired into `build.spec` and `installer.iss` so the `.exe`, its
  window/taskbar icon, and the installer all use it.
- **Desktop shortcut, two ways** — the installer's own opt-in checkbox
  (unchanged), plus a new **"Desktop Shortcut" button in the app itself**,
  wired to a `POST /api/create-shortcut` endpoint, which adds a `.lnk` to the
  Desktop on request at any time without reinstalling (via `WScript.Shell`
  through PowerShell — no new dependency, Windows-only).
- **Bug fix** — `/api/analyze` was crashing with `TypeError: Object of type
  int64 is not JSON serializable` on any dataset that actually tripped the
  imbalance/missing-values checks, because those checks return numpy scalar
  types. Added `_to_jsonable()` in `app.py` to recursively convert
  numpy/pandas types before `jsonify`. Pre-existing bug, not introduced by
  the restyle, but it blocked verifying the new diagnostic matrix, so it's
  fixed here too.
- **Typography** — Space Grotesk (headings), Inter (body), IBM Plex Mono
  (data/scores), self-hosted in `static/fonts/` so the `.exe` has no internet
  dependency at runtime.
