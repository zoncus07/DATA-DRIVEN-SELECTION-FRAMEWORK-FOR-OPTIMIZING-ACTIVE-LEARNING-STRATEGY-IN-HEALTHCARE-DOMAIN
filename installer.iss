; Active Learning Strategy Recommender — Windows installer script
; Build with Inno Setup (https://jrsoftware.org/isinfo.php, free).
; Open this file in the Inno Setup Compiler and click Compile,
; or run from command line: iscc installer.iss
;
; Produces: Output\ActiveLearningRecommender-Setup.exe
; That single Setup.exe is what you hand to end users. It installs the
; app, creates Start Menu / Desktop shortcuts, registers an uninstaller
; in "Add or Remove Programs" — and needs nothing else on the target
; machine (no Python, no pip installs). Supports silent install for
; enterprise rollout via: ActiveLearningRecommender-Setup.exe /VERYSILENT

#define MyAppName "Active Learning Strategy Recommender"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Organization"
#define MyAppExeName "ActiveLearningRecommender.exe"

[Setup]
AppId={{B7C9E7C1-8E1E-4E2C-9C1C-ALSR00000001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; Skip the welcome page and the final "ready to install" confirmation
; page - straight from the wizard start into the (now smooth) install
; progress bar, fewer clicks for the same install.
DisableWelcomePage=yes
DisableReadyPage=yes
OutputDir=Output
OutputBaseFilename=ActiveLearningRecommender-Setup
; lzma2/fast trades a slightly larger Setup.exe for noticeably quicker
; decompression during install - worth it now that we're copying many
; files instead of one giant blob.
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
; Change to admin-only if you want a per-machine install instead of per-user:
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; dist\ActiveLearningRecommender\ is now a FOLDER (onedir build) containing
; the exe plus its supporting files - copy the whole thing, subfolders included.
Source: "dist\ActiveLearningRecommender\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; No [Tasks] checkbox for these anymore - for a non-technical audience we
; don't ask, we just always create a Desktop shortcut (and a Start Menu
; one) so there's never a chance of someone unchecking the one thing they
; need to find the app again.
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
; Checked by default and opens the app the moment install finishes, so
; the very first thing they see after clicking through is the app itself.
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName} now"; Flags: nowait postinstall skipifsilent
