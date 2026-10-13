"""
app.main_window — Main application window (DocumentStudioWindow)
"""
import sys, os, shutil, subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTabWidget,
    QSpinBox, QProgressBar, QTextEdit, QFrame, QSizePolicy,
    QScrollArea, QStackedWidget, QListWidget, QListWidgetItem,
    QComboBox, QCheckBox, QSlider, QAbstractItemView, QListView
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QImage, QTransform

from .deps import fitz, PdfReader, PYHANKO_OK

from .icons import IconFont
from .styles import STYLE, build_dark_stylesheet, ACCENT, TEXT_MUTED
from .config import AppSettings, JobHistory, find_tesseract, find_ghostscript
from .helpers import section_label, hint_label, make_shadow, parse_page_ranges
from .widgets import RotatingGear, DropZone
from .workers import DocWorker, ThumbnailWorker

class DocumentStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Studio Pro")
        self.setMinimumSize(900, 650)
        self.resize(1180, 820)

        self._active_worker: Optional[DocWorker] = None
        self._thumb_worker: Optional[ThumbnailWorker] = None
        self._last_out_dir = ""
        IconFont.family()

        self._settings = AppSettings()
        self._history = JobHistory()
        self._history_enabled = self._settings.get("history_enabled", True)
        self._dark_mode = bool(self._settings.get("dark_mode", False))
        self._visual_pages = []
        self._bates_files: List[str] = []
        self._conv_files: List[str] = []

        self._build_ui()
        self._apply_theme()
        self._history_reload()
        self._select_nav(0)

    def _build_ui(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        ml = QHBoxLayout(root); ml.setContentsMargins(0, 0, 0, 0); ml.setSpacing(0)
        ml.addWidget(self._create_sidebar())

        rw = QWidget(); rl = QVBoxLayout(rw)
        rl.setContentsMargins(20, 16, 20, 16); rl.setSpacing(10)

        rl.addWidget(self._create_header())

        self._deck = QStackedWidget()
        self._deck.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Panels (index → builder)
        self._deck.addWidget(self._build_split_panel())              # 0
        self._deck.addWidget(self._build_merge_panel())              # 1
        self._deck.addWidget(self._build_convert_panel())            # 2
        self._deck.addWidget(self._build_security_panel())           # 3
        self._deck.addWidget(self._build_watermark_panel())          # 4
        self._deck.addWidget(self._build_organize_panel())           # 5
        self._deck.addWidget(self._build_tools_panel())              # 6
        self._deck.addWidget(self._build_style_panel())              # 7
        self._deck.addWidget(self._build_source_panel())             # 8
        self._deck.addWidget(self._build_optimize_panel())           # 9
        self._deck.addWidget(self._build_batch_panel())              # 10
        self._deck.addWidget(self._build_history_panel())            # 11
        self._deck.addWidget(self._build_page_organizer_panel())     # 12
        self._deck.addWidget(self._build_nup_panel())                # 13
        self._deck.addWidget(self._build_bates_panel())              # 14
        self._deck.addWidget(self._build_compare_panel())            # 15
        self._deck.addWidget(self._build_ocr_panel())                # 16
        self._deck.addWidget(self._build_mail_merge_panel())         # 17
        self._deck.addWidget(self._build_signature_panel())          # 18
        self._deck.addWidget(self._build_pdfa_panel())               # 19

        rl.addWidget(self._deck, 1)
        rl.addWidget(self._create_action_bar())
        rl.addWidget(self._create_log_panel())
        ml.addWidget(rw, 1)

    def _create_sidebar(self):
        outer = QFrame(); outer.setObjectName("sidebar"); outer.setFixedWidth(232)
        ov = QVBoxLayout(outer); ov.setContentsMargins(0, 0, 0, 0); ov.setSpacing(0)

        scroll = QScrollArea(); scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        v = QVBoxLayout(content)
        v.setContentsMargins(12, 16, 12, 14); v.setSpacing(3)

        # Brand
        br = QHBoxLayout(); br.setSpacing(9)
        logo_pm = IconFont.pixmap("star", ACCENT, 30, ratio=0.72)
        logo = QLabel(); logo.setPixmap(logo_pm); logo.setFixedSize(26, 26)
        logo.setStyleSheet("background: transparent;")
        bc = QVBoxLayout(); bc.setSpacing(0)
        bn = QLabel("DocuStudio"); bn.setObjectName("brand")
        bs = QLabel("ALL-IN-ONE SUITE"); bs.setObjectName("brand_sub")
        bc.addWidget(bn); bc.addWidget(bs)
        br.addWidget(logo); br.addLayout(bc); br.addStretch()
        v.addLayout(br); v.addSpacing(12)

        nav_groups = [
            ("DOCUMENTS", [
                ("split", "Split PDF", 0), ("merge", "Merge PDF", 1),
                ("convert", "Convert Documents", 2),
            ]),
            ("PROTECTION", [
                ("security", "PDF Security", 3),
                ("watermark", "Watermark & Numbers", 4),
                ("organize", "Organize & Rotate", 5),
                ("signature", "Digital Signatures", 18),
                ("shield_check", "PDF/A Archive", 19),
            ]),
            ("EDIT & LAYOUT", [
                ("page_view", "Visual Organizer", 12),
                ("nup", "N-up / Booklet", 13),
                ("bates", "Bates Numbering", 14),
            ]),
            ("OPTIMIZE", [
                ("compress", "Optimize / Compress", 9),
                ("batch", "Batch Processing", 10),
            ]),
            ("AUTOMATION", [
                ("ocr", "OCR / Searchable PDF", 16),
                ("mail", "Mail Merge", 17),
            ]),
            ("INSPECTION", [
                ("tools", "Metadata & QR", 6),
                ("style", "Style Inspector", 7),
                ("source", "Source / Markup", 8),
                ("compare", "PDF Comparison", 15),
                ("history", "Job History", 11),
            ]),
        ]

        self._nav_buttons = []
        for gtitle, items in nav_groups:
            gl = QLabel(gtitle); gl.setObjectName("nav_group"); v.addWidget(gl)
            for icon_name, text, idx in items:
                btn = QPushButton(f"  {text}"); btn.setObjectName("nav_btn")
                btn.setCursor(Qt.PointingHandCursor); btn.setIconSize(QSize(16, 16))
                btn.setIcon(IconFont.icon(icon_name, ACCENT, 32))
                btn.setProperty("icon_name", icon_name)
                btn.clicked.connect(lambda _, i=idx: self._select_nav(i))
                self._nav_buttons.append(btn); v.addWidget(btn)

        v.addStretch()

        # ── Developer credit with rotating gold gear ──
        footer = QFrame()
        footer.setStyleSheet("background: transparent; border: none;")
        fh = QHBoxLayout(footer)
        fh.setContentsMargins(4, 8, 4, 4)
        fh.setSpacing(9)

        # Rotating gear — gold, tilted toward content
        self._dev_gear = RotatingGear(size=22, color="#f59e0b",
                                       interval_ms=50, step_deg=2)
        fh.addWidget(self._dev_gear, 0, Qt.AlignVCenter)

        # Stacked text: link + tagline
        fv = QVBoxLayout()
        fv.setSpacing(0)
        fv.setContentsMargins(0, 0, 0, 0)

        dev_lbl = QLabel(
            '<a href="https://www.infrabitsystems.co.ke" '
            'style="color:#475569; text-decoration:none; '
            'font-size:10px; font-weight:700; letter-spacing:0.2px;">'
            'Developed by Infrabit Systems</a>'
        )
        dev_lbl.setOpenExternalLinks(True)
        dev_lbl.setCursor(Qt.PointingHandCursor)
        dev_lbl.setToolTip("www.infrabitsystems.co.ke")
        fv.addWidget(dev_lbl)

       

        fh.addLayout(fv, 1)
        v.addWidget(footer)

        scroll.setWidget(content)
        ov.addWidget(scroll)
        return outer

    def _select_nav(self, index):
        self._deck.setCurrentIndex(index)
        base_color = "#cbd5e1" if self._dark_mode else ACCENT
        for i, btn in enumerate(self._nav_buttons):
            active = (i == index)
            btn.setProperty("active", "true" if active else "false")
            icon_name = btn.property("icon_name") or "document"
            btn.setIcon(IconFont.icon(icon_name, "#ffffff" if active else base_color, 32))
            btn.style().unpolish(btn); btn.style().polish(btn)
        titles = {
            0:"Split PDF",1:"Merge PDF Documents",2:"Convert Document",
            3:"Apply PDF Security",4:"Apply Watermark / Numbers",5:"Process Pages",
            6:"Apply Metadata / Generate QR",7:"Inspect Styles",8:"View Source / Markup",
            9:"Optimize PDF",10:"Run Batch Operation",11:"Job History",
            12:"Save Reorganized PDF",13:"Create N-up / Booklet",14:"Apply Bates Numbering",
            15:"Compare PDFs",16:"Run OCR",17:"Generate Mail Merge",
            18:"Sign or Verify PDF",19:"Convert to PDF/A",
        }
        self._exec_btn.setText(f"   {titles.get(index, 'Execute Action')}")
        self._exec_btn.setIcon(IconFont.icon("play", "#ffffff", 32))
        self._exec_btn.setEnabled(index != 11)

    def _create_header(self):
        w = QWidget(); w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(10)
        vb = QVBoxLayout(); vb.setSpacing(1)
        t = QLabel("Document Studio Pro"); t.setObjectName("title")
        st = QLabel("Convert · Protect · Organize · Automate"); st.setObjectName("subtitle")
        vb.addWidget(t); vb.addWidget(st)
        h.addLayout(vb); h.addStretch()
        self._theme_btn = QPushButton(); self._theme_btn.setObjectName("tool_small")
        self._theme_btn.setFixedSize(34, 34); self._theme_btn.setCursor(Qt.PointingHandCursor)
        self._theme_btn.setToolTip("Toggle dark mode"); self._theme_btn.setIconSize(QSize(16, 16))
        self._theme_btn.clicked.connect(self._toggle_dark_mode)
        h.addWidget(self._theme_btn)
        badge = QLabel("Infrabit Edition"); badge.setObjectName("badge")
        h.addWidget(badge, alignment=Qt.AlignTop)
        return w

    # ── Panel helpers ────────────────────────────────────────
    def _make_scroll(self):
        sc = QScrollArea(); sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sc.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        sc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return sc

    def _make_card(self):
        c = QFrame(); c.setObjectName("card"); c.setGraphicsEffect(make_shadow())
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        return c

    # ── Split ────────────────────────────────────────────────
    def _build_split_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)

        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("INPUT PDF DOCUMENT"))
        self._split_dz = DropZone("Drop a PDF file here or click to browse",
                                   accept_filter="PDF Files (*.pdf)", icon_name="pdf")
        self._split_dz.files_dropped.connect(self._on_split_file_selected)
        cv.addWidget(self._split_dz)
        row = QHBoxLayout()
        self._split_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._split_file_lbl.setWordWrap(True)
        self._split_badge = QLabel("", objectName="badge"); self._split_badge.hide()
        row.addWidget(self._split_file_lbl, 1); row.addWidget(self._split_badge)
        cv.addLayout(row); v.addWidget(c)

        mc = self._make_card(); mv = QVBoxLayout(mc)
        mv.setContentsMargins(16, 14, 16, 14); mv.setSpacing(8)
        mv.addWidget(section_label("SPLIT CONFIGURATION"))
        self._split_tabs = QTabWidget()
        t = QWidget(); QVBoxLayout(t).addWidget(QLabel("Every page becomes its own single-page PDF."))
        self._split_tabs.addTab(t, "All Pages")
        t = QWidget(); tl = QHBoxLayout(t); tl.addWidget(QLabel("Extract page:"))
        self._split_spin_single = QSpinBox(); self._split_spin_single.setRange(1, 99999)
        tl.addWidget(self._split_spin_single); tl.addStretch()
        self._split_tabs.addTab(t, "Single Page")
        t = QWidget(); tl = QHBoxLayout(t); tl.addWidget(QLabel("From:"))
        self._split_spin_from = QSpinBox(); self._split_spin_from.setRange(1, 99999); tl.addWidget(self._split_spin_from)
        tl.addWidget(QLabel("to:"))
        self._split_spin_to = QSpinBox(); self._split_spin_to.setRange(1, 99999); self._split_spin_to.setValue(5)
        tl.addWidget(self._split_spin_to); tl.addStretch()
        self._split_tabs.addTab(t, "Page Range")
        t = QWidget(); tl = QVBoxLayout(t)
        tl.addWidget(QLabel("Comma-separated pages/ranges (e.g. 1, 3-5, 8):"))
        self._split_custom_edit = QLineEdit(); self._split_custom_edit.setPlaceholderText("1, 3-5, 8")
        tl.addWidget(self._split_custom_edit)
        self._split_tabs.addTab(t, "Custom")
        t = QWidget(); tl = QHBoxLayout(t); tl.addWidget(QLabel("Pages per chunk:"))
        self._split_spin_chunk = QSpinBox(); self._split_spin_chunk.setRange(1, 9999); self._split_spin_chunk.setValue(5)
        tl.addWidget(self._split_spin_chunk); tl.addStretch()
        self._split_tabs.addTab(t, "Chunks")
        t = QWidget(); tl = QHBoxLayout(t); tl.addWidget(QLabel("Target max size per part (MB):"))
        self._split_size_mb = QSpinBox(); self._split_size_mb.setRange(1, 5000); self._split_size_mb.setValue(10)
        tl.addWidget(self._split_size_mb); tl.addStretch()
        self._split_tabs.addTab(t, "By Size")
        mv.addWidget(self._split_tabs); v.addWidget(mc)

        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("DESTINATION FOLDER"))
        orow = QHBoxLayout()
        self._split_out_edit = QLineEdit(); self._split_out_edit.setPlaceholderText("Auto-generated folder...")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_dir(self._split_out_edit))
        orow.addWidget(self._split_out_edit, 1); orow.addWidget(b)
        ov.addLayout(orow); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_split_file_selected(self, paths):
        if not paths: return
        p = paths[0]; self._split_file_lbl.setText(p)
        try:
            n = len(PdfReader(p).pages)
            self._split_badge.setText(f"{n} pages"); self._split_badge.show()
            for s in (self._split_spin_single, self._split_spin_from, self._split_spin_to):
                s.setMaximum(n)
            self._split_spin_to.setValue(min(n, 5))
        except Exception: self._split_badge.hide()
        if not self._split_out_edit.text().strip():
            self._split_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_split"))
        self._log_msg(f"Loaded for Split: {Path(p).name}")

    # ── Merge ────────────────────────────────────────────────
    def _build_merge_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("DOCUMENTS TO MERGE (IN ORDER)"))
        self._merge_dz = DropZone("Drop multiple PDF files here or click to add",
                                   accept_filter="PDF Files (*.pdf)", multi=True, icon_name="merge")
        self._merge_dz.files_dropped.connect(self._on_merge_files_dropped)
        cv.addWidget(self._merge_dz)
        self._merge_list = QListWidget(); self._merge_list.setMinimumHeight(120)
        self._merge_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cv.addWidget(self._merge_list, 1)
        tbar = QHBoxLayout(); tbar.setSpacing(5)
        def tb(ic, txt, slot):
            b = QPushButton(txt); b.setObjectName("tool_small")
            b.setIcon(IconFont.icon(ic, "#334155", 24)); b.setIconSize(QSize(12, 12))
            b.clicked.connect(slot); return b
        for ic, txt, slot in [("add", "Add", self._on_merge_browse_add),
                               ("up", "Up", self._merge_move_up),
                               ("down", "Down", self._merge_move_down),
                               ("remove", "Remove", self._merge_remove_selected),
                               ("reverse", "Reverse", self._merge_reverse),
                               ("clear", "Clear", self._merge_list.clear)]:
            tbar.addWidget(tb(ic, txt, slot))
        tbar.addStretch(); cv.addLayout(tbar); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("MERGED OUTPUT PDF"))
        orow = QHBoxLayout()
        self._merge_out_edit = QLineEdit(); self._merge_out_edit.setPlaceholderText("merged_document.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._merge_out_edit, "PDF Files (*.pdf)"))
        orow.addWidget(self._merge_out_edit, 1); orow.addWidget(b)
        ov.addLayout(orow); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_merge_files_dropped(self, paths):
        for p in paths:
            if p.lower().endswith(".pdf"):
                try: t = f"{Path(p).name}  ({len(PdfReader(p).pages)} pages)"
                except Exception: t = Path(p).name
                item = QListWidgetItem(t); item.setData(Qt.UserRole, p)
                item.setIcon(IconFont.icon("pdf", ACCENT, 28))
                item.setToolTip(p); self._merge_list.addItem(item)
        if not self._merge_out_edit.text() and self._merge_list.count() > 0:
            first = self._merge_list.item(0).data(Qt.UserRole)
            self._merge_out_edit.setText(str(Path(first).parent / "merged_collection.pdf"))

    def _on_merge_browse_add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select PDF Files", "", "PDF Files (*.pdf)")
        if paths: self._on_merge_files_dropped(paths)
    def _merge_move_up(self):
        r = self._merge_list.currentRow()
        if r > 0:
            it = self._merge_list.takeItem(r); self._merge_list.insertItem(r-1, it)
            self._merge_list.setCurrentRow(r-1)
    def _merge_move_down(self):
        r = self._merge_list.currentRow()
        if 0 <= r < self._merge_list.count() - 1:
            it = self._merge_list.takeItem(r); self._merge_list.insertItem(r+1, it)
            self._merge_list.setCurrentRow(r+1)
    def _merge_remove_selected(self):
        r = self._merge_list.currentRow()
        if r >= 0: self._merge_list.takeItem(r)
    def _merge_reverse(self):
        items = []
        while self._merge_list.count() > 0: items.append(self._merge_list.takeItem(0))
        for it in reversed(items): self._merge_list.addItem(it)

    # ── Convert ──────────────────────────────────────────────
    def _build_convert_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT OR DROP INPUT DOCUMENT / IMAGES"))
        self._conv_dz = DropZone(
            "Drop document (.docx, .xlsx, .pdf, .txt, .md) or images",
            accept_filter="Supported (*.docx *.doc *.xlsx *.xls *.pdf *.png *.jpg *.jpeg *.webp *.bmp *.tiff *.txt *.md);;All Files (*.*)",
            multi=True, icon_name="convert")
        self._conv_dz.files_dropped.connect(self._on_conv_files_dropped)
        cv.addWidget(self._conv_dz)
        self._conv_input_lbl = QLabel("No document selected", objectName="filelabel")
        self._conv_input_lbl.setWordWrap(True)
        cv.addWidget(self._conv_input_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("CONVERSION TARGET"))
        self._conv_type_combo = QComboBox()
        self._conv_type_combo.addItems([
            "Word to PDF  (.docx ➔ .pdf)","Excel to PDF  (.xlsx ➔ .pdf)",
            "Images to PDF  (.png/.jpg ➔ .pdf)","PDF to Images  (extract)",
            "PDF to Word  (.pdf ➔ .docx)","PDF to Text  (.pdf ➔ .txt)",
            "Text / Markdown to PDF"])
        self._conv_type_combo.currentIndexChanged.connect(self._update_conv_out_hint)
        ov.addWidget(self._conv_type_combo)
        ov.addWidget(section_label("OUTPUT DESTINATION"))
        dr = QHBoxLayout()
        self._conv_out_edit = QLineEdit(); self._conv_out_edit.setPlaceholderText("Output file or folder...")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(self._browse_conv_out)
        dr.addWidget(self._conv_out_edit, 1); dr.addWidget(b)
        ov.addLayout(dr); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_conv_files_dropped(self, paths):
        self._conv_files = paths
        if not paths: return
        first = paths[0]; ext = Path(first).suffix.lower()
        self._conv_input_lbl.setText(
            f"{len(paths)} files selected — first: {Path(first).name}"
            if len(paths) > 1 else first)
        if ext in (".docx",".doc"): self._conv_type_combo.setCurrentIndex(0)
        elif ext in (".xlsx",".xls"): self._conv_type_combo.setCurrentIndex(1)
        elif ext in (".png",".jpg",".jpeg",".webp",".bmp",".tiff"): self._conv_type_combo.setCurrentIndex(2)
        elif ext == ".pdf": self._conv_type_combo.setCurrentIndex(4)
        elif ext in (".txt",".md",".log"): self._conv_type_combo.setCurrentIndex(6)
        self._update_conv_out_hint()

    def _update_conv_out_hint(self):
        if not self._conv_files: return
        first = Path(self._conv_files[0]); idx = self._conv_type_combo.currentIndex()
        if idx in (0,1,2,6): self._conv_out_edit.setText(str(first.parent / f"{first.stem}.pdf"))
        elif idx == 3: self._conv_out_edit.setText(str(first.parent / f"{first.stem}_images"))
        elif idx == 4: self._conv_out_edit.setText(str(first.parent / f"{first.stem}.docx"))
        elif idx == 5: self._conv_out_edit.setText(str(first.parent / f"{first.stem}.txt"))

    def _browse_conv_out(self):
        idx = self._conv_type_combo.currentIndex()
        if idx == 3:
            d = QFileDialog.getExistingDirectory(self, "Select Output Folder", self._conv_out_edit.text() or "")
            if d: self._conv_out_edit.setText(d)
        else:
            f = "PDF (*.pdf)" if idx in (0,1,2,6) else ("Word (*.docx)" if idx == 4 else "Text (*.txt)")
            self._browse_save_file(self._conv_out_edit, f)

    # ── Security (Protect / Unlock / Redact) ─────────────────
    def _build_security_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF DOCUMENT"))
        self._sec_dz = DropZone("Drop a PDF to protect, unlock, or redact",
                                 accept_filter="PDF Files (*.pdf)", icon_name="security")
        self._sec_dz.files_dropped.connect(self._on_sec_file_dropped)
        cv.addWidget(self._sec_dz)
        self._sec_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._sec_file_lbl.setWordWrap(True)
        cv.addWidget(self._sec_file_lbl); v.addWidget(c)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        tv.addWidget(section_label("SECURITY ACTION"))
        self._sec_tabs = QTabWidget()
        # Protect
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("User password:"))
        self._sec_user_pw = QLineEdit(); self._sec_user_pw.setEchoMode(QLineEdit.Password)
        r.addWidget(self._sec_user_pw); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Owner password:"))
        self._sec_owner_pw = QLineEdit(); self._sec_owner_pw.setEchoMode(QLineEdit.Password)
        r.addWidget(self._sec_owner_pw); tl.addLayout(r)
        self._sec_chk_print = QCheckBox("Allow printing"); self._sec_chk_print.setChecked(True)
        self._sec_chk_copy = QCheckBox("Allow copying"); self._sec_chk_copy.setChecked(True)
        tl.addWidget(self._sec_chk_print); tl.addWidget(self._sec_chk_copy); tl.addStretch()
        self._sec_tabs.addTab(t, "Protect")
        # Unlock
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(QLabel("Remove password and save an unrestricted copy."))
        r = QHBoxLayout(); r.addWidget(QLabel("Password:"))
        self._sec_unlock_pw = QLineEdit(); self._sec_unlock_pw.setEchoMode(QLineEdit.Password)
        r.addWidget(self._sec_unlock_pw); tl.addLayout(r); tl.addStretch()
        self._sec_tabs.addTab(t, "Unlock")
        # Redact
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(hint_label("Permanently removes text & image pixels under each match."))
        r = QHBoxLayout(); r.addWidget(QLabel("Terms:"))
        self._redact_terms_edit = QLineEdit()
        self._redact_terms_edit.setPlaceholderText("comma-separated, e.g. John Doe, 555-1234")
        r.addWidget(self._redact_terms_edit, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Pages:"))
        self._redact_pages_edit = QLineEdit(); self._redact_pages_edit.setPlaceholderText("blank = all")
        r.addWidget(self._redact_pages_edit, 1)
        r.addWidget(QLabel("Fill:"))
        self._redact_fill_combo = QComboBox()
        self._redact_fill_combo.addItem("Black", "black"); self._redact_fill_combo.addItem("White", "white")
        r.addWidget(self._redact_fill_combo); tl.addLayout(r)
        self._redact_chk_case = QCheckBox("Case sensitive"); tl.addWidget(self._redact_chk_case)
        tl.addStretch(); self._sec_tabs.addTab(t, "Redact")
        tv.addWidget(self._sec_tabs); v.addWidget(tc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT PDF FILE"))
        orow = QHBoxLayout()
        self._sec_out_edit = QLineEdit(); self._sec_out_edit.setPlaceholderText("Destination...")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._sec_out_edit, "PDF Files (*.pdf)"))
        orow.addWidget(self._sec_out_edit, 1); orow.addWidget(b)
        ov.addLayout(orow); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_sec_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._sec_file_lbl.setText(p); stem = Path(p).stem
        i = self._sec_tabs.currentIndex()
        if i == 0: self._sec_out_edit.setText(str(Path(p).parent / f"{stem}_protected.pdf"))
        elif i == 1: self._sec_out_edit.setText(str(Path(p).parent / f"{stem}_unlocked.pdf"))
        else: self._sec_out_edit.setText(str(Path(p).parent / f"{stem}_redacted.pdf"))

    # ── Watermark / Numbers / Header-Footer ──────────────────
    def _build_watermark_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF DOCUMENT"))
        self._wm_dz = DropZone("Drop a PDF to stamp or watermark",
                                accept_filter="PDF Files (*.pdf)", icon_name="watermark")
        self._wm_dz.files_dropped.connect(self._on_wm_file_dropped)
        cv.addWidget(self._wm_dz)
        self._wm_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._wm_file_lbl.setWordWrap(True)
        cv.addWidget(self._wm_file_lbl); v.addWidget(c)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        self._stamp_tabs = QTabWidget()
        # Text Watermark
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("Watermark Text:"))
        self._wm_text_edit = QLineEdit("CONFIDENTIAL"); r.addWidget(self._wm_text_edit)
        wc = QComboBox(); wc.addItems(["CONFIDENTIAL","DRAFT","DO NOT COPY","SAMPLE","ORIGINAL","CUSTOM"])
        wc.currentTextChanged.connect(lambda tx: self._wm_text_edit.setText(tx) if tx != "CUSTOM" else None)
        r.addWidget(wc); tl.addLayout(r)
        ga = QHBoxLayout(); ga.setSpacing(12)
        c1 = QVBoxLayout(); self._wm_angle_lbl = QLabel("Rotation: 45°")
        self._wm_angle_slider = QSlider(Qt.Horizontal)
        self._wm_angle_slider.setRange(-90, 90); self._wm_angle_slider.setValue(45)
        self._wm_angle_slider.valueChanged.connect(lambda v_: self._wm_angle_lbl.setText(f"Rotation: {v_}°"))
        c1.addWidget(self._wm_angle_lbl); c1.addWidget(self._wm_angle_slider); ga.addLayout(c1)
        c2 = QVBoxLayout(); self._wm_opac_lbl = QLabel("Opacity: 25%")
        self._wm_opac_slider = QSlider(Qt.Horizontal)
        self._wm_opac_slider.setRange(5, 90); self._wm_opac_slider.setValue(25)
        self._wm_opac_slider.valueChanged.connect(lambda v_: self._wm_opac_lbl.setText(f"Opacity: {v_}%"))
        c2.addWidget(self._wm_opac_lbl); c2.addWidget(self._wm_opac_slider); ga.addLayout(c2)
        tl.addLayout(ga)
        r = QHBoxLayout(); r.addWidget(QLabel("Font size:"))
        self._wm_size_spin = QSpinBox(); self._wm_size_spin.setRange(16, 150); self._wm_size_spin.setValue(56)
        r.addWidget(self._wm_size_spin)
        r.addWidget(QLabel("Color:"))
        self._wm_color_combo = QComboBox()
        for n, c in [("Blue","#2563eb"),("Gray","#64748b"),("Red","#dc2626"),
                     ("Navy","#1e3a8a"),("Green","#16a34a"),("Black","#000000")]:
            self._wm_color_combo.addItem(n, c)
        r.addWidget(self._wm_color_combo); r.addStretch(); tl.addLayout(r)
        self._wm_chk_bg = QCheckBox("Stamp behind text"); self._wm_chk_bg.setChecked(True)
        tl.addWidget(self._wm_chk_bg); tl.addStretch()
        self._stamp_tabs.addTab(t, "Text Watermark")

        # Image Watermark
        t_img = QWidget(); il = QVBoxLayout(t_img); il.setSpacing(8)
        ir = QHBoxLayout(); ir.addWidget(QLabel("Watermark Image:"))
        self._wm_img_path_edit = QLineEdit(); self._wm_img_path_edit.setPlaceholderText("Select image (.png, .jpg, .webp, .svg, .bmp)...")
        b_img = QPushButton("Browse Image"); b_img.setObjectName("browse")
        b_img.setIcon(IconFont.icon("image", "#334155", 28)); b_img.setIconSize(QSize(13, 13))
        b_img.clicked.connect(self._browse_wm_img)
        ir.addWidget(self._wm_img_path_edit, 1); ir.addWidget(b_img)
        il.addLayout(ir)

        iga = QHBoxLayout(); iga.setSpacing(12)
        ic1 = QVBoxLayout(); self._wm_img_angle_lbl = QLabel("Rotation: 0°")
        self._wm_img_angle_slider = QSlider(Qt.Horizontal)
        self._wm_img_angle_slider.setRange(-180, 180); self._wm_img_angle_slider.setValue(0)
        self._wm_img_angle_slider.valueChanged.connect(lambda v_: self._wm_img_angle_lbl.setText(f"Rotation: {v_}°"))
        ic1.addWidget(self._wm_img_angle_lbl); ic1.addWidget(self._wm_img_angle_slider); iga.addLayout(ic1)

        ic2 = QVBoxLayout(); self._wm_img_opac_lbl = QLabel("Opacity: 30%")
        self._wm_img_opac_slider = QSlider(Qt.Horizontal)
        self._wm_img_opac_slider.setRange(5, 100); self._wm_img_opac_slider.setValue(30)
        self._wm_img_opac_slider.valueChanged.connect(lambda v_: self._wm_img_opac_lbl.setText(f"Opacity: {v_}%"))
        ic2.addWidget(self._wm_img_opac_lbl); ic2.addWidget(self._wm_img_opac_slider); iga.addLayout(ic2)

        ic3 = QVBoxLayout(); self._wm_img_scale_lbl = QLabel("Scale: 50% of page")
        self._wm_img_scale_slider = QSlider(Qt.Horizontal)
        self._wm_img_scale_slider.setRange(10, 120); self._wm_img_scale_slider.setValue(50)
        self._wm_img_scale_slider.valueChanged.connect(lambda v_: self._wm_img_scale_lbl.setText(f"Scale: {v_}% of page"))
        ic3.addWidget(self._wm_img_scale_lbl); ic3.addWidget(self._wm_img_scale_slider); iga.addLayout(ic3)
        il.addLayout(iga)

        pr = QHBoxLayout(); pr.addWidget(QLabel("Position:"))
        self._wm_img_pos_combo = QComboBox()
        self._wm_img_pos_combo.addItems(["Center", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right", "Tiled (Repeat across page)"])
        pr.addWidget(self._wm_img_pos_combo, 1); pr.addStretch(); il.addLayout(pr)

        self._wm_img_chk_bg = QCheckBox("Stamp behind text (background)")
        self._wm_img_chk_bg.setChecked(True)
        il.addWidget(self._wm_img_chk_bg); il.addStretch()
        self._stamp_tabs.addTab(t_img, "Image Watermark")
        # Numbers
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("Format:"))
        self._num_fmt_combo = QComboBox()
        self._num_fmt_combo.addItems(["Page X of Y","Page X","X / Y","- X -","X"])
        r.addWidget(self._num_fmt_combo, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Position:"))
        self._num_pos_combo = QComboBox()
        self._num_pos_combo.addItems(["Bottom Center","Bottom Right","Bottom Left","Top Right","Top Center"])
        r.addWidget(self._num_pos_combo, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Font size:"))
        self._num_size_spin = QSpinBox(); self._num_size_spin.setRange(8, 24); self._num_size_spin.setValue(10)
        r.addWidget(self._num_size_spin); r.addStretch(); tl.addLayout(r)
        tl.addStretch(); self._stamp_tabs.addTab(t, "Numbers")
        # Header / Footer
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(hint_label("Placeholders: {page} {pages} {filename} {date} {time} {title}"))
        r = QHBoxLayout(); r.addWidget(QLabel("Header:"))
        self._hf_header_edit = QLineEdit(); self._hf_header_edit.setPlaceholderText("e.g. {title}")
        r.addWidget(self._hf_header_edit, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Footer:"))
        self._hf_footer_edit = QLineEdit(); self._hf_footer_edit.setPlaceholderText("Page {page} of {pages}")
        r.addWidget(self._hf_footer_edit, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Font size:"))
        self._hf_size_spin = QSpinBox(); self._hf_size_spin.setRange(6, 18); self._hf_size_spin.setValue(9)
        r.addWidget(self._hf_size_spin); r.addStretch(); tl.addLayout(r)
        tl.addStretch(); self._stamp_tabs.addTab(t, "Header / Footer")
        tv.addWidget(self._stamp_tabs); v.addWidget(tc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT PDF FILE"))
        orow = QHBoxLayout()
        self._wm_out_edit = QLineEdit(); self._wm_out_edit.setPlaceholderText("stamped.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._wm_out_edit, "PDF Files (*.pdf)"))
        orow.addWidget(self._wm_out_edit, 1); orow.addWidget(b)
        ov.addLayout(orow); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_wm_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._wm_file_lbl.setText(p)
        self._wm_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_stamped.pdf"))

    def _browse_wm_img(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Select Watermark Image", self._wm_img_path_edit.text() or "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.svg);;All Files (*.*)")
        if f:
            self._wm_img_path_edit.setText(f)

    # ── Organize ─────────────────────────────────────────────
    def _build_organize_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF DOCUMENT"))
        self._org_dz = DropZone("Drop a PDF to rotate, delete, reorder",
                                 accept_filter="PDF Files (*.pdf)", icon_name="organize")
        self._org_dz.files_dropped.connect(self._on_org_file_dropped)
        cv.addWidget(self._org_dz)
        self._org_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._org_file_lbl.setWordWrap(True)
        cv.addWidget(self._org_file_lbl); v.addWidget(c)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        self._org_tabs = QTabWidget()
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("Rotation:"))
        self._rot_angle_combo = QComboBox()
        self._rot_angle_combo.addItem("90° CW", 90); self._rot_angle_combo.addItem("180°", 180)
        self._rot_angle_combo.addItem("270° CW", 270)
        r.addWidget(self._rot_angle_combo)
        r.addWidget(QLabel("Apply to:"))
        self._rot_scope_combo = QComboBox()
        self._rot_scope_combo.addItem("All", "all"); self._rot_scope_combo.addItem("Specific", "custom")
        r.addWidget(self._rot_scope_combo); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Pages:"))
        self._rot_pages_edit = QLineEdit(); self._rot_pages_edit.setPlaceholderText("1, 3, 5-7")
        r.addWidget(self._rot_pages_edit, 1); tl.addLayout(r); tl.addStretch()
        self._org_tabs.addTab(t, "Rotate")
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(QLabel("Pages to remove:"))
        self._del_pages_edit = QLineEdit(); self._del_pages_edit.setPlaceholderText("2, 4, 7-9")
        tl.addWidget(self._del_pages_edit); tl.addStretch()
        self._org_tabs.addTab(t, "Delete")
        t = QWidget(); tl = QVBoxLayout(t); tl.addWidget(QLabel("Reverse page order.")); tl.addStretch()
        self._org_tabs.addTab(t, "Reverse")
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("Insert from:"))
        self._ins_pdf_edit = QLineEdit(); r.addWidget(self._ins_pdf_edit, 1)
        ib = QPushButton("Browse"); ib.setObjectName("browse")
        ib.setIcon(IconFont.icon("folder", "#334155", 28)); ib.setIconSize(QSize(13, 13))
        def _pick():
            p, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
            if p: self._ins_pdf_edit.setText(p)
        ib.clicked.connect(_pick); r.addWidget(ib); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Before page:"))
        self._ins_pos_spin = QSpinBox(); self._ins_pos_spin.setRange(1, 99999)
        r.addWidget(self._ins_pos_spin); r.addWidget(QLabel("Source pages:"))
        self._ins_pages_edit = QLineEdit(); self._ins_pages_edit.setPlaceholderText("blank = all")
        r.addWidget(self._ins_pages_edit, 1); tl.addLayout(r); tl.addStretch()
        self._org_tabs.addTab(t, "Insert")
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        r = QHBoxLayout(); r.addWidget(QLabel("Target:"))
        self._resize_target_combo = QComboBox()
        for l, d in [("A4","a4"),("US Letter","letter"),("US Legal","legal"),("A5","a5"),("Fit to A4","fit")]:
            self._resize_target_combo.addItem(l, d)
        r.addWidget(self._resize_target_combo)
        r.addWidget(QLabel("Margin (mm):"))
        self._resize_margin_spin = QSpinBox(); self._resize_margin_spin.setRange(0, 60)
        r.addWidget(self._resize_margin_spin); r.addStretch(); tl.addLayout(r); tl.addStretch()
        self._org_tabs.addTab(t, "Resize")
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(QLabel("Detect and remove blank pages."))
        r = QHBoxLayout(); r.addWidget(QLabel("Strictness:"))
        self._blank_thresh = QLineEdit("0.995"); r.addWidget(self._blank_thresh, 1)
        tl.addLayout(r); tl.addStretch()
        self._org_tabs.addTab(t, "Remove Blanks")
        tv.addWidget(self._org_tabs); v.addWidget(tc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT PDF FILE"))
        orow = QHBoxLayout()
        self._org_out_edit = QLineEdit(); self._org_out_edit.setPlaceholderText("organized.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._org_out_edit, "PDF Files (*.pdf)"))
        orow.addWidget(self._org_out_edit, 1); orow.addWidget(b)
        ov.addLayout(orow); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_org_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._org_file_lbl.setText(p)
        self._org_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_organized.pdf"))

    # ── Tools (Metadata / QR) ────────────────────────────────
    def _build_tools_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        self._tool_tabs = QTabWidget()
        # Metadata
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        self._meta_dz = DropZone("Drop a PDF to view/edit metadata",
                                  accept_filter="PDF Files (*.pdf)", icon_name="tag")
        self._meta_dz.files_dropped.connect(self._on_meta_file_dropped)
        tl.addWidget(self._meta_dz)
        self._meta_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._meta_file_lbl.setWordWrap(True); tl.addWidget(self._meta_file_lbl)
        self._meta_inputs = {}
        for field in ["Title","Author","Subject","Keywords","Creator"]:
            r = QHBoxLayout()
            l = QLabel(f"{field}:"); l.setMinimumWidth(72)
            le = QLineEdit(); self._meta_inputs[field.lower()] = le
            r.addWidget(l); r.addWidget(le, 1); tl.addLayout(r)
        self._meta_chk_clear = QCheckBox("Wipe all metadata")
        tl.addWidget(self._meta_chk_clear)
        r = QHBoxLayout(); r.addWidget(QLabel("Output:"))
        self._meta_out_edit = QLineEdit(); r.addWidget(self._meta_out_edit, 1)
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._meta_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(b); tl.addLayout(r); tl.addStretch()
        self._tool_tabs.addTab(t, "PDF Metadata")
        # QR
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(QLabel("Enter URL, Text, Wi-Fi, or Contact info:"))
        self._qr_text_edit = QTextEdit(); self._qr_text_edit.setMaximumHeight(70)
        self._qr_text_edit.setPlaceholderText("https://example.com"); tl.addWidget(self._qr_text_edit)
        r = QHBoxLayout(); r.addWidget(QLabel("Box Size:"))
        self._qr_size_spin = QSpinBox(); self._qr_size_spin.setRange(4, 30); self._qr_size_spin.setValue(10)
        r.addWidget(self._qr_size_spin); r.addWidget(QLabel("Border:"))
        self._qr_border_spin = QSpinBox(); self._qr_border_spin.setRange(1, 10); self._qr_border_spin.setValue(4)
        r.addWidget(self._qr_border_spin); r.addStretch(); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Save to:"))
        self._qr_out_edit = QLineEdit(); self._qr_out_edit.setPlaceholderText("qrcode.png")
        qb = QPushButton("Browse"); qb.setObjectName("browse")
        qb.setIcon(IconFont.icon("folder", "#334155", 28)); qb.setIconSize(QSize(13, 13))
        qb.clicked.connect(lambda: self._browse_save_file(self._qr_out_edit, "PNG (*.png);;JPEG (*.jpg)"))
        r.addWidget(self._qr_out_edit, 1); r.addWidget(qb); tl.addLayout(r); tl.addStretch()
        self._tool_tabs.addTab(t, "QR Code")
        tv.addWidget(self._tool_tabs); v.addWidget(tc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_meta_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._meta_file_lbl.setText(p)
        self._meta_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_meta.pdf"))
        try:
            meta = PdfReader(p).metadata or {}
            for k in ["title","author","subject","keywords","creator"]:
                self._meta_inputs[k].setText(str(meta.get("/" + k.capitalize()) or ""))
        except Exception: pass

    # ── Style ────────────────────────────────────────────────
    def _build_style_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT DOCUMENT TO INSPECT"))
        self._style_dz = DropZone("Drop a .docx, .pdf, or .html document",
            accept_filter="Documents (*.docx *.docm *.pdf *.html *.htm)", icon_name="style")
        self._style_dz.files_dropped.connect(self._on_style_file_dropped)
        cv.addWidget(self._style_dz)
        self._style_file_lbl = QLabel("No document selected", objectName="filelabel")
        self._style_file_lbl.setWordWrap(True)
        cv.addWidget(self._style_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("SAVE REPORT"))
        r = QHBoxLayout()
        self._style_out_edit = QLineEdit(); self._style_out_edit.setPlaceholderText("report.txt (optional)")
        rb = QPushButton("Browse"); rb.setObjectName("browse")
        rb.setIcon(IconFont.icon("folder", "#334155", 28)); rb.setIconSize(QSize(13, 13))
        rb.clicked.connect(lambda: self._browse_save_file(self._style_out_edit, "Text Report (*.txt)"))
        r.addWidget(self._style_out_edit, 1); r.addWidget(rb); ov.addLayout(r)
        self._style_chk_html = QCheckBox("Also generate HTML Style Guide")
        self._style_chk_html.setStyleSheet(f"font-weight: 600; color: {ACCENT};")
        ov.addWidget(self._style_chk_html); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_style_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._style_file_lbl.setText(p)
        self._style_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_style_report.txt"))

    # ── Source ───────────────────────────────────────────────
    def _build_source_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT DOCUMENT TO INSPECT"))
        self._src_dz = DropZone("Drop a document",
            accept_filter="Documents (*.docx *.docm *.xlsx *.xlsm *.pptx *.pptm *.pdf *.html *.htm *.txt *.md)",
            icon_name="source")
        self._src_dz.files_dropped.connect(self._on_src_file_dropped)
        cv.addWidget(self._src_dz)
        self._src_file_lbl = QLabel("No document selected", objectName="filelabel")
        self._src_file_lbl.setWordWrap(True)
        cv.addWidget(self._src_file_lbl); v.addWidget(c)
        cc = self._make_card(); cmpv = QVBoxLayout(cc)
        cmpv.setContentsMargins(16, 14, 16, 14); cmpv.setSpacing(8)
        cmpv.addWidget(section_label("COMPONENT TO VIEW"))
        r = QHBoxLayout(); r.addWidget(QLabel("Part:"))
        self._src_comp_combo = QComboBox()
        for l, d in [("List all parts","__list__"),("word/document.xml","word/document.xml"),
                     ("word/styles.xml","word/styles.xml"),("word/numbering.xml","word/numbering.xml"),
                     ("word/settings.xml","word/settings.xml"),("word/theme/theme1.xml","word/theme/theme1.xml"),
                     ("[Content_Types].xml","[Content_Types].xml"),
                     ("xl/workbook.xml","xl/workbook.xml"),
                     ("ppt/presentation.xml","ppt/presentation.xml"),
                     ("PDF page stream","__pdf_stream__")]:
            self._src_comp_combo.addItem(l, d)
        r.addWidget(self._src_comp_combo, 1); cmpv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Page number:"))
        self._src_page_spin = QSpinBox(); self._src_page_spin.setRange(1, 99999)
        r.addWidget(self._src_page_spin); r.addStretch(); cmpv.addLayout(r)
        v.addWidget(cc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT"))
        self._src_chk_html = QCheckBox("Generate HTML + CSS export (DOCX only)")
        self._src_chk_html.setStyleSheet(f"font-weight: 600; color: {ACCENT};")
        ov.addWidget(self._src_chk_html)
        r = QHBoxLayout()
        self._src_out_edit = QLineEdit(); self._src_out_edit.setPlaceholderText("document_source.xml")
        ob = QPushButton("Browse"); ob.setObjectName("browse")
        ob.setIcon(IconFont.icon("folder", "#334155", 28)); ob.setIconSize(QSize(13, 13))
        ob.clicked.connect(lambda: self._browse_save_file(
            self._src_out_edit, "HTML (*.html);;XML (*.xml);;Text (*.txt);;All Files (*.*)"))
        r.addWidget(self._src_out_edit, 1); r.addWidget(ob); ov.addLayout(r)
        v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    def _on_src_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._src_file_lbl.setText(p)
        ext = Path(p).suffix.lower(); stem = Path(p).stem
        target = None
        if ext in (".docx", ".docm"):
            self._src_out_edit.setText(str(Path(p).parent / f"{stem}_document.xml")); target = "word/document.xml"
        elif ext in (".xlsx", ".xlsm"):
            self._src_out_edit.setText(str(Path(p).parent / f"{stem}_workbook.xml")); target = "xl/workbook.xml"
        elif ext in (".pptx", ".pptm"):
            self._src_out_edit.setText(str(Path(p).parent / f"{stem}_presentation.xml")); target = "ppt/presentation.xml"
        elif ext == ".pdf":
            self._src_out_edit.setText(str(Path(p).parent / f"{stem}_page_stream.txt")); target = "__pdf_stream__"
        else:
            self._src_out_edit.setText(str(Path(p).parent / f"{stem}_source.txt"))
        if target:
            for i in range(self._src_comp_combo.count()):
                if self._src_comp_combo.itemData(i) == target:
                    self._src_comp_combo.setCurrentIndex(i); break

    # ── Optimize ─────────────────────────────────────────────
    def _build_optimize_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF TO OPTIMIZE"))
        self._opt_dz = DropZone("Drop a PDF to compress",
                                 accept_filter="PDF Files (*.pdf)", icon_name="compress")
        self._opt_dz.files_dropped.connect(self._on_opt_file_dropped)
        cv.addWidget(self._opt_dz)
        self._opt_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._opt_file_lbl.setWordWrap(True)
        cv.addWidget(self._opt_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("COMPRESSION PRESET"))
        self._opt_preset_combo = QComboBox()
        self._opt_preset_combo.addItem("Lossless — no quality loss", "lossless")
        self._opt_preset_combo.addItem("Balanced — moderate downsample", "balanced")
        self._opt_preset_combo.addItem("Aggressive — smallest file", "aggressive")
        ov.addWidget(self._opt_preset_combo)
        ov.addWidget(hint_label("PyMuPDF required for balanced/aggressive."))
        r = QHBoxLayout()
        self._opt_out_edit = QLineEdit(); self._opt_out_edit.setPlaceholderText("compressed.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._opt_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._opt_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_opt_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._opt_file_lbl.setText(p)
        self._opt_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_compressed.pdf"))

    # ── Batch ────────────────────────────────────────────────
    def _build_batch_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("BATCH CONFIGURATION"))
        cv.addWidget(hint_label("Apply one operation to every PDF in a folder."))
        r = QHBoxLayout(); r.addWidget(QLabel("Input folder:"))
        self._batch_in_edit = QLineEdit(); r.addWidget(self._batch_in_edit, 1)
        bi = QPushButton("Browse"); bi.setObjectName("browse")
        bi.setIcon(IconFont.icon("folder", "#334155", 28)); bi.setIconSize(QSize(13, 13))
        bi.clicked.connect(lambda: self._browse_dir(self._batch_in_edit)); r.addWidget(bi); cv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Output folder:"))
        self._batch_out_edit = QLineEdit(); r.addWidget(self._batch_out_edit, 1)
        bo = QPushButton("Browse"); bo.setObjectName("browse")
        bo.setIcon(IconFont.icon("folder", "#334155", 28)); bo.setIconSize(QSize(13, 13))
        bo.clicked.connect(lambda: self._browse_dir(self._batch_out_edit)); r.addWidget(bo); cv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("File pattern:"))
        self._batch_pattern_edit = QLineEdit("*.pdf"); r.addWidget(self._batch_pattern_edit, 1)
        cv.addLayout(r); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("BATCH OPERATION"))
        self._batch_op_combo = QComboBox()
        self._batch_op_combo.addItem("Compress every PDF", "compress")
        self._batch_op_combo.addItem("Add watermark", "watermark")
        self._batch_op_combo.addItem("Number pages", "numbering")
        self._batch_op_combo.addItem("Strip metadata", "metadata_clear")
        self._batch_op_combo.addItem("Remove blank pages", "remove_blanks")
        ov.addWidget(self._batch_op_combo)
        r = QHBoxLayout(); r.addWidget(QLabel("Watermark text:"))
        self._batch_wm_text = QLineEdit("CONFIDENTIAL"); r.addWidget(self._batch_wm_text, 1)
        ov.addLayout(r); v.addWidget(oc)
        v.addStretch()
        sc.setWidget(w); return sc

    # ── History ──────────────────────────────────────────────
    def _build_history_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("RECENT JOBS"))
        cv.addWidget(hint_label("Double-click an entry to re-run it with the same settings."))
        self._history_list = QListWidget(); self._history_list.setMinimumHeight(180)
        self._history_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._history_list.itemDoubleClicked.connect(self._history_rerun)
        cv.addWidget(self._history_list, 1)
        r = QHBoxLayout()
        bc = QPushButton("Clear History"); bc.setObjectName("tool_small")
        bc.setIcon(IconFont.icon("clear", "#334155", 24)); bc.setIconSize(QSize(12, 12))
        bc.clicked.connect(self._history_clear)
        br = QPushButton("Refresh"); br.setObjectName("tool_small")
        br.setIcon(IconFont.icon("refresh", "#334155", 24)); br.setIconSize(QSize(12, 12))
        br.clicked.connect(self._history_reload)
        r.addWidget(br); r.addWidget(bc); r.addStretch(); cv.addLayout(r)
        v.addWidget(c)
        v.addStretch()
        sc.setWidget(w); return sc

    def _history_reload(self):
        if not hasattr(self, "_history_list"): return
        self._history_list.clear()
        for item in self._history.items:
            when = item.get("when", "")[:19].replace("T", " ")
            summary = item.get("summary", "")[:80]
            action = item.get("action", "?")
            li = QListWidgetItem(f"[{when}]  {action}:  {summary}")
            li.setData(Qt.UserRole, item); li.setIcon(IconFont.icon("history", ACCENT, 28))
            self._history_list.addItem(li)

    def _history_clear(self):
        self._history.clear(); self._history_reload()

    def _history_rerun(self, li):
        item = li.data(Qt.UserRole)
        if not item: return
        a = item.get("action", ""); p = item.get("params", {})
        if a and p: self._start_worker(a, p)

    # ── Visual Organizer ─────────────────────────────────────
    def _build_page_organizer_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF TO ORGANIZE VISUALLY"))
        self._vorg_dz = DropZone("Drop a PDF to load thumbnails",
                                  accept_filter="PDF Files (*.pdf)", icon_name="page_view")
        self._vorg_dz.files_dropped.connect(self._on_vorg_file_dropped)
        cv.addWidget(self._vorg_dz)
        self._vorg_file_lbl = QLabel("No PDF loaded", objectName="filelabel")
        self._vorg_file_lbl.setWordWrap(True)
        cv.addWidget(self._vorg_file_lbl); v.addWidget(c)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        tv.addWidget(section_label("PAGES (DRAG TO REORDER)"))
        tb = QHBoxLayout(); tb.setSpacing(5)
        def tbt(ic, txt, slot):
            b = QPushButton(txt); b.setObjectName("tool_small")
            b.setIcon(IconFont.icon(ic, "#334155", 24)); b.setIconSize(QSize(12, 12))
            b.clicked.connect(slot); return b
        tb.addWidget(tbt("rotate", "Rotate CW", self._vorg_rotate_cw))
        tb.addWidget(tbt("reverse", "Rotate CCW", self._vorg_rotate_ccw))
        tb.addWidget(tbt("delete", "Delete", self._vorg_delete_selected))
        tb.addWidget(tbt("refresh", "Restore", self._vorg_restore_all))
        tb.addWidget(tbt("swap", "Reverse", self._vorg_reverse))
        tb.addStretch(); tv.addLayout(tb)
        self._vorg_status = QLabel("Load a PDF to begin.", objectName="hint")
        tv.addWidget(self._vorg_status)
        self._vorg_list = QListWidget(); self._vorg_list.setObjectName("thumblist")
        self._vorg_list.setViewMode(QListView.IconMode)
        self._vorg_list.setIconSize(QSize(130, 170)); self._vorg_list.setGridSize(QSize(160, 210))
        self._vorg_list.setResizeMode(QListView.Adjust)
        self._vorg_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._vorg_list.setDefaultDropAction(Qt.MoveAction)
        self._vorg_list.setMovement(QListView.Static)
        self._vorg_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._vorg_list.setMinimumHeight(300)
        self._vorg_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._vorg_list.setSpacing(4)
        tv.addWidget(self._vorg_list, 1); v.addWidget(tc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT PDF FILE"))
        r = QHBoxLayout()
        self._vorg_out_edit = QLineEdit(); self._vorg_out_edit.setPlaceholderText("reorganized.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._vorg_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._vorg_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc)
        sc.setWidget(w); return sc

    def _on_vorg_file_dropped(self, paths):
        if not paths: return
        p = paths[0]
        if fitz is None:
            self._log_msg("Visual organizer requires PyMuPDF."); return
        self._vorg_file_lbl.setText(p)
        self._vorg_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_reorganized.pdf"))
        self._vorg_source_pdf = p
        self._vorg_list.clear(); self._visual_pages = []
        self._vorg_status.setText("Loading thumbnails...")
        if self._thumb_worker and self._thumb_worker.isRunning(): return
        self._thumb_worker = ThumbnailWorker(p, width=130)
        self._thumb_worker.thumb_ready.connect(self._vorg_add_thumb)
        self._thumb_worker.finished_all.connect(self._vorg_thumbs_done)
        self._thumb_worker.start()

    def _vorg_add_thumb(self, idx, png_bytes):
        img = QImage.fromData(png_bytes, "PNG")
        if img.isNull(): return
        pm = QPixmap.fromImage(img)
        item = QListWidgetItem(f"P{idx+1}"); item.setIcon(QIcon(pm))
        item.setData(Qt.UserRole, {"src": idx, "rot": 0, "keep": True})
        item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        item.setFlags(item.flags() | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        self._vorg_list.addItem(item)
        self._visual_pages.append({"src": idx, "rot": 0, "keep": True})

    def _vorg_thumbs_done(self, total, error):
        if error: self._vorg_status.setText(f"Error: {error}"); return
        self._vorg_status.setText(f"{total} pages loaded. Drag to reorder.")

    def _vorg_selected_rows(self):
        return sorted({self._vorg_list.row(it) for it in self._vorg_list.selectedItems()})
    def _vorg_rotate_cw(self):
        for r in self._vorg_selected_rows():
            it = self._vorg_list.item(r); d = it.data(Qt.UserRole) or {}
            d["rot"] = (d.get("rot", 0) + 90) % 360; it.setData(Qt.UserRole, d)
            try:
                pm = it.icon().pixmap(it.icon().actualSize(QSize(130, 170)))
                it.setIcon(QIcon(pm.transformed(QTransform().rotate(90))))
            except Exception: pass
    def _vorg_rotate_ccw(self):
        for r in self._vorg_selected_rows():
            it = self._vorg_list.item(r); d = it.data(Qt.UserRole) or {}
            d["rot"] = (d.get("rot", 0) + 270) % 360; it.setData(Qt.UserRole, d)
            try:
                pm = it.icon().pixmap(it.icon().actualSize(QSize(130, 170)))
                it.setIcon(QIcon(pm.transformed(QTransform().rotate(-90))))
            except Exception: pass
    def _vorg_delete_selected(self):
        for r in sorted(self._vorg_selected_rows(), reverse=True):
            self._vorg_list.takeItem(r)
    def _vorg_restore_all(self):
        if not getattr(self, "_vorg_source_pdf", None): return
        self._vorg_list.clear(); self._visual_pages = []
        self._thumb_worker = ThumbnailWorker(self._vorg_source_pdf, width=130)
        self._thumb_worker.thumb_ready.connect(self._vorg_add_thumb)
        self._thumb_worker.finished_all.connect(self._vorg_thumbs_done)
        self._thumb_worker.start()
    def _vorg_reverse(self):
        items = []
        while self._vorg_list.count() > 0: items.append(self._vorg_list.takeItem(0))
        for it in reversed(items): self._vorg_list.addItem(it)
    def _collect_vorg_state(self):
        order = []
        for i in range(self._vorg_list.count()):
            it = self._vorg_list.item(i); d = it.data(Qt.UserRole) or {}
            order.append({"src": d.get("src", i), "rot": d.get("rot", 0), "keep": True})
        return order

    # ── N-up ─────────────────────────────────────────────────
    def _build_nup_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF FOR IMPOSITION"))
        self._nup_dz = DropZone("Drop a PDF to impose", accept_filter="PDF Files (*.pdf)", icon_name="nup")
        self._nup_dz.files_dropped.connect(self._on_nup_file_dropped)
        cv.addWidget(self._nup_dz)
        self._nup_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._nup_file_lbl.setWordWrap(True)
        cv.addWidget(self._nup_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("LAYOUT"))
        r = QHBoxLayout(); r.addWidget(QLabel("Layout:"))
        self._nup_layout_combo = QComboBox()
        self._nup_layout_combo.addItem("2-Up", "2up")
        self._nup_layout_combo.addItem("4-Up", "4up")
        self._nup_layout_combo.addItem("9-Up", "9up")
        self._nup_layout_combo.addItem("Booklet (saddle-stitch)", "booklet")
        r.addWidget(self._nup_layout_combo, 1); ov.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Sheet:"))
        self._nup_sheet_combo = QComboBox()
        self._nup_sheet_combo.addItem("A4", "a4")
        self._nup_sheet_combo.addItem("US Letter", "letter")
        self._nup_sheet_combo.addItem("US Legal", "legal")
        r.addWidget(self._nup_sheet_combo)
        r.addWidget(QLabel("Gutter (mm):"))
        self._nup_gutter_spin = QSpinBox(); self._nup_gutter_spin.setRange(0, 30); self._nup_gutter_spin.setValue(5)
        r.addWidget(self._nup_gutter_spin); r.addStretch(); ov.addLayout(r)
        r = QHBoxLayout()
        self._nup_out_edit = QLineEdit(); self._nup_out_edit.setPlaceholderText("imposed.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._nup_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._nup_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_nup_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._nup_file_lbl.setText(p)
        self._nup_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_imposed.pdf"))

    # ── Bates ────────────────────────────────────────────────
    def _build_bates_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("BATES NUMBERING"))
        self._bates_dz = DropZone("Drop one or more PDFs (numbered in order)",
                                   accept_filter="PDF Files (*.pdf)", multi=True, icon_name="bates")
        self._bates_dz.files_dropped.connect(self._on_bates_files_dropped)
        cv.addWidget(self._bates_dz)
        self._bates_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._bates_file_lbl.setWordWrap(True)
        cv.addWidget(self._bates_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("STAMP FORMAT"))
        r = QHBoxLayout(); r.addWidget(QLabel("Prefix:"))
        self._bates_prefix_edit = QLineEdit(); self._bates_prefix_edit.setPlaceholderText("ABC-")
        r.addWidget(self._bates_prefix_edit, 1)
        r.addWidget(QLabel("Start:"))
        self._bates_start_spin = QSpinBox(); self._bates_start_spin.setRange(1, 999999)
        r.addWidget(self._bates_start_spin); ov.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Digits:"))
        self._bates_digits_spin = QSpinBox(); self._bates_digits_spin.setRange(1, 10); self._bates_digits_spin.setValue(6)
        r.addWidget(self._bates_digits_spin)
        r.addWidget(QLabel("Suffix:"))
        self._bates_suffix_edit = QLineEdit(); r.addWidget(self._bates_suffix_edit, 1)
        ov.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Position:"))
        self._bates_pos_combo = QComboBox()
        self._bates_pos_combo.addItems(["bottom-right","bottom-left","bottom-center","top-right","top-left"])
        r.addWidget(self._bates_pos_combo)
        r.addWidget(QLabel("Font size:"))
        self._bates_size_spin = QSpinBox(); self._bates_size_spin.setRange(6, 20); self._bates_size_spin.setValue(9)
        r.addWidget(self._bates_size_spin); r.addStretch(); ov.addLayout(r)
        self._bates_merge_chk = QCheckBox("Merge into one output PDF"); self._bates_merge_chk.setChecked(True)
        ov.addWidget(self._bates_merge_chk)
        r = QHBoxLayout()
        self._bates_out_edit = QLineEdit(); self._bates_out_edit.setPlaceholderText("bates_stamped.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._bates_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._bates_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_bates_files_dropped(self, paths):
        pdfs = [p for p in paths if p.lower().endswith(".pdf")]
        if not pdfs: return
        self._bates_files = pdfs
        if len(pdfs) == 1:
            self._bates_file_lbl.setText(pdfs[0])
            self._bates_out_edit.setText(str(Path(pdfs[0]).parent / f"{Path(pdfs[0]).stem}_bates.pdf"))
        else:
            self._bates_file_lbl.setText(f"{len(pdfs)} PDFs — first: {Path(pdfs[0]).name}")
            self._bates_out_edit.setText(str(Path(pdfs[0]).parent / "bates_stamped.pdf"))

    # ── Compare ──────────────────────────────────────────────
    def _build_compare_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT TWO PDFs TO COMPARE"))
        r = QHBoxLayout(); r.addWidget(QLabel("PDF A:"))
        self._cmp_a_edit = QLineEdit(); r.addWidget(self._cmp_a_edit, 1)
        b1 = QPushButton("Browse"); b1.setObjectName("browse")
        b1.setIcon(IconFont.icon("folder", "#334155", 28)); b1.setIconSize(QSize(13, 13))
        b1.clicked.connect(self._pick_cmp_a); r.addWidget(b1); cv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("PDF B:"))
        self._cmp_b_edit = QLineEdit(); r.addWidget(self._cmp_b_edit, 1)
        b2 = QPushButton("Browse"); b2.setObjectName("browse")
        b2.setIcon(IconFont.icon("folder", "#334155", 28)); b2.setIconSize(QSize(13, 13))
        b2.clicked.connect(self._pick_cmp_b); r.addWidget(b2); cv.addLayout(r)
        v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OPTIONS"))
        self._cmp_ignore_ws_chk = QCheckBox("Ignore whitespace"); self._cmp_ignore_ws_chk.setChecked(True)
        self._cmp_ignore_case_chk = QCheckBox("Ignore case")
        ov.addWidget(self._cmp_ignore_ws_chk); ov.addWidget(self._cmp_ignore_case_chk)
        r = QHBoxLayout()
        self._cmp_out_edit = QLineEdit(); self._cmp_out_edit.setPlaceholderText("comparison_report.html")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._cmp_out_edit, "HTML (*.html)"))
        r.addWidget(self._cmp_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _pick_cmp_a(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF A", "", "PDF Files (*.pdf)")
        if p:
            self._cmp_a_edit.setText(p)
            if not self._cmp_out_edit.text():
                self._cmp_out_edit.setText(str(Path(p).parent / "comparison_report.html"))
    def _pick_cmp_b(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PDF B", "", "PDF Files (*.pdf)")
        if p: self._cmp_b_edit.setText(p)

    # ── OCR ──────────────────────────────────────────────────
    def _build_ocr_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT SCANNED PDF"))
        cv.addWidget(hint_label("Adds an invisible text layer over each page so the PDF becomes searchable."))
        self._ocr_dz = DropZone("Drop a scanned PDF", accept_filter="PDF Files (*.pdf)", icon_name="ocr")
        self._ocr_dz.files_dropped.connect(self._on_ocr_file_dropped)
        cv.addWidget(self._ocr_dz)
        self._ocr_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._ocr_file_lbl.setWordWrap(True)
        cv.addWidget(self._ocr_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OCR OPTIONS"))
        tess = find_tesseract()
        if tess:
            st = QLabel(f"Tesseract found: {tess}")
            st.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: 600;")
        else:
            st = QLabel("Tesseract NOT found. Install from github.com/UB-Mannheim/tesseract/wiki")
            st.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 600;")
        st.setWordWrap(True); ov.addWidget(st)
        r = QHBoxLayout(); r.addWidget(QLabel("Language:"))
        self._ocr_lang_combo = QComboBox()
        self._ocr_lang_combo.addItems(["eng","eng+fra","eng+deu","eng+spa","fra","deu","spa",
                                       "chi_sim","jpn","kor","ara","hin"])
        r.addWidget(self._ocr_lang_combo)
        r.addWidget(QLabel("DPI:"))
        self._ocr_dpi_spin = QSpinBox(); self._ocr_dpi_spin.setRange(100, 600); self._ocr_dpi_spin.setValue(200)
        r.addWidget(self._ocr_dpi_spin); r.addStretch(); ov.addLayout(r)
        r = QHBoxLayout()
        self._ocr_out_edit = QLineEdit(); self._ocr_out_edit.setPlaceholderText("searchable.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._ocr_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._ocr_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_ocr_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._ocr_file_lbl.setText(p)
        self._ocr_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_searchable.pdf"))

    # ── Mail Merge ───────────────────────────────────────────
    def _build_mail_merge_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("TEMPLATE & DATA SOURCE"))
        cv.addWidget(hint_label("Use Jinja2 placeholders in the DOCX template, e.g.  {{ name }}  or  {{ address }}"))
        r = QHBoxLayout(); r.addWidget(QLabel("Template:"))
        self._mm_template_edit = QLineEdit(); r.addWidget(self._mm_template_edit, 1)
        b1 = QPushButton("Browse"); b1.setObjectName("browse")
        b1.setIcon(IconFont.icon("folder", "#334155", 28)); b1.setIconSize(QSize(13, 13))
        b1.clicked.connect(self._pick_mm_template); r.addWidget(b1); cv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Data:"))
        self._mm_data_edit = QLineEdit(); r.addWidget(self._mm_data_edit, 1)
        b2 = QPushButton("Browse"); b2.setObjectName("browse")
        b2.setIcon(IconFont.icon("folder", "#334155", 28)); b2.setIconSize(QSize(13, 13))
        b2.clicked.connect(self._pick_mm_data); r.addWidget(b2); cv.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Output folder:"))
        self._mm_out_dir_edit = QLineEdit(); r.addWidget(self._mm_out_dir_edit, 1)
        b3 = QPushButton("Browse"); b3.setObjectName("browse")
        b3.setIcon(IconFont.icon("folder", "#334155", 28)); b3.setIconSize(QSize(13, 13))
        b3.clicked.connect(lambda: self._browse_dir(self._mm_out_dir_edit)); r.addWidget(b3); cv.addLayout(r)
        v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OPTIONS"))
        r = QHBoxLayout(); r.addWidget(QLabel("Format:"))
        self._mm_format_combo = QComboBox()
        self._mm_format_combo.addItem("Word (.docx)", "docx")
        self._mm_format_combo.addItem("PDF (via Word COM)", "pdf")
        r.addWidget(self._mm_format_combo); r.addStretch(); ov.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Filename from field:"))
        self._mm_name_field_edit = QLineEdit()
        self._mm_name_field_edit.setPlaceholderText("e.g. InvoiceNo (blank for auto-numbers)")
        r.addWidget(self._mm_name_field_edit, 1); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _pick_mm_template(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select DOCX Template", "", "Word (*.docx *.docm)")
        if p: self._mm_template_edit.setText(p)
    def _pick_mm_data(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select Data Source", "",
            "Data (*.csv *.json *.xlsx *.xls);;All Files (*.*)")
        if p: self._mm_data_edit.setText(p)

    # ── Signatures ───────────────────────────────────────────
    def _build_signature_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF DOCUMENT"))
        self._sig_dz = DropZone("Drop a PDF to sign or verify",
                                 accept_filter="PDF Files (*.pdf)", icon_name="signature")
        self._sig_dz.files_dropped.connect(self._on_sig_file_dropped)
        cv.addWidget(self._sig_dz)
        self._sig_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._sig_file_lbl.setWordWrap(True)
        cv.addWidget(self._sig_file_lbl); v.addWidget(c)
        tc = self._make_card(); tv = QVBoxLayout(tc)
        tv.setContentsMargins(16, 14, 16, 14); tv.setSpacing(8)
        self._sig_tabs = QTabWidget()
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(hint_label("Reads embedded signatures and reports signer, issuer, and integrity."))
        if not PYHANKO_OK:
            wl = QLabel("pyhanko not installed. Run: pip install pyhanko")
            wl.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 600;")
            tl.addWidget(wl)
        tl.addStretch(); self._sig_tabs.addTab(t, "Verify")
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(8)
        tl.addWidget(hint_label("Apply a signature using a PKCS#12 (.pfx / .p12) certificate."))
        r = QHBoxLayout(); r.addWidget(QLabel("Certificate:"))
        self._sig_pfx_edit = QLineEdit(); r.addWidget(self._sig_pfx_edit, 1)
        spb = QPushButton("Browse"); spb.setObjectName("browse")
        spb.setIcon(IconFont.icon("folder", "#334155", 28)); spb.setIconSize(QSize(13, 13))
        spb.clicked.connect(self._pick_sig_pfx); r.addWidget(spb); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Password:"))
        self._sig_pw_edit = QLineEdit(); self._sig_pw_edit.setEchoMode(QLineEdit.Password)
        r.addWidget(self._sig_pw_edit, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Reason:"))
        self._sig_reason_edit = QLineEdit("Digitally signed"); r.addWidget(self._sig_reason_edit, 1)
        tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Location:"))
        self._sig_location_edit = QLineEdit(); r.addWidget(self._sig_location_edit, 1); tl.addLayout(r)
        r = QHBoxLayout(); r.addWidget(QLabel("Field name:"))
        self._sig_field_edit = QLineEdit("Signature1"); r.addWidget(self._sig_field_edit, 1)
        tl.addLayout(r)
        if not PYHANKO_OK:
            wl = QLabel("pyhanko not installed. Run: pip install pyhanko")
            wl.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 600;")
            tl.addWidget(wl)
        tl.addStretch(); self._sig_tabs.addTab(t, "Sign")
        tv.addWidget(self._sig_tabs); v.addWidget(tc)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("OUTPUT PDF FILE (for signing)"))
        r = QHBoxLayout()
        self._sig_out_edit = QLineEdit(); self._sig_out_edit.setPlaceholderText("signed.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._sig_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._sig_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_sig_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._sig_file_lbl.setText(p)
        self._sig_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_signed.pdf"))
    def _pick_sig_pfx(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select PKCS#12 Certificate", "",
            "PKCS#12 (*.pfx *.p12);;All Files (*.*)")
        if p: self._sig_pfx_edit.setText(p)

    # ── PDF/A ────────────────────────────────────────────────
    def _build_pdfa_panel(self):
        sc = self._make_scroll(); w = QWidget(); v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0); v.setSpacing(10)
        c = self._make_card(); cv = QVBoxLayout(c)
        cv.setContentsMargins(16, 14, 16, 14); cv.setSpacing(8)
        cv.addWidget(section_label("SELECT PDF TO ARCHIVE"))
        cv.addWidget(hint_label("Converts to PDF/A — the ISO standard for long-term digital preservation."))
        self._pdfa_dz = DropZone("Drop a PDF to convert to PDF/A",
                                  accept_filter="PDF Files (*.pdf)", icon_name="archive")
        self._pdfa_dz.files_dropped.connect(self._on_pdfa_file_dropped)
        cv.addWidget(self._pdfa_dz)
        self._pdfa_file_lbl = QLabel("No PDF selected", objectName="filelabel")
        self._pdfa_file_lbl.setWordWrap(True)
        cv.addWidget(self._pdfa_file_lbl); v.addWidget(c)
        oc = self._make_card(); ov = QVBoxLayout(oc)
        ov.setContentsMargins(16, 14, 16, 14); ov.setSpacing(8)
        ov.addWidget(section_label("PDF/A OPTIONS"))
        gs = find_ghostscript()
        if gs:
            gl = QLabel(f"Ghostscript found: {gs}")
            gl.setStyleSheet("color: #16a34a; font-size: 11px; font-weight: 600;")
        else:
            gl = QLabel("Ghostscript NOT found. Install from ghostscript.com")
            gl.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 600;")
        gl.setWordWrap(True); ov.addWidget(gl)
        r = QHBoxLayout(); r.addWidget(QLabel("Level:"))
        self._pdfa_level_combo = QComboBox()
        self._pdfa_level_combo.addItem("PDF/A-1b — strict", "1")
        self._pdfa_level_combo.addItem("PDF/A-2b — recommended", "2")
        self._pdfa_level_combo.addItem("PDF/A-3b — allows attachments", "3")
        self._pdfa_level_combo.setCurrentIndex(1)
        r.addWidget(self._pdfa_level_combo, 1); ov.addLayout(r)
        r = QHBoxLayout()
        self._pdfa_out_edit = QLineEdit(); self._pdfa_out_edit.setPlaceholderText("archived_pdfa.pdf")
        b = QPushButton("Browse"); b.setObjectName("browse")
        b.setIcon(IconFont.icon("folder", "#334155", 28)); b.setIconSize(QSize(13, 13))
        b.clicked.connect(lambda: self._browse_save_file(self._pdfa_out_edit, "PDF Files (*.pdf)"))
        r.addWidget(self._pdfa_out_edit, 1); r.addWidget(b); ov.addLayout(r)
        v.addWidget(oc); v.addStretch()
        sc.setWidget(w); return sc

    def _on_pdfa_file_dropped(self, paths):
        if not paths: return
        p = paths[0]; self._pdfa_file_lbl.setText(p)
        self._pdfa_out_edit.setText(str(Path(p).parent / f"{Path(p).stem}_pdfa.pdf"))

    # ── Action bar & log ─────────────────────────────────────
    def _create_action_bar(self):
        c = QFrame(); c.setObjectName("card"); c.setGraphicsEffect(make_shadow())
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        v = QVBoxLayout(c); v.setContentsMargins(14, 10, 14, 10); v.setSpacing(8)
        self._progress = QProgressBar(); self._progress.setValue(0); self._progress.setTextVisible(False)
        v.addWidget(self._progress)
        row = QHBoxLayout(); row.setSpacing(8)
        self._status_lbl = QLabel("Ready")
        self._status_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-weight: 600;")
        self._status_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._open_btn = QPushButton("Open Folder"); self._open_btn.setObjectName("secondary")
        self._open_btn.setIcon(IconFont.icon("folder", "#334155", 28)); self._open_btn.setIconSize(QSize(14, 14))
        self._open_btn.clicked.connect(self._open_last_folder); self._open_btn.setEnabled(False)
        self._exec_btn = QPushButton("Execute Action"); self._exec_btn.setObjectName("primary")
        self._exec_btn.setIcon(IconFont.icon("play", "#ffffff", 28)); self._exec_btn.setIconSize(QSize(14, 14))
        self._exec_btn.clicked.connect(self._dispatch_action)
        row.addWidget(self._status_lbl, 1); row.addWidget(self._open_btn); row.addWidget(self._exec_btn)
        v.addLayout(row)
        return c

    def _create_log_panel(self):
        c = QFrame(); c.setObjectName("card"); c.setGraphicsEffect(make_shadow())
        c.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        v = QVBoxLayout(c); v.setContentsMargins(14, 8, 14, 8); v.setSpacing(5)
        h = QHBoxLayout(); h.setSpacing(6)
        il = QLabel(IconFont.glyph("list")); il.setFont(IconFont.font(12))
        il.setStyleSheet(f"color: {ACCENT};"); h.addWidget(il)
        h.addWidget(section_label("ACTIVITY LOG")); h.addStretch()
        cb = QPushButton("Clear"); cb.setObjectName("tool_small")
        cb.setIcon(IconFont.icon("clear", "#334155", 24)); cb.setIconSize(QSize(12, 12))
        cb.clicked.connect(lambda: self._log.clear()); h.addWidget(cb)
        v.addLayout(h)
        self._log = QTextEdit(objectName="log"); self._log.setReadOnly(True)
        self._log.setMinimumHeight(70); self._log.setMaximumHeight(130)
        v.addWidget(self._log)
        return c

    # ── Helpers ──────────────────────────────────────────────
    def _browse_dir(self, le):
        d = QFileDialog.getExistingDirectory(self, "Select Folder", le.text() or "")
        if d: le.setText(d)
    def _browse_save_file(self, le, f):
        p, _ = QFileDialog.getSaveFileName(self, "Save File", le.text() or "", f)
        if p: le.setText(p)
    def _log_msg(self, msg): self._log.append(msg)
    def _open_last_folder(self):
        if self._last_out_dir:
            p = Path(self._last_out_dir)
            target = p if p.is_dir() else p.parent
            if target.exists():
                try: os.startfile(str(target))
                except Exception: pass

    def _apply_theme(self):
        app = QApplication.instance()
        if self._dark_mode:
            app.setStyleSheet(build_dark_stylesheet())
            base_icon = "#cbd5e1"
            self._theme_btn.setIcon(IconFont.icon("sun", "#cbd5e1", 28))
        else:
            app.setStyleSheet(STYLE)
            base_icon = ACCENT
            self._theme_btn.setIcon(IconFont.icon("moon", "#334155", 28))
        self._theme_btn.setIconSize(QSize(15, 15))
        for btn in getattr(self, "_nav_buttons", []):
            active = (btn.property("active") == "true")
            icon_name = btn.property("icon_name") or "document"
            btn.setIcon(IconFont.icon(icon_name, "#ffffff" if active else base_icon, 32))
        if hasattr(self, "_exec_btn"):
            self._exec_btn.setIcon(IconFont.icon("play", "#ffffff", 28))
        for dz in self.findChildren(DropZone):
            dz._icon.setStyleSheet(f"color: {base_icon}; background: transparent; border: none;")

    def _toggle_dark_mode(self):
        self._dark_mode = not self._dark_mode
        self._settings.set("dark_mode", self._dark_mode)
        self._apply_theme()

    def closeEvent(self, ev):
        try: self._settings.save()
        except Exception: pass
        super().closeEvent(ev)

    # ── Dispatcher ───────────────────────────────────────────
    def _dispatch_action(self):
        idx = self._deck.currentIndex()
        action_name = ""; params = {}
        if idx == 0:
            pdf_path = self._split_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Please select a valid PDF first."); return
            out_dir = self._split_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_split")
            tab = self._split_tabs.currentIndex(); action_name = "split"
            params = {"pdf_path": pdf_path, "output_dir": out_dir}
            if tab == 0: params["mode"] = "all"
            elif tab == 1: params["mode"] = "single"; params["page"] = self._split_spin_single.value()
            elif tab == 2:
                s = self._split_spin_from.value(); e = self._split_spin_to.value()
                if s > e: self._log_msg("'From' cannot exceed 'To'."); return
                params["mode"] = "range"; params["start"] = s; params["end"] = e
            elif tab == 3:
                pages = parse_page_ranges(self._split_custom_edit.text().strip())
                if not pages: self._log_msg("Enter valid pages."); return
                params["mode"] = "custom"; params["pages"] = pages
            elif tab == 4: params["mode"] = "chunk"; params["chunk"] = self._split_spin_chunk.value()
            elif tab == 5:
                action_name = "split_by_size"
                params = {"pdf_path": pdf_path, "output_dir": out_dir, "target_mb": self._split_size_mb.value()}
        elif idx == 1:
            n = self._merge_list.count()
            if n < 2: self._log_msg("Add at least 2 PDFs."); return
            files = [self._merge_list.item(i).data(Qt.UserRole) for i in range(n)]
            out = self._merge_out_edit.text().strip() or str(Path(files[0]).parent / "merged_collection.pdf")
            action_name = "merge"; params = {"files": files, "out_file": out}
        elif idx == 2:
            if not self._conv_files: self._log_msg("Select files to convert."); return
            cidx = self._conv_type_combo.currentIndex()
            out = self._conv_out_edit.text().strip()
            action_name = "convert"
            tm = ["docx_to_pdf","excel_to_pdf","images_to_pdf","pdf_to_images",
                  "pdf_to_docx","pdf_to_txt","text_to_pdf"]
            first = self._conv_files[0]
            if not out: self._update_conv_out_hint(); out = self._conv_out_edit.text().strip()
            params = {"conv_type": tm[cidx], "input_path": first,
                      "img_paths": self._conv_files, "output_path": out}
        elif idx == 3:
            pdf_path = self._sec_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._sec_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_out.pdf")
            st = self._sec_tabs.currentIndex()
            if st == 0:
                pw = self._sec_user_pw.text().strip()
                if not pw: self._log_msg("Enter a user password."); return
                action_name = "security"
                params = {"sec_mode": "protect", "pdf_path": pdf_path, "out_file": out,
                          "user_pw": pw, "owner_pw": self._sec_owner_pw.text().strip(),
                          "allow_print": self._sec_chk_print.isChecked(),
                          "allow_copy": self._sec_chk_copy.isChecked()}
            elif st == 1:
                action_name = "security"
                params = {"sec_mode": "unlock", "pdf_path": pdf_path, "out_file": out,
                          "password": self._sec_unlock_pw.text().strip()}
            else:
                terms = self._redact_terms_edit.text().strip()
                if not terms: self._log_msg("Enter search terms."); return
                action_name = "redact"
                params = {"pdf_path": pdf_path, "out_file": out, "terms": terms,
                          "page_range": self._redact_pages_edit.text().strip(),
                          "fill": self._redact_fill_combo.currentData(),
                          "case_sensitive": self._redact_chk_case.isChecked()}
        elif idx == 4:
            pdf_path = self._wm_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._wm_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_stamped.pdf")
            wt = self._stamp_tabs.currentIndex()
            if wt == 0:
                action_name = "watermark"
                params = {"pdf_path": pdf_path, "out_file": out,
                          "wm_type": "text",
                          "text": self._wm_text_edit.text().strip() or "CONFIDENTIAL",
                          "angle": self._wm_angle_slider.value(),
                          "opacity": self._wm_opac_slider.value() / 100.0,
                          "font_size": self._wm_size_spin.value(),
                          "color_hex": self._wm_color_combo.currentData(),
                          "is_background": self._wm_chk_bg.isChecked()}
            elif wt == 1:
                img_p = self._wm_img_path_edit.text().strip()
                if not img_p or not os.path.exists(img_p):
                    self._log_msg("Select a valid watermark image."); return
                action_name = "watermark"
                pos_map = {0: "center", 1: "top-left", 2: "top-right", 3: "bottom-left", 4: "bottom-right", 5: "tiled"}
                params = {"pdf_path": pdf_path, "out_file": out,
                          "wm_type": "image",
                          "image_path": img_p,
                          "angle": self._wm_img_angle_slider.value(),
                          "opacity": self._wm_img_opac_slider.value() / 100.0,
                          "scale_pct": self._wm_img_scale_slider.value(),
                          "position": pos_map.get(self._wm_img_pos_combo.currentIndex(), "center"),
                          "is_background": self._wm_img_chk_bg.isChecked()}
            elif wt == 2:
                action_name = "numbering"
                pm = {0:"bottom-center",1:"bottom-right",2:"bottom-left",3:"top-right",4:"top-center"}
                params = {"pdf_path": pdf_path, "out_file": out,
                          "format": self._num_fmt_combo.currentText(),
                          "position": pm.get(self._num_pos_combo.currentIndex(), "bottom-center"),
                          "font_size": self._num_size_spin.value()}
            else:
                action_name = "header_footer"
                params = {"pdf_path": pdf_path, "out_file": out,
                          "header_text": self._hf_header_edit.text(),
                          "footer_text": self._hf_footer_edit.text(),
                          "font_size": self._hf_size_spin.value(), "color_hex": "#0f172a"}
        elif idx == 5:
            pdf_path = self._org_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._org_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_organized.pdf")
            ot = self._org_tabs.currentIndex(); action_name = "organize"
            if ot == 0:
                params = {"org_mode": "rotate", "pdf_path": pdf_path, "out_file": out,
                          "angle": self._rot_angle_combo.currentData(),
                          "scope": self._rot_scope_combo.currentData(),
                          "pages": parse_page_ranges(self._rot_pages_edit.text().strip())}
            elif ot == 1:
                dp = parse_page_ranges(self._del_pages_edit.text().strip())
                if not dp: self._log_msg("Enter pages to delete."); return
                params = {"org_mode": "delete", "pdf_path": pdf_path, "out_file": out, "delete_pages": dp}
            elif ot == 2:
                params = {"org_mode": "reverse", "pdf_path": pdf_path, "out_file": out}
            elif ot == 3:
                src = self._ins_pdf_edit.text().strip()
                if not src or not os.path.exists(src): self._log_msg("Select a source PDF."); return
                action_name = "insert_pages"
                params = {"base_pdf": pdf_path, "insert_pdf": src,
                          "position": self._ins_pos_spin.value(),
                          "pages": parse_page_ranges(self._ins_pages_edit.text().strip()),
                          "out_file": out}
            elif ot == 4:
                action_name = "resize"
                params = {"pdf_path": pdf_path, "out_file": out,
                          "target": self._resize_target_combo.currentData(),
                          "margin_mm": self._resize_margin_spin.value()}
            elif ot == 5:
                try: th = float(self._blank_thresh.text().strip())
                except ValueError: th = 0.995
                action_name = "remove_blanks"
                params = {"pdf_path": pdf_path, "out_file": out, "threshold": th}
        elif idx == 6:
            ttab = self._tool_tabs.currentIndex()
            if ttab == 0:
                pdf_path = self._meta_file_lbl.text().strip()
                if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                    self._log_msg("Select a valid PDF."); return
                out = self._meta_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_meta.pdf")
                action_name = "metadata"
                params = {"pdf_path": pdf_path, "out_file": out,
                          "clear_all": self._meta_chk_clear.isChecked(),
                          "title": self._meta_inputs["title"].text().strip(),
                          "author": self._meta_inputs["author"].text().strip(),
                          "subject": self._meta_inputs["subject"].text().strip(),
                          "keywords": self._meta_inputs["keywords"].text().strip(),
                          "creator": self._meta_inputs["creator"].text().strip()}
            else:
                text = self._qr_text_edit.toPlainText().strip()
                if not text: self._log_msg("Enter text or URL."); return
                out = self._qr_out_edit.text().strip() or str(Path.cwd() / "qrcode.png")
                action_name = "qrcode"
                params = {"text": text, "out_file": out,
                          "box_size": self._qr_size_spin.value(), "border": self._qr_border_spin.value()}
        elif idx == 7:
            doc_path = self._style_file_lbl.text().strip()
            if not doc_path or doc_path == "No document selected" or not os.path.exists(doc_path):
                self._log_msg("Select a document."); return
            action_name = "style_inspect"
            params = {"doc_path": doc_path,
                      "include_fonts": True, "include_colors": True,
                      "html_export": self._style_chk_html.isChecked(),
                      "out_report": self._style_out_edit.text().strip()}
        elif idx == 8:
            doc_path = self._src_file_lbl.text().strip()
            if not doc_path or doc_path == "No document selected" or not os.path.exists(doc_path):
                self._log_msg("Select a document."); return
            action_name = "source_view"
            params = {"doc_path": doc_path, "out_file": self._src_out_edit.text().strip(),
                      "component": self._src_comp_combo.currentData(),
                      "page_num": self._src_page_spin.value(),
                      "html_convert": self._src_chk_html.isChecked()}
        elif idx == 9:
            pdf_path = self._opt_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._opt_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_compressed.pdf")
            action_name = "compress"
            params = {"pdf_path": pdf_path, "out_file": out,
                      "preset": self._opt_preset_combo.currentData()}
        elif idx == 10:
            in_d = self._batch_in_edit.text().strip(); out_d = self._batch_out_edit.text().strip()
            if not in_d or not os.path.isdir(in_d): self._log_msg("Select an input folder."); return
            if not out_d: out_d = str(Path(in_d).parent / f"{Path(in_d).name}_batch")
            action_name = "batch"
            params = {"input_dir": in_d, "output_dir": out_d,
                      "pattern": self._batch_pattern_edit.text().strip() or "*.pdf",
                      "batch_op": self._batch_op_combo.currentData(),
                      "text": self._batch_wm_text.text().strip() or "CONFIDENTIAL",
                      "angle": 45, "opacity": 0.25, "font_size": 56,
                      "color_hex": ACCENT, "is_background": True,
                      "format": "Page X of Y", "position": "bottom-center"}
        elif idx == 11:
            self._log_msg("History is view-only. Double-click an entry to re-run."); return
        elif idx == 12:
            if not getattr(self, "_vorg_source_pdf", None) or self._vorg_list.count() == 0:
                self._log_msg("Load and reorder a PDF first."); return
            out = self._vorg_out_edit.text().strip() or str(Path(self._vorg_source_pdf).parent / f"{Path(self._vorg_source_pdf).stem}_reorganized.pdf")
            action_name = "organize_visual"
            params = {"pdf_path": self._vorg_source_pdf, "out_file": out,
                      "page_order": self._collect_vorg_state()}
        elif idx == 13:
            pdf_path = self._nup_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._nup_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_imposed.pdf")
            action_name = "nup"
            params = {"pdf_path": pdf_path, "out_file": out,
                      "layout": self._nup_layout_combo.currentData(),
                      "sheet_size": self._nup_sheet_combo.currentData(),
                      "gutter_mm": self._nup_gutter_spin.value()}
        elif idx == 14:
            files = getattr(self, "_bates_files", [])
            if not files: self._log_msg("Select PDFs for Bates."); return
            out = self._bates_out_edit.text().strip() or str(Path(files[0]).parent / "bates_stamped.pdf")
            action_name = "bates"
            params = {"files": files, "out_file": out,
                      "prefix": self._bates_prefix_edit.text(),
                      "suffix": self._bates_suffix_edit.text(),
                      "start": self._bates_start_spin.value(),
                      "digits": self._bates_digits_spin.value(),
                      "font_size": self._bates_size_spin.value(),
                      "position": self._bates_pos_combo.currentText(),
                      "color_hex": "#000000",
                      "merge_output": self._bates_merge_chk.isChecked()}
        elif idx == 15:
            a = self._cmp_a_edit.text().strip(); b = self._cmp_b_edit.text().strip()
            if not a or not os.path.exists(a) or not b or not os.path.exists(b):
                self._log_msg("Select two valid PDFs."); return
            out = self._cmp_out_edit.text().strip() or str(Path(a).parent / "comparison_report.html")
            action_name = "compare"
            params = {"pdf_a": a, "pdf_b": b, "out_file": out,
                      "ignore_whitespace": self._cmp_ignore_ws_chk.isChecked(),
                      "ignore_case": self._cmp_ignore_case_chk.isChecked()}
        elif idx == 16:
            pdf_path = self._ocr_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._ocr_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_searchable.pdf")
            action_name = "ocr"
            params = {"pdf_path": pdf_path, "out_file": out,
                      "lang": self._ocr_lang_combo.currentText(),
                      "dpi": self._ocr_dpi_spin.value()}
        elif idx == 17:
            tpl = self._mm_template_edit.text().strip(); data = self._mm_data_edit.text().strip()
            outd = self._mm_out_dir_edit.text().strip()
            if not tpl or not os.path.exists(tpl): self._log_msg("Select a valid DOCX template."); return
            if not data or not os.path.exists(data): self._log_msg("Select a valid data source."); return
            if not outd: outd = str(Path(tpl).parent / "mail_merge_output")
            action_name = "mail_merge"
            params = {"template": tpl, "data_source": data, "output_dir": outd,
                      "format": self._mm_format_combo.currentData(),
                      "name_field": self._mm_name_field_edit.text().strip()}
        elif idx == 18:
            pdf_path = self._sig_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            st = self._sig_tabs.currentIndex()
            if st == 0:
                action_name = "verify_signatures"; params = {"pdf_path": pdf_path}
            else:
                pfx = self._sig_pfx_edit.text().strip()
                if not pfx or not os.path.exists(pfx): self._log_msg("Select a .pfx / .p12 certificate."); return
                out = self._sig_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_signed.pdf")
                action_name = "sign_pdf"
                params = {"pdf_path": pdf_path, "out_file": out,
                          "pfx_path": pfx, "pfx_password": self._sig_pw_edit.text(),
                          "reason": self._sig_reason_edit.text().strip() or "Digitally signed",
                          "location": self._sig_location_edit.text().strip(),
                          "field_name": self._sig_field_edit.text().strip() or "Signature1"}
        elif idx == 19:
            pdf_path = self._pdfa_file_lbl.text().strip()
            if not pdf_path or pdf_path == "No PDF selected" or not os.path.exists(pdf_path):
                self._log_msg("Select a valid PDF."); return
            out = self._pdfa_out_edit.text().strip() or str(Path(pdf_path).parent / f"{Path(pdf_path).stem}_pdfa.pdf")
            action_name = "pdfa"
            params = {"pdf_path": pdf_path, "out_file": out,
                      "level": self._pdfa_level_combo.currentData()}
        if not action_name: return
        self._start_worker(action_name, params)

    def _start_worker(self, action, params):
        self._exec_btn.setEnabled(False); self._progress.setValue(0)
        self._status_lbl.setText("Processing...")
        self._active_worker = DocWorker(action, params)
        self._active_worker.progress.connect(self._progress.setValue)
        self._active_worker.log_line.connect(self._log_msg)
        self._active_worker.finished.connect(self._on_worker_finished)
        self._active_worker.start()

    def _on_worker_finished(self, success, message, out_path):
        self._exec_btn.setEnabled(self._deck.currentIndex() != 11)
        if success:
            self._progress.setValue(100); self._status_lbl.setText("Completed")
            self._log_msg(f"\n  SUCCESS: {message}\n     -> {out_path}\n")
            self._last_out_dir = out_path; self._open_btn.setEnabled(True)
            try:
                if self._history_enabled and self._active_worker:
                    self._history.add(action=self._active_worker.action, summary=message,
                                      out_path=out_path, params=self._active_worker.p)
                    self._history_reload()
            except Exception: pass
        else:
            self._status_lbl.setText("Failed")
            self._log_msg(f"\n  ERROR: {message}\n")

    def closeEvent(self, event):
        try:
            if hasattr(self, "_dev_gear") and self._dev_gear:
                self._dev_gear.stop()
        except Exception:
            pass
        super().closeEvent(event)


