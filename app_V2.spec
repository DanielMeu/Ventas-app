# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, copy_metadata, collect_data_files

# Submódulos que PyInstaller no detecta automáticamente
hidden_numpy = collect_submodules('numpy')
hidden_pandas = collect_submodules('pandas')
hidden_streamlit = collect_submodules('streamlit')
hidden_metadata = collect_submodules('importlib_metadata')
hidden_plotly = collect_submodules('plotly')
# hidden_matplotlib = collect_submodules('matplotlib')

# Unificamos todos los hiddenimports
hidden_all = hidden_numpy + hidden_pandas + hidden_streamlit + hidden_metadata + hidden_plotly 

# hiddenimports=['matplotlib', 'matplotlib.backends.backend_tkagg']

hiddenimports=[
    "pandas._libs.tslibs.timedeltas",
    "pandas._libs.tslibs.timestamps",
    "pandas._libs.tslibs.np_datetime",
    "plotly.matplotlylib",
    "streamlit.external.langchain"
]


# Archivos de datos de streamlit y plotly
datas = (
    copy_metadata('streamlit') +
    copy_metadata('plotly') +
    collect_data_files('plotly') +           # ? busca validators y package_data donde corresponde
    collect_data_files('streamlit') +        # ? incluye recursos estáticos de streamlit
    [
        ('ventas.db', '.'),                  # ? tu base de datos
    ]
)

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
