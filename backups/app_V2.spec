# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, copy_metadata

# Submódulos que PyInstaller no detecta automáticamente
hidden_numpy = collect_submodules('numpy')
hidden_pandas = collect_submodules('pandas')
hidden_streamlit = collect_submodules('streamlit')
hidden_metadata = collect_submodules('importlib_metadata')
hidden_plotly = collect_submodules('plotly')

# Unificamos todos los hiddenimports
hidden_all = hidden_numpy + hidden_pandas + hidden_streamlit + hidden_metadata + hidden_plotly

# Copiar metadatos de paquetes y además tu base de datos
datas = copy_metadata('streamlit') + copy_metadata('plotly') + [
    ('ventas.db', '.'),  # ? tu base de datos se copia junto al .exe
    ('plotly/validators/*', 'plotly/validators'),
    ('plotly/package_data/*', 'plotly/package_data'),
    ('plotly/package_data/templates/*', 'plotly/package_data/templates'),
    ('streamlit/*', 'streamlit')
]

a = Analysis(
    ['app_V2.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_all,
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
    name='app_V2',
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
)
