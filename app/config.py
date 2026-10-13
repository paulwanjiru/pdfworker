"""
app.config — Configuration, settings, and job history
"""
import sys, os, json, datetime, shutil
from pathlib import Path

def _app_data_dir():
    if os.name == "nt": base = Path(os.getenv("APPDATA", str(Path.home())))
    elif sys.platform == "darwin": base = Path.home() / "Library" / "Application Support"
    else: base = Path.home() / ".config"
    d = base / "DocumentStudioPro"; d.mkdir(parents=True, exist_ok=True); return d


def find_tesseract():
    p = shutil.which("tesseract")
    if p: return p
    for c in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
              r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
              "/usr/local/bin/tesseract", "/opt/homebrew/bin/tesseract",
              "/usr/bin/tesseract"]:
        if os.path.exists(c): return c
    return None


def find_ghostscript():
    for name in ("gswin64c", "gswin32c", "gs"):
        p = shutil.which(name)
        if p: return p
    try:
        import glob
        for pat in [r"C:\Program Files\gs\*\bin\gswin64c.exe",
                    r"C:\Program Files (x86)\gs\*\bin\gswin32c.exe"]:
            hits = sorted(glob.glob(pat))
            if hits: return hits[-1]
    except Exception: pass
    return None


class AppSettings:
    DEFAULTS = {"dark_mode": False, "history_enabled": True}
    def __init__(self):
        self.path = _app_data_dir() / "settings.json"
        self.data = dict(self.DEFAULTS); self._load()
    def _load(self):
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    for k in self.DEFAULTS:
                        if k in raw: self.data[k] = raw[k]
        except Exception: pass
    def save(self):
        try: self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        except Exception: pass
    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else self.DEFAULTS.get(key))
    def set(self, key, value, autosave=True):
        self.data[key] = value
        if autosave: self.save()


class JobHistory:
    MAX_ITEMS = 20
    def __init__(self):
        self.path = _app_data_dir() / "history.json"
        self.items = []; self._load()
    def _load(self):
        try:
            if self.path.exists():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(raw, list): self.items = raw[: self.MAX_ITEMS]
        except Exception: self.items = []
    def save(self):
        try: self.path.write_text(json.dumps(self.items, indent=2, default=str), encoding="utf-8")
        except Exception: pass
    def add(self, action, summary, out_path, params):
        self.items.insert(0, {"when": datetime.datetime.now().isoformat(timespec="seconds"),
                              "action": action, "summary": summary,
                              "output": out_path, "params": params})
        self.items = self.items[: self.MAX_ITEMS]; self.save()
    def clear(self): self.items = []; self.save()

