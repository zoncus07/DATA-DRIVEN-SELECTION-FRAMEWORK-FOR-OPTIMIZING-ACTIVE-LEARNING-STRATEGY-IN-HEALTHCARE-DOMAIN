@echo off
REM Run this on a Windows machine, inside the desktop_app folder.
REM Requires Python 3.10-3.12 installed and on PATH.

echo === Creating virtual environment ===
python -m venv venv
call venv\Scripts\activate

echo === Installing dependencies ===
pip install --upgrade pip
pip install -r requirements.txt

echo === Building executable ===
pyinstaller build.spec --noconfirm

echo.
echo App folder built: dist\ActiveLearningRecommender\ (run ActiveLearningRecommender.exe inside it)

REM === Optional: build a proper installer with Inno Setup, if installed ===
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo === Building installer with Inno Setup ===
    %ISCC% installer.iss
    echo.
    echo Installer built: Output\ActiveLearningRecommender-Setup.exe
    echo This is the single file to hand out to end users.
) else (
    echo.
    echo [Optional] Inno Setup not found - skipping installer build.
    echo Install it free from https://jrsoftware.org/isdl.php, then re-run
    echo this script to also get a proper Setup.exe with shortcuts and
    echo an uninstaller. The raw .exe above already works fine on its own.
)

pause
