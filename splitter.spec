# -*- mode: python ; coding: utf-8 -*-
# ============================================================
#  Document Studio Pro — PyInstaller Build Spec
#  Build command:  py -m PyInstaller splitter.spec
# ============================================================

import os
import sys
from pathlib import Path

block_cipher = None

# ── Resolve paths ─────────────────────────────────────────────────────────────
HERE = Path(SPECPATH)          # d:\software
ICON = str(HERE / "hierarchy.ico")

# ── Collect Qt platform + style plugins (needed for windowed PyQt5) ───────────
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# ── Hidden imports: all the modules PyInstaller misses by static analysis ─────
hidden = [
    # PyQt5
    "PyQt5.sip",
    "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets",
    "PyQt5.QtPrintSupport", "PyQt5.QtNetwork",
    # pypdf
    "pypdf", "pypdf.generic", "pypdf.filters",
    # PyMuPDF / fitz
    "fitz", "pymupdf",
    # pdf2docx
    "pdf2docx", "pdf2docx.converter",
    # Pillow
    "PIL", "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont",
    "PIL.PngImagePlugin", "PIL.JpegImagePlugin",
    "PIL.BmpImagePlugin", "PIL.TiffImagePlugin",
    "PIL.WebPImagePlugin", "PIL.GifImagePlugin",
    # reportlab
    "reportlab", "reportlab.pdfgen", "reportlab.pdfgen.canvas",
    "reportlab.lib", "reportlab.lib.pagesizes", "reportlab.lib.utils",
    "reportlab.lib.units", "reportlab.lib.colors",
    "reportlab.platypus", "reportlab.rl_config",
    "reportlab.graphics",
    # python-docx
    "docx", "docx.oxml", "docx.shared",
    # qrcode
    "qrcode", "qrcode.image.pil", "qrcode.image.base",
    "qrcode.image.svg",
    # pywin32 / win32com
    "win32com", "win32com.client", "win32com.shell",
    "pywintypes", "win32api", "win32con",
    # stdlib extras
    "xml.etree.ElementTree",
    "importlib.metadata",
    "pkg_resources",
    "setuptools",
]

# ── Data files: Qt plugins, reportlab fonts, etc. ────────────────────────────
datas = []

# Include reportlab fonts directory
try:
    import reportlab
    rl_dir = Path(reportlab.__file__).parent
    datas.append((str(rl_dir / "fonts"), "reportlab/fonts"))
    datas.append((str(rl_dir / "graphics"), "reportlab/graphics"))
except Exception:
    pass

# Include pdf2docx resources
try:
    import pdf2docx
    p2d_dir = Path(pdf2docx.__file__).parent
    datas.append((str(p2d_dir), "pdf2docx"))
except Exception:
    pass

# Include PyMuPDF/fitz resources
try:
    import pymupdf
    fitz_dir = Path(pymupdf.__file__).parent
    for pat in ["*.dll", "*.so", "*.dylib", "*.pyd"]:
        for f in fitz_dir.glob(pat):
            datas.append((str(f), "pymupdf"))
except Exception:
    try:
        import fitz
        fitz_dir = Path(fitz.__file__).parent
        for pat in ["*.dll", "*.so", "*.dylib", "*.pyd"]:
            for f in fitz_dir.glob(pat):
                datas.append((str(f), "fitz"))
    except Exception:
        pass

# ── Binary hook: pywin32 DLLs ─────────────────────────────────────────────────
binaries = []
try:
    import win32api
    import os as _os
    pywin_dir = Path(win32api.__file__).parent
    for dll in pywin_dir.glob("*.dll"):
        binaries.append((str(dll), "."))
except Exception:
    pass

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    [str(HERE / "splitter.py")],
    pathex=[str(HERE), str(HERE / "app")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden + [
        # app package submodules
        "app", "app.deps", "app.icons", "app.styles", "app.config",
        "app.helpers", "app.widgets", "app.workers", "app.main_window",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "pandas",
        "notebook", "IPython", "tk", "tkinter",
        "_tkinter", "test", "unittest",
        "cv2", "opencv",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ── Remove unneeded Qt modules and heavy unused DLLs ──────────────────────────
excluded_qt_mods = {
    "QtBluetooth", "QtDBus", "QtDesigner", "QtHelp",
    "QtLocation", "QtMultimedia", "QtMultimediaWidgets",
    "QtNfc", "QtOpenGL", "QtQml", "QtQuick", "QtQuickWidgets",
    "QtSensors", "QtSerialPort", "QtSql", "QtSvg",
    "QtTest", "QtWebChannel", "QtWebEngine",
    "QtWebEngineCore", "QtWebEngineWidgets",
    "QtWebSockets", "QtXml", "QtXmlPatterns",
}
# Exclude OpenCV / scipy / openblas DLLs — pulled in transitively via pdf2docx but unused at runtime
excluded_binaries = {
    "cv2", "opencv", "libopenblas", "libscipy",
    "ffmpeg", "videoio", "openblas",
}
a.binaries = [
    b for b in a.binaries
    if not any(mod in b[0] for mod in excluded_qt_mods)
    and not any(ex in b[0].lower() for ex in excluded_binaries)
]
# Also strip from datas
a.datas = [
    d for d in a.datas
    if not any(ex in d[0].lower() for ex in excluded_binaries)
]

# ── Package ───────────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ── EXE (one-directory mode — much faster startup than --onefile) ─────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,       # onedir mode
    name="DocumentStudioPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # skip UPX to avoid AV false positives
    console=False,               # windowed — no console flash
    icon=ICON,
    version_file=None,
)

# ── COLLECT (output folder) ───────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="DocumentStudioPro",    # → dist\DocumentStudioPro\
)
