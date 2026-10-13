"""
app.widgets — Custom UI widgets (RotatingGear, DropZone)
"""
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QFileDialog, QSizePolicy, QLayout
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPixmap, QTransform

from .icons import IconFont
from .styles import ACCENT, ACCENT_SOFT, TEXT_SECONDARY, TEXT_MUTED

class RotatingGear(QLabel):
    """
    Continuously rotating gold gear icon.
    Renders the MDL2 'settings' glyph and rotates it smoothly via QTimer.
    Uses a high-resolution source pixmap so edges stay crisp while spinning.
    """
    def __init__(self, size: int = 22, color: str = "#f59e0b",
                 interval_ms: int = 50, step_deg: int = 2, parent=None):
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self._step = step_deg
        self.setFixedSize(size, size)
        self.setStyleSheet("background: transparent; border: none;")
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # High-res source for smooth rotation (4x oversample)
        self._base = IconFont.pixmap("settings", color, size * 4, ratio=0.80)
        self._render()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(interval_ms)

    def _tick(self):
        try:
            self._angle = (self._angle + self._step) % 360
            self._render()
        except Exception:
            pass

    def _render(self):
        # Rotate the source pixmap (canvas grows, but content stays centered)
        rotated = self._base.transformed(
            QTransform().rotate(self._angle), Qt.SmoothTransformation
        )
        rw, rh = rotated.width(), rotated.height()
        bw = self._base.width()
        # Center-crop back to the original square so visual size is preserved
        x = (rw - bw) // 2
        y = (rh - bw) // 2
        cropped = rotated.copy(x, y, bw, bw)
        # Scale down to display size
        final = cropped.scaled(self._size, self._size,
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(final)

    def stop(self):
        try: self._timer.stop()
        except Exception: pass


class DropZone(QFrame):
    files_dropped = pyqtSignal(list)

    def __init__(self, title="Drop document here or click to browse",
                 accept_filter="All Files (*.*)", multi=False, parent=None,
                 icon_name="document"):
        super().__init__(parent)
        self.setObjectName("dropzone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumHeight(125)
        self._filter = accept_filter
        self._multi = multi

        # Layout grows to fit its content — no clipping, ever
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        # Icon
        self._icon = QLabel(IconFont.glyph(icon_name))
        self._icon.setFont(IconFont.font(26))
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self._icon.setStyleSheet(
            f"color: {ACCENT}; background: transparent; border: none;"
        )

        # Primary description — allows wrapping, never truncates
        self._text = QLabel(title)
        self._text.setAlignment(Qt.AlignCenter)
        self._text.setWordWrap(True)
        self._text.setMinimumWidth(160)
        self._text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._text.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12.5px; font-weight: 600; "
            f"background: transparent; border: none;"
        )

        # Secondary hint
        self._subtext = QLabel("Drag & drop files from your computer")
        self._subtext.setAlignment(Qt.AlignCenter)
        self._subtext.setWordWrap(True)
        self._subtext.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._subtext.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )

        layout.addWidget(self._icon)
        layout.addWidget(self._text)
        layout.addWidget(self._subtext)

    def mousePressEvent(self, event):
        if self._multi:
            paths, _ = QFileDialog.getOpenFileNames(self, "Select Documents", "", self._filter)
            if paths: self.files_dropped.emit(paths)
        else:
            path, _ = QFileDialog.getOpenFileName(self, "Select Document", "", self._filter)
            if path: self.files_dropped.emit([path])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"QFrame#dropzone {{ border-color: {ACCENT}; background: {ACCENT_SOFT}; }}")

    def dragLeaveEvent(self, event): self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile()]
        if paths: self.files_dropped.emit(paths)

