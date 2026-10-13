"""
app.styles — Design tokens and stylesheets for Document Studio Pro
"""

#  DESIGN TOKENS — BLUE / WHITE / BLACK
# ══════════════════════════════════════════════════════════════
# Accent (Royal Blue)
ACCENT          = "#2563eb"
ACCENT_HOVER    = "#3b82f6"
ACCENT_PRESSED  = "#1d4ed8"
ACCENT_SOFT     = "#eff6ff"
ACCENT_EDGE     = "#bfdbfe"

# Light-mode surfaces
BG_ROOT         = "#f8fafc"
BG_SIDEBAR      = "#f1f5f9"
BG_SURFACE_1    = "#ffffff"
BG_SURFACE_2    = "#f8fafc"
BG_ELEV         = "#e2e8f0"
BG_INSET        = "#f8fafc"

BORDER_SOFT     = "#e2e8f0"
BORDER_MED      = "#cbd5e1"
BORDER_STRONG   = "#94a3b8"

TEXT_STRONG     = "#000000"
TEXT_PRIMARY    = "#0f172a"
TEXT_SECONDARY  = "#334155"
TEXT_MUTED      = "#64748b"
TEXT_FAINT      = "#94a3b8"

# Dark-mode palette (high contrast)
D_BG_ROOT       = "#0b1220"
D_BG_SIDEBAR    = "#111827"
D_BG_SURFACE_1  = "#1e293b"
D_BG_SURFACE_2  = "#172033"
D_BG_ELEV       = "#334155"
D_BG_INSET      = "#0f172a"

D_BORDER_SOFT   = "#334155"
D_BORDER_MED    = "#475569"
D_BORDER_STRONG = "#64748b"

D_TEXT_STRONG   = "#ffffff"
D_TEXT_PRIMARY  = "#f1f5f9"
D_TEXT_SECOND   = "#cbd5e1"
D_TEXT_SECONDARY = D_TEXT_SECOND
D_TEXT_MUTED    = "#94a3b8"
D_TEXT_FAINT    = "#64748b"

D_ACCENT        = "#3b82f6"
D_ACCENT_HOVER  = "#60a5fa"
D_ACCENT_PRESS  = "#2563eb"
D_ACCENT_PRESSED = D_ACCENT_PRESS
D_ACCENT_SOFT   = "#1e3a8a"
D_ACCENT_EDGE   = "#1d4ed8"


STYLE = f"""
/* ═══════════════════════════════════════════════════════════
   DOCUMENT STUDIO PRO — Blue / White / Black
═══════════════════════════════════════════════════════════ */

QMainWindow, QWidget#root {{
    background-color: {BG_ROOT};
    font-family: "Segoe UI Variable Display","Segoe UI","Inter",sans-serif;
    color: {TEXT_PRIMARY};
}}

/* ── Sidebar ─────────────────────────────────────────────── */
QFrame#sidebar {{
    background: {BG_SIDEBAR};
    border-right: 1px solid {BORDER_MED};
}}
QScrollArea#sidebarScroll {{
    background: transparent;
    border: none;
}}
QScrollArea#sidebarScroll > QWidget > QWidget {{
    background: transparent;
}}
QFrame#sidebar QLabel#brand {{
    color: {TEXT_STRONG};
    font-size: 17px;
    font-weight: 800;
    letter-spacing: 0.3px;
}}
QFrame#sidebar QLabel#brand_sub {{
    color: {TEXT_MUTED};
    font-size: 10px;
    letter-spacing: 1.2px;
    font-weight: 700;
}}
QFrame#sidebar QLabel#nav_group {{
    color: {TEXT_FAINT};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.4px;
    padding: 10px 12px 4px 12px;
}}
QPushButton#nav_btn {{
    text-align: left;
    padding: 8px 12px;
    border: 1px solid transparent;
    border-radius: 6px;
    background: transparent;
    color: {TEXT_SECONDARY};
    font-size: 12.5px;
    font-weight: 600;
    min-height: 22px;
}}
QPushButton#nav_btn:hover {{
    background: {BG_ELEV};
    color: {TEXT_STRONG};
}}
QPushButton#nav_btn:focus {{
    outline: none;
    border: 1px solid {ACCENT};
}}
QPushButton#nav_btn[active="true"] {{
    background: {ACCENT};
    color: #ffffff;
    font-weight: 700;
    border: 1px solid {ACCENT_PRESSED};
}}

/* ── Cards ──────────────────────────────────────────────── */
QFrame#card {{
    background: {BG_SURFACE_1};
    border: 1px solid {BORDER_SOFT};
    border-radius: 10px;
}}

/* ── Drop zones ─────────────────────────────────────────── */
QFrame#dropzone {{
    background: {BG_INSET};
    border: 2px dashed {BORDER_MED};
    border-radius: 9px;
}}
QFrame#dropzone:hover {{
    border-color: {ACCENT};
    background: {ACCENT_SOFT};
}}

/* ── Tabs ───────────────────────────────────────────────── */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    background: {BG_ELEV};
    color: {TEXT_SECONDARY};
    padding: 7px 14px;
    margin-right: 3px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 600;
}}
QTabBar::tab:selected {{
    background: {ACCENT};
    color: #ffffff;
}}
QTabBar::tab:hover:!selected {{
    background: #cbd5e1;
    color: {TEXT_STRONG};
}}

/* ── Inputs ─────────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background: {BG_SURFACE_1};
    border: 1px solid {BORDER_MED};
    border-radius: 6px;
    color: {TEXT_PRIMARY};
    padding: 6px 10px;
    font-size: 12.5px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    min-height: 18px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {ACCENT};
    background: {BG_SURFACE_1};
}}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
    background: {BG_ELEV};
    color: {TEXT_FAINT};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox::down-arrow {{ image: none; width: 0; }}
QComboBox QAbstractItemView {{
    background: {BG_SURFACE_1};
    border: 1px solid {BORDER_MED};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    color: {TEXT_PRIMARY};
    padding: 4px;
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 16px;
    background: {BG_ELEV};
    border: none;
    border-radius: 3px;
    margin: 1px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {BORDER_MED};
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BG_ELEV};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #ffffff;
    border: 2px solid {ACCENT};
    width: 14px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 8px;
}}

QCheckBox, QRadioButton {{
    color: {TEXT_PRIMARY};
    font-size: 12.5px;
    spacing: 8px;
    padding: 3px 0;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_STRONG};
    background: {BG_SURFACE_1};
    border-radius: 3px;
}}
QRadioButton::indicator {{ border-radius: 8px; }}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton#primary {{
    background: {ACCENT};
    color: #ffffff;
    border: 1px solid {ACCENT_PRESSED};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12.5px;
    font-weight: 700;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:pressed {{ background: {ACCENT_PRESSED}; }}
QPushButton#primary:disabled {{
    background: {BG_ELEV};
    color: {TEXT_FAINT};
    border-color: {BORDER_MED};
}}

QPushButton#secondary {{
    background: {BG_SURFACE_1};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MED};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12.5px;
    font-weight: 600;
}}
QPushButton#secondary:hover {{
    background: {ACCENT_SOFT};
    color: {ACCENT_PRESSED};
    border-color: {ACCENT};
}}
QPushButton#secondary:disabled {{
    background: {BG_ELEV};
    color: {TEXT_FAINT};
    border-color: {BORDER_SOFT};
}}

QPushButton#browse, QPushButton#tool_small {{
    background: {BG_SURFACE_1};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_MED};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 11.5px;
    font-weight: 600;
}}
QPushButton#browse:hover, QPushButton#tool_small:hover {{
    background: {ACCENT_SOFT};
    color: {ACCENT_PRESSED};
    border-color: {ACCENT};
}}

/* ── Lists ──────────────────────────────────────────────── */
QListWidget {{
    background: {BG_SURFACE_1};
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
    color: {TEXT_PRIMARY};
    font-size: 12px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {BORDER_SOFT};
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background: {ACCENT_SOFT};
    color: {ACCENT_PRESSED};
    font-weight: 600;
}}
QListWidget::item:hover:!selected {{
    background: {BG_INSET};
}}

/* ── Progress ───────────────────────────────────────────── */
QProgressBar {{
    background: {BG_ELEV};
    border: none;
    border-radius: 4px;
    height: 6px;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 4px;
}}

/* ── Log ────────────────────────────────────────────────── */
QTextEdit#log {{
    background: {BG_INSET};
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    font-family: "Cascadia Mono","Consolas","Courier New",monospace;
    font-size: 11px;
    padding: 8px;
}}

/* ── Labels ─────────────────────────────────────────────── */
QLabel#title {{
    color: {TEXT_STRONG};
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.2px;
}}
QLabel#subtitle {{
    color: {TEXT_MUTED};
    font-size: 11.5px;
}}
QLabel#sectionlabel {{
    color: {TEXT_MUTED};
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 1.1px;
    padding-bottom: 2px;
}}
QLabel#filelabel {{
    color: {TEXT_PRIMARY};
    font-size: 12px;
}}
QLabel#badge {{
    color: {ACCENT_PRESSED};
    font-size: 11px;
    font-weight: 700;
    background: {ACCENT_SOFT};
    border: 1px solid {ACCENT_EDGE};
    border-radius: 5px;
    padding: 3px 9px;
}}
QLabel#hint {{
    color: {TEXT_FAINT};
    font-size: 11px;
}}

/* ── Scroll areas ───────────────────────────────────────── */
QScrollArea {{ border: none; background: transparent; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 1px; }}
QScrollBar::handle:vertical {{
    background: {BORDER_MED};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 1px; }}
QScrollBar::handle:horizontal {{
    background: {BORDER_MED};
    border-radius: 5px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QToolTip {{
    background: {TEXT_STRONG};
    color: #ffffff;
    border: none;
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 11px;
}}

/* ── Thumbnail list (visual organizer) ──────────────────── */
QListWidget#thumblist {{
    background: {BG_INSET};
    border: 1px solid {BORDER_SOFT};
    border-radius: 8px;
    padding: 8px;
}}
QListWidget#thumblist::item {{
    background: {BG_SURFACE_1};
    border: 2px solid {BORDER_SOFT};
    border-radius: 6px;
    margin: 5px;
    padding: 6px;
    color: {TEXT_SECONDARY};
}}
QListWidget#thumblist::item:selected {{
    background: {ACCENT_SOFT};
    border: 2px solid {ACCENT};
    color: {ACCENT_PRESSED};
}}
QListWidget#thumblist::item:hover {{ border-color: {ACCENT}; }}
"""

def build_dark_stylesheet():
    return f"""
QMainWindow, QWidget#root {{
    background-color: {D_BG_ROOT};
    font-family: "Segoe UI Variable Display","Segoe UI","Inter",sans-serif;
    color: {D_TEXT_PRIMARY};
}}

QFrame#sidebar {{ background: {D_BG_SIDEBAR}; border-right: 1px solid {D_BORDER_SOFT}; }}
QScrollArea#sidebarScroll {{ background: transparent; border: none; }}
QScrollArea#sidebarScroll > QWidget > QWidget {{ background: transparent; }}
QFrame#sidebar QLabel#brand {{ color: {D_TEXT_STRONG}; font-size: 17px; font-weight: 800; }}
QFrame#sidebar QLabel#brand_sub {{ color: {D_TEXT_MUTED}; font-size: 10px; letter-spacing: 1.2px; font-weight: 700; }}
QFrame#sidebar QLabel#nav_group {{ color: {D_TEXT_FAINT}; font-size: 10px; font-weight: 800; letter-spacing: 1.4px; padding: 10px 12px 4px 12px; }}
QPushButton#nav_btn {{
    text-align: left; padding: 8px 12px; border: 1px solid transparent;
    border-radius: 6px; background: transparent; color: {D_TEXT_SECOND};
    font-size: 12.5px; font-weight: 600; min-height: 22px;
}}
QPushButton#nav_btn:hover {{ background: {D_BG_ELEV}; color: {D_TEXT_STRONG}; }}
QPushButton#nav_btn[active="true"] {{
    background: {D_ACCENT};
    color: #ffffff;
    font-weight: 700;
    border: 1px solid {D_ACCENT_PRESS};
}}

QFrame#card {{
    background: {D_BG_SURFACE_1};
    border: 1px solid {D_BORDER_SOFT};
    border-radius: 10px;
}}
QFrame#dropzone {{
    background: {D_BG_INSET};
    border: 2px dashed {D_BORDER_MED};
    border-radius: 9px;
}}
QFrame#dropzone:hover {{
    border-color: {D_ACCENT};
    background: {D_ACCENT_SOFT};
}}
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    background: {D_BG_ELEV};
    color: {D_TEXT_SECOND};
    padding: 7px 14px; margin-right: 3px; border-radius: 5px;
    font-size: 12px; font-weight: 600;
}}
QTabBar::tab:selected {{ background: {D_ACCENT}; color: #ffffff; }}
QTabBar::tab:hover:!selected {{ background: {D_BORDER_MED}; color: {D_TEXT_STRONG}; }}

QLineEdit, QSpinBox, QComboBox {{
    background: {D_BG_INSET};
    border: 1px solid {D_BORDER_MED};
    border-radius: 6px;
    color: {D_TEXT_PRIMARY};
    padding: 6px 10px;
    font-size: 12.5px;
    selection-background-color: {D_ACCENT};
    selection-color: #ffffff;
    min-height: 18px;
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {D_ACCENT};
    background: {D_BG_SURFACE_2};
}}
QLineEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
    background: {D_BG_ELEV};
    color: {D_TEXT_MUTED};
}}
QComboBox QAbstractItemView {{
    background: {D_BG_SURFACE_1};
    border: 1px solid {D_BORDER_MED};
    selection-background-color: {D_ACCENT};
    selection-color: #ffffff;
    color: {D_TEXT_PRIMARY};
    outline: none;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 16px;
    background: {D_BG_ELEV};
    border: none;
    border-radius: 3px;
    margin: 1px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: {D_BORDER_MED}; }}

QSlider::groove:horizontal {{ height: 4px; background: {D_BG_ELEV}; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {D_ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: #ffffff;
    border: 2px solid {D_ACCENT};
    width: 14px;
    margin-top: -6px; margin-bottom: -6px;
    border-radius: 8px;
}}

QCheckBox, QRadioButton {{ color: {D_TEXT_PRIMARY}; font-size: 12.5px; spacing: 8px; padding: 3px 0; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px; height: 16px;
    border: 1px solid {D_BORDER_MED};
    background: {D_BG_INSET};
    border-radius: 3px;
}}
QRadioButton::indicator {{ border-radius: 8px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {D_ACCENT};
    border-color: {D_ACCENT};
}}

QPushButton#primary {{
    background: {D_ACCENT};
    color: #ffffff;
    border: 1px solid {D_ACCENT_PRESS};
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12.5px;
    font-weight: 700;
}}
QPushButton#primary:hover {{ background: {D_ACCENT_HOVER}; }}
QPushButton#primary:pressed {{ background: {D_ACCENT_PRESS}; }}
QPushButton#primary:disabled {{
    background: {D_BG_ELEV};
    color: {D_TEXT_MUTED};
    border-color: {D_BORDER_SOFT};
}}

QPushButton#secondary {{
    background: {D_BG_SURFACE_1};
    color: {D_TEXT_PRIMARY};
    border: 1px solid {D_BORDER_MED};
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 12.5px;
    font-weight: 600;
}}
QPushButton#secondary:hover {{
    background: {D_ACCENT_SOFT};
    color: #ffffff;
    border-color: {D_ACCENT};
}}
QPushButton#secondary:disabled {{
    background: {D_BG_ELEV};
    color: {D_TEXT_MUTED};
    border-color: {D_BORDER_SOFT};
}}

QPushButton#browse, QPushButton#tool_small {{
    background: {D_BG_SURFACE_1};
    color: {D_TEXT_PRIMARY};
    border: 1px solid {D_BORDER_MED};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 11.5px;
    font-weight: 600;
}}
QPushButton#browse:hover, QPushButton#tool_small:hover {{
    background: {D_ACCENT_SOFT};
    color: #ffffff;
    border-color: {D_ACCENT};
}}

QListWidget {{
    background: {D_BG_SURFACE_1};
    border: 1px solid {D_BORDER_SOFT};
    border-radius: 8px;
    color: {D_TEXT_PRIMARY};
    font-size: 12px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 8px;
    border-bottom: 1px solid {D_BORDER_SOFT};
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background: {D_ACCENT_SOFT};
    color: #ffffff;
    font-weight: 600;
}}
QListWidget::item:hover:!selected {{ background: {D_BG_ELEV}; }}

QProgressBar {{ background: {D_BG_ELEV}; border: none; border-radius: 4px; height: 6px; color: transparent; }}
QProgressBar::chunk {{ background: {D_ACCENT}; border-radius: 4px; }}

QTextEdit#log {{
    background: {D_BG_INSET};
    border: 1px solid {D_BORDER_SOFT};
    border-radius: 8px;
    color: {D_TEXT_PRIMARY};
    font-family: "Cascadia Mono","Consolas","Courier New",monospace;
    font-size: 11px;
    padding: 8px;
}}

QLabel#title {{ color: {D_TEXT_STRONG}; font-size: 18px; font-weight: 800; }}
QLabel#subtitle {{ color: {D_TEXT_SECOND}; font-size: 11.5px; }}
QLabel#sectionlabel {{ color: {D_TEXT_MUTED}; font-size: 10.5px; font-weight: 800; letter-spacing: 1.1px; padding-bottom: 2px; }}
QLabel#filelabel {{ color: {D_TEXT_PRIMARY}; font-size: 12px; }}
QLabel#badge {{
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    background: {D_ACCENT_PRESS};
    border: 1px solid {D_ACCENT};
    border-radius: 5px;
    padding: 3px 9px;
}}
QLabel#hint {{ color: {D_TEXT_MUTED}; font-size: 11px; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 1px; }}
QScrollBar::handle:vertical {{ background: {D_BORDER_MED}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {D_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 1px; }}
QScrollBar::handle:horizontal {{ background: {D_BORDER_MED}; border-radius: 5px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {D_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QToolTip {{
    background: {D_BG_SURFACE_1};
    color: {D_TEXT_STRONG};
    border: 1px solid {D_BORDER_MED};
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 11px;
}}

QListWidget#thumblist {{
    background: {D_BG_INSET};
    border: 1px solid {D_BORDER_SOFT};
    border-radius: 8px;
    padding: 8px;
}}
QListWidget#thumblist::item {{
    background: {D_BG_SURFACE_1};
    border: 2px solid {D_BORDER_SOFT};
    border-radius: 6px;
    margin: 5px;
    padding: 6px;
    color: {D_TEXT_SECONDARY};
}}
QListWidget#thumblist::item:selected {{
    background: {D_ACCENT_SOFT};
    border: 2px solid {D_ACCENT};
    color: #ffffff;
}}
QListWidget#thumblist::item:hover {{ border-color: {D_ACCENT}; }}
"""

