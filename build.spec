# -*- mode: python ; coding: utf-8 -*-
# Build with:  pyinstaller build.spec
# Produces a FOLDER (dist/ActiveLearningRecommender/) containing
# ActiveLearningRecommender.exe plus its supporting files ("onedir" mode).
#
# Why onedir instead of onefile: a onefile exe zips everything (sklearn,
# scipy, pandas...) into one blob and has to re-extract it to a temp
# folder on every single launch - slow every time, and it makes the
# installer's progress bar sit at 0% then jump to 100% while copying
# that one big file. onedir ships many small files instead, so Inno
# Setup's progress bar moves smoothly and the app starts instantly on
# every launch after install (no re-extraction step).

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# sklearn and scipy ship a lot of compiled (.pyx/Cython) internals that
# PyInstaller's static import scanner can't see. Hand-picking hiddenimports
# is a whack-a-mole game (works from source, breaks in the frozen exe) —
# collecting every submodule is slower to build but reliable.
hidden = (
    collect_submodules('sklearn')
    + collect_submodules('scipy')
    + collect_submodules('pandas')
)

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
        ('icon.ico', '.'),
    ],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ActiveLearningRecommender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

# COLLECT gathers the exe + all its binaries/data into dist/ActiveLearningRecommender/
# as a folder of separate files, instead of packing them into the exe itself.
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ActiveLearningRecommender',
)
