# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('common/images/logo.png', 'common/images'), ('common/images/logo_icon.ico', 'common/images'), ('common/images/seal.png', 'common/images')],
    hiddenimports=['agent.config', 'agent.signer', 'agent.version', 'pkcs11', 'pkcs11.attributes', 'pkcs11.constants', 'pkcs11.util', 'cryptography', 'flask', 'flask_cors', 'pystray', 'PIL', 'reportlab', 'PyPDF2', 'requests'],
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
    name='DigitalSignatureAgent',
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
    icon=['common\\images\\logo_icon.ico'],
)
