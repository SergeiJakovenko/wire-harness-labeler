# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for WireTester

from PyInstaller.utils.hooks import collect_data_files

# Собираем все данные библиотек barcode и qrcode:
#   - шрифты DejaVuSansMono.ttf (нужны для python-barcode)
#   - вспомогательные файлы qrcode
datas = [
    ('templates', 'templates'),
]
datas += collect_data_files('barcode')
datas += collect_data_files('qrcode')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'barcode',
        'barcode.writer',
        'barcode.codex',
        'qrcode',
        'qrcode.image.pil',
        'PIL',
        'PIL.Image',
        'PIL.ImageFont',
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WireTester',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)