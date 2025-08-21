# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['BloodLogger/ui/main_window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('BloodLogger/assets', 'assets'),
        ('BloodLogger/db', 'db'),
        ('BloodLogger/ui/db/bloodlogger_template.db', 'ui/db'),
        ('BloodLogger/db/schema.sql', 'db'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main_window',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['BloodLogger/assets/Logo.ico'],
)
