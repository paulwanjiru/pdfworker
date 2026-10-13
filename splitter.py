"""
splitter.py — Document Studio Pro (Entry Point)
================================================
v5 — Blue / White / Black theme. Fully responsive. High-contrast dark mode.

Requirements:
  pip install pypdf PyQt5 pillow python-docx reportlab qrcode docx2pdf pywin32 PyMuPDF pdf2docx
  Optional:  pip install pytesseract pyhanko docxtpl
  External:  Tesseract OCR binary (OCR), Ghostscript (PDF/A)

Application package: app/
  app/icons.py        — IconFont, RotatingGear icon system
  app/styles.py       — Design tokens and stylesheets (light + dark)
  app/config.py       — AppSettings, JobHistory, helper finders
  app/helpers.py      — UI helpers (parse_page_ranges, section_label, etc.)
  app/widgets.py      — DropZone, RotatingGear custom widgets
  app/workers.py      — DocWorker, ThumbnailWorker background threads
  app/main_window.py  — DocumentStudioWindow (main application window)
"""

import sys
import signal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QColor, QPalette, QFontDatabase
from PyQt5.QtCore import Qt

from app.styles import (
    STYLE,
    BG_ROOT, BG_SURFACE_1, BG_INSET,
    TEXT_PRIMARY, TEXT_STRONG,
    ACCENT,
)
from app.main_window import DocumentStudioWindow


def main():
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except Exception:
        pass

    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,          QColor(BG_ROOT))
    pal.setColor(QPalette.WindowText,      QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Base,            QColor(BG_SURFACE_1))
    pal.setColor(QPalette.AlternateBase,   QColor(BG_INSET))
    pal.setColor(QPalette.Text,            QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Button,          QColor(BG_SURFACE_1))
    pal.setColor(QPalette.ButtonText,      QColor(TEXT_PRIMARY))
    pal.setColor(QPalette.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ToolTipBase,     QColor(TEXT_STRONG))
    pal.setColor(QPalette.ToolTipText,     QColor("#ffffff"))
    app.setPalette(pal)

    font = QFont("Segoe UI Variable Text", 10)
    try:
        if not QFontDatabase().families().count("Segoe UI Variable Text"):
            font = QFont("Segoe UI", 10)
    except Exception:
        font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setStyleSheet(STYLE)

    win = DocumentStudioWindow()
    win.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()