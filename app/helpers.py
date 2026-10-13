"""
app.helpers — Helper utilities for UI and document operations
"""
from PyQt5.QtWidgets import QLabel, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor

def parse_page_ranges(s, max_pages=99999):
    pages = set()
    for part in [p.strip() for p in s.split(",") if p.strip()]:
        if "-" in part:
            sub = part.split("-")
            if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                a, b = int(sub[0]), int(sub[1])
                if a <= b:
                    for p in range(a, b + 1):
                        if 1 <= p <= max_pages: pages.add(p)
        elif part.isdigit():
            p = int(part)
            if 1 <= p <= max_pages: pages.add(p)
    return sorted(pages)


def section_label(text):
    lbl = QLabel(text); lbl.setObjectName("sectionlabel"); return lbl


def hint_label(text):
    lbl = QLabel(text); lbl.setObjectName("hint"); lbl.setWordWrap(True); return lbl


def make_shadow(blur=18, dy=3, alpha=28):
    s = QGraphicsDropShadowEffect()
    s.setBlurRadius(blur); s.setOffset(0, dy); s.setColor(QColor(0, 0, 0, alpha))
    return s


def preserve_pdf_metadata_and_structure(reader, writer):
    try:
        if reader.metadata:
            clean = {k: str(v) for k, v in reader.metadata.items() if v is not None}
            if clean: writer.add_metadata(clean)
    except Exception: pass
    try:
        if hasattr(reader, "root_object") and hasattr(writer, "root_object"):
            if "/AcroForm" in reader.root_object and "/AcroForm" not in writer.root_object:
                writer.root_object["/AcroForm"] = reader.root_object["/AcroForm"]
    except Exception: pass

