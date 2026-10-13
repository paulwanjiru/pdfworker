"""
app.deps — Optional third-party dependency resolution for Document Studio Pro
=============================================================================
All optional imports are centralised here so every other module can simply do:
    from .deps import fitz, PdfReader, Image, ...
This avoids repeating the same try/except blocks in workers.py, main_window.py
and anywhere else that needs to guard against missing packages at runtime.
"""

# ── PyMuPDF / fitz ────────────────────────────────────────────────────────────
import sys
try:
    import pymupdf as fitz  # newer package name
    sys.modules.setdefault("fitz", fitz)
except ImportError:
    try:
        import fitz          # legacy name
    except ImportError:
        fitz = None

# ── pdf2docx ──────────────────────────────────────────────────────────────────
try:
    from pdf2docx import Converter as PDF2DocxConverter
except ImportError:
    PDF2DocxConverter = None

# ── OCR / pytesseract ─────────────────────────────────────────────────────────
try:
    import pytesseract
except ImportError:
    pytesseract = None

# ── docxtpl (Word template engine) ────────────────────────────────────────────
try:
    from docxtpl import DocxTemplate
except ImportError:
    DocxTemplate = None

# ── pyhanko (PDF signatures) ──────────────────────────────────────────────────
try:
    from pyhanko.pdf_utils.reader import PdfFileReader as PyHankoReader
    from pyhanko.sign.validation import validate_pdf_signature
    from pyhanko.sign import signers as pyhanko_signers
    from pyhanko.sign.signers.pdf_signer import PdfSigner, PdfSignatureMetadata
    from pyhanko_certvalidator import ValidationContext as PyHankoVC
    PYHANKO_OK = True
except ImportError:
    PyHankoReader = None
    validate_pdf_signature = None
    pyhanko_signers = None
    PdfSigner = None
    PdfSignatureMetadata = None
    PyHankoVC = None
    PYHANKO_OK = False

# ── pypdf ─────────────────────────────────────────────────────────────────────
try:
    import pypdf
    from pypdf import PdfReader, PdfWriter, Transformation
except ImportError:
    pypdf = None
    PdfReader = None
    PdfWriter = None
    Transformation = None

# ── Pillow ────────────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageOps
except ImportError:
    Image = None
    ImageOps = None

# ── python-docx ───────────────────────────────────────────────────────────────
try:
    from docx import Document
except ImportError:
    Document = None

# ── reportlab ─────────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.utils import ImageReader
except ImportError:
    letter = None
    canvas = None
    rl_colors = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    getSampleStyleSheet = None
    ImageReader = None

# ── qrcode ────────────────────────────────────────────────────────────────────
try:
    import qrcode
except ImportError:
    qrcode = None

# ── pywin32 / win32com ────────────────────────────────────────────────────────
try:
    import pythoncom
    import win32com.client
    win32com = win32com  # re-export
except ImportError:
    pythoncom = None
    win32com = None

__all__ = [
    # fitz
    "fitz",
    # pdf2docx
    "PDF2DocxConverter",
    # OCR
    "pytesseract",
    # docxtpl
    "DocxTemplate",
    # pyhanko
    "PyHankoReader", "validate_pdf_signature", "pyhanko_signers",
    "PdfSigner", "PdfSignatureMetadata", "PyHankoVC", "PYHANKO_OK",
    # pypdf
    "pypdf", "PdfReader", "PdfWriter", "Transformation",
    # Pillow
    "Image", "ImageOps",
    # python-docx
    "Document",
    # reportlab
    "letter", "canvas", "rl_colors", "SimpleDocTemplate",
    "Paragraph", "Spacer", "getSampleStyleSheet", "ImageReader",
    # qrcode
    "qrcode",
    # win32
    "pythoncom", "win32com",
]
