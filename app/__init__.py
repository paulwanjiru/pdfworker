"""
Document Studio Pro Application Package
"""

from .icons import IconFont
from .styles import STYLE, build_dark_stylesheet
from .config import AppSettings, JobHistory
from .helpers import parse_page_ranges
from .widgets import RotatingGear, DropZone
from .workers import DocWorker, ThumbnailWorker
from .main_window import DocumentStudioWindow
from . import deps

__all__ = [
    "IconFont",
    "STYLE",
    "build_dark_stylesheet",
    "AppSettings",
    "JobHistory",
    "parse_page_ranges",
    "RotatingGear",
    "DropZone",
    "DocWorker",
    "ThumbnailWorker",
    "DocumentStudioWindow",
    "deps",
]
