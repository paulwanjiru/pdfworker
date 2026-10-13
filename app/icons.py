"""
app.icons — Icon system for Document Studio Pro
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPixmap, QPainter, QIcon, QFontDatabase

class IconFont:
    GLYPHS = {
        "split":"\uE8C6","merge":"\uE8C8","convert":"\uE895","security":"\uE72E",
        "watermark":"\uE7E6","organize":"\uE8CB","tools":"\uE713","style":"\uE790",
        "source":"\uE943","play":"\uE768","folder":"\uE8B7","open":"\uE8E5",
        "save":"\uE74E","add":"\uE710","remove":"\uE738","delete":"\uE74D",
        "up":"\uE74A","down":"\uE74B","reverse":"\uE8CB","clear":"\uE894",
        "refresh":"\uE72C","check":"\uE73E","cancel":"\uE711","close":"\uE8BB",
        "info":"\uE946","warning":"\uE7BA","error":"\uEA39","success":"\uE930",
        "edit":"\uE70F","search":"\uE721","share":"\uE72D","link":"\uE71B",
        "print":"\uE749","unlock":"\uE785","key":"\uE192","shield":"\uEA18",
        "star":"\uE734","document":"\uE8A5","page":"\uE7C3","pdf":"\uEA90",
        "word":"\uE8A5","excel":"\uE9F9","image":"\uE91B","font":"\uE8D2",
        "color":"\uE790","code":"\uE943","scan":"\uE8FE","grid":"\uE80A",
        "list":"\uE8FD","layers":"\uE81E","paint":"\uE790","brush":"\uE7E6",
        "text":"\uE8D2","tag":"\uE8EC","globe":"\uE774","book":"\uE8F1",
        "chart":"\uE9D2","table":"\uE80A","qr":"\uE8FE","shield_check":"\uEA18",
        "compress":"\uE7B8","history":"\uE81C","batch":"\uE8F1","resize":"\uE740",
        "insert":"\uE710","blank":"\uE7C3","settings":"\uE713","moon":"\uE708",
        "sun":"\uE706","dpi":"\uE7F4","size":"\uE8A0",
        "redact":"\uE72E","nup":"\uE80A","booklet":"\uE8F1","bates":"\uE8EF",
        "compare":"\uE8CB","rotate":"\uE7AD","grid_view":"\uE80A","page_view":"\uE7C3",
        "swap":"\uE8AB","arrow_left":"\uE76B","arrow_right":"\uE76C",
        "zoom_in":"\uE8A3","zoom_out":"\uE71F","detect":"\uE721",
        "ocr":"\uE8FE","signature":"\uE929","archive":"\uE7B8",
        "template":"\uE8A5","mail":"\uE715",
    }
    _family = None; _icon_cache = {}

    @classmethod
    def family(cls):
        if cls._family: return cls._family
        try: fams = set(QFontDatabase().families())
        except Exception: fams = set()
        for cand in ("Segoe Fluent Icons","Segoe MDL2 Assets","Segoe UI Symbol"):
            if cand in fams:
                cls._family = cand; return cls._family
        cls._family = "Segoe UI Symbol"; return cls._family

    @classmethod
    def glyph(cls, name, default="\uE8A5"): return cls.GLYPHS.get(name, default)

    @classmethod
    def font(cls, px=16):
        f = QFont(cls.family()); f.setPixelSize(px); return f

    @classmethod
    def pixmap(cls, name, color="#2563eb", size=32, ratio=0.62):
        pm = QPixmap(size, size); pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.TextAntialiasing, True)
        p.setPen(QColor(color))
        f = QFont(cls.family()); f.setPixelSize(max(8, int(size*ratio))); p.setFont(f)
        p.drawText(pm.rect(), Qt.AlignCenter, cls.glyph(name))
        p.end(); return pm

    @classmethod
    def icon(cls, name, color="#2563eb", size=48):
        key = (name, color, size)
        if key in cls._icon_cache: return cls._icon_cache[key]
        ic = QIcon(cls.pixmap(name, color, size))
        cls._icon_cache[key] = ic
        return ic

