"""Reference renderer: a Python mirror of source/LuxeHijriPrayerView.mc.

It reads the real layout constants (source/Layout.mc), presets (source/Themes.mc), strings
(resources*/strings/strings.xml), vector art (resources/jsonData/*.json) and the generated
bitmap fonts of the requested screen size (resources[-round-WxH]/fonts), and draws a frame
with the same primitives, order and scaling as the Monkey C code. Shapes are rasterised with
4x supersampling (approximating device anti-aliasing); frames can be reduced to the 64-colour
MIP palette.

These images are REFERENCE RENDERS of the layout, not screenshots of the compiled watch face.
Prayer times, Hijri date and sun times are computed by tools/luxe_ref/calc.py (the mirror of
the Monkey C algorithms); sensor values are supplied by the caller.
"""
import json
import math
import os
import re
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

from luxe_ref import calc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = 4  # supersampling factor
BASE = 280


def _consts(path):
    src = open(os.path.join(ROOT, path)).read()
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", src)}


L = type("Layout", (), _consts("source/Layout.mc"))
T = _consts("source/Themes.mc")


def _themes():
    src = open(os.path.join(ROOT, "source", "Themes.mc")).read()
    body = src[src.index("const PRESETS"):src.index("const MULTICOLOR")]
    rows = re.findall(r"\[([^\[\]]+)\]", body)
    presets = [[int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{6}", r)] for r in rows]
    multi = [v == "true" for v in re.findall(r"true|false", src[src.index("const MULTICOLOR"):src.index("const SOURCE_COLORS")])]
    hexes = lambda a, b: [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{6}", src[src.index(a):src.index(b) if b else None])]
    srccol = hexes("const SOURCE_COLORS", "const COLOUR_CHOICES")
    colours = hexes("const COLOUR_CHOICES", "const TEXT_CHOICES")
    texts = hexes("const TEXT_CHOICES", "const HAND_CHOICES")
    h = hexes("const HAND_CHOICES", None)
    return presets, multi, srccol, colours, texts, [h[i:i + 2] for i in range(0, len(h), 2)]


PRESETS, MULTICOLOR, SOURCE_COLORS, COLOUR_CHOICES, TEXT_CHOICES, HAND_CHOICES = _themes()


def _friday():
    src = open(os.path.join(ROOT, "source", "Themes.mc")).read()
    hexes = lambda a, b: [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{6}", src[src.index(a):src.index(b)])]
    return hexes("const FRIDAY =", "const FRIDAY_HANDS"), hexes("const FRIDAY_HANDS", "const FRIDAY_NUMERALS")


FRIDAY, FRIDAY_HANDS = _friday()
FRIDAY_NUMERALS = T["FRIDAY_NUMERALS"]
FAMILIES = ["luxe", "classic", "sport"]
PRESET_NAMES = ["Luxury Blue", "Royal Gold", "Emerald Night", "Burgundy Royale", "Ice Silver", "Stealth", "Scarlet Noir", "Ember Gold", "Oasis Gold", "E-Ink"]
BACKGROUNDS = ["bg_mosque", "bg_geometric", "bg_marble", "bg_night"]
RESOLUTIONS = [218, 240, 260, 280, 360, 390, 416, 454, 466]


def strings(lang="eng"):
    out = {}
    for d in (["resources"] + (["resources-fre"] if lang == "fre" else [])):
        for el in ET.parse(os.path.join(ROOT, d, "strings", "strings.xml")).getroot():
            out[el.get("id")] = el.text
    return out


def rgb(c):
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


# ------------------------------------------------------------------ fonts
class BmFont:
    def __init__(self, folder, name):
        path = os.path.join(folder, name + ".fnt")
        self.chars = {}
        for line in open(path):
            kv = dict(re.findall(r"(\w+)=(\"[^\"]*\"|\S+)", line))
            if line.startswith("common"):
                self.height = int(kv["lineHeight"])
            elif line.startswith("char "):
                self.chars[int(kv["id"])] = {k: int(v) for k, v in kv.items() if k != "page"}
        self.atlas = Image.open(os.path.join(folder, name + ".png")).getchannel("A")

    def width(self, text):
        return sum(self.chars.get(ord(ch), self.chars[32])["xadvance"] for ch in text)


_FONTS = {}


def font_dir(size):
    return os.path.join(ROOT, "resources" if size == BASE else "resources-round-%dx%d" % (size, size), "fonts")


def font(name, size=BASE):
    key = (name, size)
    if key not in _FONTS:
        _FONTS[key] = BmFont(font_dir(size), name)
    return _FONTS[key]


# ------------------------------------------------------------------ Dc emulation
LEFT, CENTER, RIGHT, VCENTER = 2, 1, 0, 4
CLOCKWISE, COUNTER_CLOCKWISE = 1, 0


class Dc:
    def __init__(self, w=280, h=280):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S))
        self.d = ImageDraw.Draw(self.img)
        self.fg = (255, 255, 255)
        self.bg = (0, 0, 0)
        self.pen = 1

    @staticmethod
    def _p(x, y):
        return ((x + 0.5) * S, (y + 0.5) * S)

    def setColor(self, fg, bg=None):
        self.fg = rgb(fg)
        if bg is not None and bg >= 0:
            self.bg = rgb(bg)

    def setPenWidth(self, w):
        self.pen = w

    def clear(self):
        self.d.rectangle([0, 0, self.w * S, self.h * S], fill=self.bg)

    def fillRectangle(self, x, y, w, h):
        self.d.rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], fill=self.fg)

    def fillRoundedRectangle(self, x, y, w, h, r):
        self.d.rounded_rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], radius=r * S, fill=self.fg)

    def drawRoundedRectangle(self, x, y, w, h, r):
        self.d.rounded_rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], radius=r * S, outline=self.fg,
                                 width=max(1, int(self.pen * S)))

    def drawPoint(self, x, y):
        self.fillRectangle(x, y, 1, 1)

    def fillCircle(self, x, y, r):
        cx, cy = self._p(x, y)
        rr = (r + 0.5) * S
        self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=self.fg)

    def fillEllipse(self, x, y, a, b):
        cx, cy = self._p(x, y)
        self.d.ellipse([cx - (a + 0.5) * S, cy - (b + 0.5) * S, cx + (a + 0.5) * S, cy + (b + 0.5) * S], fill=self.fg)

    def drawCircle(self, x, y, r):
        cx, cy = self._p(x, y)
        ro = (r + self.pen / 2.0) * S
        self.d.ellipse([cx - ro, cy - ro, cx + ro, cy + ro], outline=self.fg, width=max(1, int(self.pen * S)))

    def drawArc(self, x, y, r, direction, start, end):
        if direction == COUNTER_CLOCKWISE:
            start, end = end, start
        a0, a1 = -start, -end
        while a1 <= a0:
            a1 += 360
        cx, cy = self._p(x, y)
        ro = (r + self.pen / 2.0) * S
        self.d.arc([cx - ro, cy - ro, cx + ro, cy + ro], a0, a1, fill=self.fg, width=int(self.pen * S))

    def drawLine(self, x1, y1, x2, y2):
        w = max(1, int(self.pen * S))
        self.d.line([self._p(x1, y1), self._p(x2, y2)], fill=self.fg, width=w)
        if self.pen > 1:
            for (x, y) in ((x1, y1), (x2, y2)):
                cx, cy = self._p(x, y)
                rr = self.pen * S / 2.0
                self.d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=self.fg)

    def fillPolygon(self, pts):
        self.d.polygon([self._p(x, y) for x, y in pts], fill=self.fg)

    def getTextWidthInPixels(self, text, f):
        return f.width(text)

    def drawText(self, x, y, f, text, just):
        w = f.width(text)
        if just & CENTER:
            x0 = x - w // 2
        elif just & LEFT:
            x0 = x
        else:
            x0 = x - w
        y0 = y - f.height // 2 if just & VCENTER else y
        for ch in text:
            g = f.chars.get(ord(ch), f.chars[32])
            if g["width"] > 0:
                glyph = f.atlas.crop((g["x"], g["y"], g["x"] + g["width"], g["y"] + g["height"]))
                glyph = glyph.resize((g["width"] * S, g["height"] * S), Image.NEAREST)
                self.img.paste(Image.new("RGB", glyph.size, self.fg),
                               ((x0 + g["xoffset"]) * S, (y0 + g["yoffset"]) * S), glyph)
            x0 += g["xadvance"]

    def bitmap(self):
        return self.img.resize((self.w, self.h), Image.BOX)


MIP_LEVELS = (0x00, 0x55, 0xAA, 0xFF)


def to_mip(img):
    lut = [min(MIP_LEVELS, key=lambda l: abs(l - v)) for v in range(256)]
    return img.point(lut * 3)


def circular(img, outside=(0, 0, 0)):
    mask = Image.new("L", (img.width * 4, img.height * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, img.width * 4 - 1, img.height * 4 - 1], fill=255)
    mask = mask.resize(img.size, Image.LANCZOS)
    out = Image.new("RGB", img.size, outside)
    out.paste(img, (0, 0), mask)
    return out


# ------------------------------------------------------------------ helpers mirrored from the view
def format_count(n):
    if n < 10000:
        return str(n)
    if n < 100000:
        return "%.1fk" % (n / 1000.0)
    return "%dk" % (n // 1000)


def read_source(src, sensors):
    """Mirror of DataFields.read() fed with simulated raw sensor values."""
    v = sensors.get(src)
    if src == 3:
        pct = int(round(v["battery"]))
        warn = 1 if pct <= 15 and not v.get("charging") else 0
        return [str(pct), v["battery"] / 100.0, warn]
    if v is None or v.get("value") is None:
        return [None, None, 0]
    x = v["value"]
    if src == 0:
        return [format_count(x), x / v["goal"] if v.get("goal") else None, 0]
    if src == 1:
        return [str(x), (x - 40.0) / 160.0, 1 if v.get("stale") else 0]
    if src == 2:
        return [format_count(x), None, 0]
    if src == 4:
        km = x / 100000.0
        return ["%.1f" % km if km < 100 else "%d" % km, None, 0]
    if src == 5:
        return [str(x), x / v["goal"] if v.get("goal") else None, 0]
    return [str(x), x / 100.0, 0]


def format_time(minutes, is24=True):
    if minutes is None:
        return "--:--"
    m = minutes % 1440
    h, mm = m // 60, m % 60
    if is24:
        return "%02d:%02d" % (h, mm)
    h = h % 12 or 12
    return "%d:%02d" % (h, mm)


LABELS = ["LabelSteps", "LabelHeart", "LabelCalories", "LabelBattery", "LabelKm", "LabelFloors",
          "LabelBodyBattery", "LabelStress", "LabelActive"]
NONE_SOURCE = 9
SUN_RING = 10
MOON = 11
# Themes.MOON_LIT, MOON_DARK, MOON_RING
MOON_LIT, MOON_DARK, MOON_RING = 0xFFF2C0, 0x2A3350, 0xC8D2E6
# Themes.SUN_DAY, SUN_TWILIGHT, SUN_NIGHT, SUN_NIGHT_TEXT
SUN_DAY, SUN_TWILIGHT, SUN_NIGHT, SUN_NIGHT_TEXT = 0xFFC83A, 0x8A5BC8, 0x3355AA, 0x9FB8FF


def ayah_pick(mode, fixed, included, hour):
    """Mirror of AyahPicker.pick()."""
    if mode == 2:
        return -1
    if mode == 1:
        return fixed
    idx = [i for i, v in enumerate(included) if v]
    return idx[hour % len(idx)] if idx else fixed
PRAYER_NAMES = {0: "Prayer0", 2: "Prayer2", 3: "Prayer3", 5: "Prayer5", 6: "Prayer6"}


class Face:
    def __init__(self, settings, lang="eng", size=BASE):
        self.s = settings
        self.size = size
        self.k = size / float(BASE)
        self.str = strings(lang)
        self.lite = settings.get("lite", False)     # Connect IQ 3 watches: vector dial only
        self.apply(False)
        f = lambda n: font(n, size)
        fam = FAMILIES[settings.get("font_family", 0)]
        self.f_num, self.f_l, self.f_m, self.f_s, self.f_xs, self.f_ar = (
            f("luxe_num"), f(fam + "_l"), f(fam + "_m"), f(fam + "_s"), f(fam + "_xs"), f("ar_small"))
        self.f_dl, self.f_dxs = f(fam + "_dl"), f(fam + "_dxs")

    def apply(self, friday):
        """Mirror of applySettings(): colours, dial and numerals of the style, or of the Friday dial."""
        st, size = self.s, self.size
        self.friday = friday
        self.c = FRIDAY if friday else PRESETS[st["preset"]]
        self.multi = st.get("gauge_colors", 0) == 0 and (friday or MULTICOLOR[st["preset"]])
        ink = not friday and st["preset"] == T["INK"]     # E-Ink: grey daylight ring and Moon
        self.sun_cols = [0x555555, 0xAAAAAA, 0x000000, 0x000000] if ink else [SUN_DAY, SUN_TWILIGHT, SUN_NIGHT, SUN_NIGHT_TEXT]
        self.moon_cols = [0xFFFFFF, 0x000000, 0x000000] if ink else [MOON_LIT, MOON_DARK, MOON_RING]
        self.text = TEXT_CHOICES[st["text_color"] - 1] if st.get("text_color") else self.c[T["TEXT"]]
        self.accent = COLOUR_CHOICES[st["accent_color"] - 1] if st.get("accent_color") else self.c[T["ACCENT"]]
        self.sec = COLOUR_CHOICES[st["seconds_color"] - 1] if st.get("seconds_color") else self.c[T["SECONDS"]]
        if st.get("hand_color"):
            hc = HAND_CHOICES[st["hand_color"] - 1]
        else:
            hc = FRIDAY_HANDS if friday else [self.c[T["GOLD"]], self.c[T["GOLD_DK"]]]
        self.hand_light, self.hand_dark = hc
        load = lambda n: json.load(open(os.path.join(ROOT, "resources", "jsonData", n + ".json")))
        self.bg_ops = load("bg_friday" if friday else BACKGROUNDS[st["background"]])
        self.frame_ops = load("frame")
        if self.lite:
            self.hd = None
        elif friday:
            path = os.path.join(ROOT, "hd", str(size), "drawables", "dial_fri.jpg")
            self.hd = Image.open(path).convert("RGB") if os.path.exists(path) else None
        else:
            self.hd = self.load_dial(st["preset"], st["background"], size)
        numerals = FRIDAY_NUMERALS if friday else st["preset"]
        self.nums = self.load_numerals(numerals, st.get("dial_digits", 0), size) if self.hd else None

    def friday_now(self, now, watch_offset):
        """Mirror of fridayNow(): Friday from 00:00 until Asr (15:00 without a location)."""
        s = self.s
        if not s.get("friday_design", True) or calc.day_of_week(calc.local_epoch_day(now, watch_offset)) != 5:
            return False
        if s["lat"] == 0 and s["lon"] == 0:
            return (now + watch_offset) % 86400 < 15 * 3600
        offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
        day = calc.local_epoch_day(now, offset)
        asr = calc.moment(day, self.day_times(day, offset / 3600.0)[calc.ASR], offset / 3600.0)
        if asr is None:
            return (now + watch_offset) % 86400 < 15 * 3600
        return now < asr

    def is_jumuah(self, day):
        return self.s.get("jumuah", 750) >= 0 and calc.day_of_week(day) == 5

    @staticmethod
    def load_dial(preset, bg, size):
        """HD static dial (tools/build_hd.py) if it has been generated, else None (vector fallback)."""
        for ext in ("png", "jpg"):
            path = os.path.join(ROOT, "hd", str(size), "drawables", "dial_%d_%d.%s" % (preset, bg, ext))
            if os.path.exists(path):
                return Image.open(path).convert("RGB")
        return None

    @staticmethod
    def load_numerals(preset, digits, size):
        """Numeral bitmaps 12 / 3 / 6 / 9 (tools/build_hd.py), or None."""
        paths = [os.path.join(ROOT, "hd", str(size), "drawables", "num_%d_%d_%d.png" % (preset, digits, q))
                 for q in range(4)]
        if not all(os.path.exists(f) for f in paths):
            return None
        return [Image.open(f).convert("RGBA") for f in paths]

    # ---- scaling (mirror of LuxeHijriPrayerView.p())
    def p(self, v):
        return int(math.floor(v * self.k + 0.5))

    def pen(self, w):
        return max(1, int(math.floor(w * self.k + 0.5)))

    def polar(self, r, a):
        c = self.size / 2.0
        return [int(math.floor(c + r * self.k * math.sin(a) + 0.5)), int(math.floor(c - r * self.k * math.cos(a) + 0.5))]

    def rotate_poly(self, pts, a):
        sn, cs = math.sin(a), math.cos(a)
        c = self.size / 2.0
        k = self.k
        return [(int(math.floor(c + (x * cs - y * sn) * k + 0.5)), int(math.floor(c + (x * sn + y * cs) * k + 0.5)))
                for x, y in pts]

    # ---- vector art interpreter (mirror of Backgrounds.draw)
    def draw_ops(self, dc, ops):
        c, p = self.c, self.p
        for op in ops:
            code = op[0]
            dc.setColor(c[op[1]], -1)
            if code == 0:
                dc.fillPolygon([(p(op[k]), p(op[k + 1])) for k in range(2, len(op) - 1, 2)])
            elif code == 1:
                dc.fillCircle(p(op[2]), p(op[3]), p(op[4]))
            elif code == 2:
                dc.setPenWidth(self.pen(op[2])); dc.drawLine(p(op[3]), p(op[4]), p(op[5]), p(op[6]))
            elif code == 3:
                dc.setPenWidth(self.pen(op[2]))
                for k in range(3, len(op) - 3, 2):
                    dc.drawLine(p(op[k]), p(op[k + 1]), p(op[k + 2]), p(op[k + 3]))
            elif code == 4:
                size = self.pen(op[2])
                for k in range(3, len(op) - 1, 2):
                    if size <= 1:
                        dc.drawPoint(p(op[k]), p(op[k + 1]))
                    else:
                        dc.fillRectangle(p(op[k]), p(op[k + 1]), size, size)
            elif code == 5:
                dc.setPenWidth(self.pen(op[2])); dc.drawCircle(p(op[3]), p(op[4]), p(op[5]))
            elif code == 6:
                dc.fillRectangle(p(op[2]), p(op[3]), max(1, p(op[4])), max(1, p(op[5])))
            elif code == 7:
                dc.setPenWidth(self.pen(op[2]))
                self.star8(dc, p(op[3]), p(op[4]), p(op[5]))
            elif code == 8:
                dc.fillRectangle(0, 0, self.size, self.size)
            elif code == 9:
                dc.fillCircle(p(op[3]), p(op[4]), p(op[5]))
                dc.setColor(c[op[2]], -1)
                dc.fillCircle(p(op[3] + op[6]), p(op[4] + op[7]), p(op[8]))
            elif code == 10:
                dc.fillRoundedRectangle(p(op[2]), p(op[3]), p(op[4]), p(op[5]), p(op[6]))
            elif code == 11:
                dc.setPenWidth(self.pen(op[2]))
                dc.drawRoundedRectangle(p(op[3]), p(op[4]), p(op[5]), p(op[6]), p(op[7]))
        dc.setPenWidth(1)

    @staticmethod
    def star8(dc, x, y, r):
        d = int(r * 0.7071 + 0.5)
        for (a, b, e, f) in [(x, y - r, x + r, y), (x + r, y, x, y + r), (x, y + r, x - r, y), (x - r, y, x, y - r),
                             (x - d, y - d, x + d, y - d), (x + d, y - d, x + d, y + d), (x + d, y + d, x - d, y + d),
                             (x - d, y + d, x - d, y - d)]:
            dc.drawLine(a, b, e, f)

    # ---- static layer (mirror of drawStaticLayer)
    def draw_static(self, dc):
        c, p = self.c, self.p
        if self.hd is not None:
            dc.img.paste(self.hd.resize((self.size * S, self.size * S), Image.NEAREST), (0, 0))
            for q, b in enumerate(self.nums or []):   # mirror of drawNumerals
                x, y = self.polar(L.NUM_R, q * math.pi / 2)
                big = b.resize((b.width * S, b.height * S), Image.NEAREST)
                dc.img.paste(big, ((x - b.width // 2) * S, (y - b.height // 2) * S), big)
            return
        dc.setColor(c[T["BG"]], c[T["BG"]]); dc.clear()
        self.draw_ops(dc, self.bg_ops)
        self.draw_ops(dc, self.frame_ops)
        # minute track
        dc.setPenWidth(self.pen(1))
        dc.setColor(c[T["TICK"]], -1)
        for i in range(60):
            if i % 5:
                a = i * math.pi / 30
                p0, p1 = self.polar(L.TICK_R_IN, a), self.polar(L.TICK_R_OUT, a)
                dc.drawLine(p0[0], p0[1], p1[0], p1[1])
        # hour indices (two-tone), numerals at 12 / 3 / 6 / 9
        for h in range(12):
            if h % 3 == 0:
                continue
            a = h * math.pi / 6
            wi, wo, ri, ro = L.IDX_W_IN, L.IDX_W_OUT, L.IDX_R_IN, L.IDX_R_OUT
            dc.setColor(c[T["GOLD"]], -1)
            dc.fillPolygon(self.rotate_poly([(-wi, -ri), (0, -ri), (0, -ro), (-wo, -ro)], a))
            dc.setColor(c[T["GOLD_DK"]], -1)
            dc.fillPolygon(self.rotate_poly([(0, -ri), (wi, -ri), (wo, -ro), (0, -ro)], a))
        for h, txt in ((0, "12"), (3, "3"), (6, "6"), (9, "9")):
            x, y = self.polar(L.NUM_R, h * math.pi / 6)
            dc.setColor(c[T["PLATE"]], -1)
            dc.drawText(x + 1, y + 1, self.f_num, txt, CENTER | VCENTER)
            dc.setColor(c[T["GOLD"]], -1)
            dc.drawText(x, y, self.f_num, txt, CENTER | VCENTER)
        # crescent above the date block
        dc.setColor(c[T["GOLD"]], -1)
        dc.fillCircle(p(140), p(L.CRESCENT_Y), p(6))
        dc.setColor(c[T["BG"]], -1)
        dc.fillCircle(p(143), p(L.CRESCENT_Y - 2), p(5))
        # gauge discs and tracks
        for (x, y) in self.gauge_centres():
            dc.setColor(c[T["PLATE"]], -1); dc.fillCircle(x, y, p(L.GAUGE_DISC_R))
            dc.setPenWidth(self.pen(1)); dc.setColor(c[T["GOLD_DK"]], -1); dc.drawCircle(x, y, p(L.GAUGE_DISC_R))
            dc.setPenWidth(self.pen(L.GAUGE_PEN)); dc.setColor(c[T["TRACK"]], -1); dc.drawCircle(x, y, p(L.GAUGE_R))
        dc.setPenWidth(1)
        # diamond under the hub
        dc.setColor(c[T["GOLD"]], -1)
        cx, dy = p(140), p(L.HUB_DIAMOND_Y)
        d = p(4)
        dc.fillPolygon([(cx, dy - d), (cx + d, dy), (cx, dy + d), (cx - d, dy)])

    def gauge_centres(self):
        p = self.p
        return [(p(140 - L.GAUGE_UP_DX), p(L.GAUGE_UP_Y)), (p(140 + L.GAUGE_UP_DX), p(L.GAUGE_UP_Y)),
                (p(140 - L.GAUGE_SIDE_DX), p(L.GAUGE_SIDE_Y)), (p(140 + L.GAUGE_SIDE_DX), p(L.GAUGE_SIDE_Y))]

    # ---- dynamic content
    def gauge_icon(self, dc, x, y, src):
        q = self.k
        P = lambda v: int(math.floor(v * q + 0.5))
        if src == 0:
            dc.fillEllipse(x - P(3), y + P(1), P(2), P(4)); dc.fillEllipse(x + P(3), y - P(1), P(2), P(4))
        elif src == 1:
            dc.fillCircle(x - P(2), y - P(2), P(3)); dc.fillCircle(x + P(2), y - P(2), P(3))
            dc.fillPolygon([(x - P(5), y - P(1)), (x + P(5), y - P(1)), (x, y + P(5))])
        elif src == 2:  # flame
            dc.fillPolygon([(x, y - P(6)), (x + P(4), y + P(1)), (x + P(3), y + P(4)), (x - P(3), y + P(4)), (x - P(4), y + P(1))])
        elif src == 3:  # battery
            dc.fillRectangle(x - P(6), y - P(3), P(11), P(7)); dc.fillRectangle(x + P(5), y - P(1), P(2), P(3))
        elif src == 4:  # route arrow
            dc.setPenWidth(self.pen(2)); dc.drawLine(x - P(5), y + P(4), x + P(4), y - P(4)); dc.setPenWidth(1)
            dc.fillPolygon([(x + P(5), y - P(5)), (x, y - P(4)), (x + P(4), y)])
        elif src == 5:
            dc.setPenWidth(self.pen(2))
            pts = [(x - P(6), y + P(4)), (x - P(3), y + P(4)), (x - P(3), y + P(1)), (x, y + P(1)), (x, y - P(2)),
                   (x + P(3), y - P(2)), (x + P(3), y - P(5)), (x + P(6), y - P(5))]
            for i in range(len(pts) - 1):
                dc.drawLine(*pts[i], *pts[i + 1])
            dc.setPenWidth(1)
        elif src == 6:
            dc.fillPolygon([(x + P(2), y - P(6)), (x - P(3), y + P(1)), (x + P(1), y + P(1))])
            dc.fillPolygon([(x - P(1), y - P(1)), (x + P(3), y - P(1)), (x - P(2), y + P(6))])
        elif src == 8:
            dc.setPenWidth(self.pen(2)); dc.drawCircle(x, y + P(1), P(5)); dc.drawLine(x, y + P(1), x + P(2), y - P(2))
            dc.setPenWidth(1); dc.fillRectangle(x - P(1), y - P(7), P(3), P(2))
        elif src == 7:
            dc.setPenWidth(self.pen(2))
            pts = [(x - P(6), y + P(1)), (x - P(3), y - P(3)), (x, y + P(3)), (x + P(3), y - P(3)), (x + P(6), y + P(1))]
            for i in range(len(pts) - 1):
                dc.drawLine(*pts[i], *pts[i + 1])
            dc.setPenWidth(1)

    def draw_gauge(self, dc, x, y, src, sensors):
        c, p = self.c, self.p
        if src == NONE_SOURCE:
            return
        color = SOURCE_COLORS[src] if self.multi else (self.text if self.s.get("gauge_colors") == 2 else self.accent)
        value, progress, flag = read_source(src, sensors)
        if progress is not None:
            pr = max(0.0, min(progress, 1.0))
            sweep = int(360.0 * pr)
            if sweep >= 2:
                end = 90 - sweep
                if end < 0:
                    end += 360
                col = c[T["WARN"]] if (src == 3 and flag == 1) else color
                dc.setColor(col, -1)
                dc.setPenWidth(self.pen(L.GAUGE_PEN))
                dc.drawArc(x, y, p(L.GAUGE_R), CLOCKWISE, 90, end)
                dc.setPenWidth(1)
        batt = src == 3
        dc.setColor(color, -1)
        self.gauge_icon(dc, x, y + p(L.GAUGE_BATT_ICON_DY if batt else L.GAUGE_ICON_DY), src)
        tcol = self.text
        if value is None:
            value, tcol = "--", c[T["DIM"]]
        elif flag == 1:
            tcol = c[T["WARN"]] if src == 3 else c[T["DIM"]]
        f = self.f_l if src == 3 else self.f_m
        inner = 2 * (p(L.GAUGE_R) - self.pen(L.GAUGE_PEN) // 2) - 2
        if f.width(value) > inner:
            f = self.f_m
            if f.width(value) > inner:
                f = self.f_s
        dc.setColor(tcol, -1)
        dc.drawText(x, y + p(L.GAUGE_VALUE_DY), f, value, CENTER | VCENTER)
        label = self.str[LABELS[src]]
        if src == 4 and self.s.get("statute"):
            label = self.str["LabelMi"]
        dc.setColor(color, -1)
        dc.drawText(x, y + p(L.GAUGE_BATT_LABEL_DY if batt else L.GAUGE_LABEL_DY), self.f_xs, label, CENTER | VCENTER)

    def day_times(self, day, tz):
        """Mirror of PrayerSchedule.update: computed times plus the per-prayer adjustments."""
        s = self.s
        t = list(calc.compute_day(day, s["lat"], s["lon"], tz, s["method"], s["asr"], s["highlat"]))
        for k, i in enumerate(calc.PRAYERS):
            adj = s.get("adjust", [0] * 5)[k]
            if t[i] is not None and adj:
                t[i] += adj / 60.0
        if self.is_jumuah(day):              # Friday: Jumu'ah at the fixed time
            t[calc.DHUHR] = self.s.get("jumuah", 750) / 60.0
        return t

    # ---- daylight / darkness ring (mirror of drawSunRing, sunArc, ringDeg)
    @staticmethod
    def ring_deg(m):
        return (90 - int((m - 720) / 4)) % 360

    def sun_arc(self, dc, x, y, r, m0, m1, color):
        if m1 - m0 < 4:
            return
        dc.setColor(color, -1)
        dc.drawArc(x, y, r, CLOCKWISE, self.ring_deg(m0), self.ring_deg(m1))

    def sun_ring(self, dc, x, y, now, watch_offset):
        s, p, c = self.s, self.p, self.c
        offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
        tz = offset / 3600.0
        day = calc.local_epoch_day(now, offset)
        comp = lambda d: self.day_times(day + d, tz)
        d0 = comp(0)
        rise, sset = calc.to_minutes(d0[calc.SUNRISE]), calc.to_minutes(d0[calc.SUNSET])
        if (s["lat"] == 0 and s["lon"] == 0) or rise is None or sset is None:
            dc.setColor(c[T["DIM"]], -1)
            dc.drawText(x, y + p(L.GAUGE_VALUE_DY), self.f_m, "--", CENTER | VCENTER)
            return
        fajr, isha = calc.to_minutes(d0[calc.FAJR]), calc.to_minutes(d0[calc.ISHA])
        fajr = rise if fajr is None else fajr
        isha = sset if isha is None else isha
        r = p(L.GAUGE_R)
        dc.setPenWidth(self.pen(L.GAUGE_PEN))
        SD, ST, SN, SNT = self.sun_cols
        self.sun_arc(dc, x, y, r, isha, fajr + 1440, SN)
        self.sun_arc(dc, x, y, r, fajr, rise, ST)
        self.sun_arc(dc, x, y, r, rise, sset, SD)
        self.sun_arc(dc, x, y, r, sset, isha, ST)
        dc.setPenWidth(1)
        now_min = ((now + offset) % 86400) // 60
        a = (now_min - 720) * math.pi / 720.0
        mx, my = x + int(r * math.sin(a)), y - int(r * math.cos(a))
        dc.setColor(0x000000, -1); dc.fillCircle(mx, my, p(4))
        dc.setColor(0xFFFFFF, -1); dc.fillCircle(mx, my, p(3))
        is_day = rise <= now_min < sset
        if is_day:
            target = calc.moment(day, d0[calc.SUNSET], tz)
        elif now_min >= sset:
            target = calc.moment(day + 1, comp(1)[calc.SUNRISE], tz)
        else:
            target = calc.moment(day, d0[calc.SUNRISE], tz)
        col = self.sun_cols[0] if is_day else self.sun_cols[3]
        ix, iy = x, y + p(L.GAUGE_ICON_DY)
        dc.setColor(col, -1)
        if is_day:
            dc.fillCircle(ix, iy, p(3))
            for k in range(8):
                ra = k * math.pi / 4
                dc.drawLine(ix + int(p(5) * math.cos(ra)), iy + int(p(5) * math.sin(ra)),
                            ix + int(p(6) * math.cos(ra)), iy + int(p(6) * math.sin(ra)))
        else:
            dc.fillCircle(ix, iy, p(5))
            dc.setColor(c[T["PLATE"]], -1); dc.fillCircle(ix + p(2), iy - p(2), p(4))
        value = "--" if target is None else calc.countdown_text(target - now)
        fnt = self.f_m if self.f_m.width(value) <= 2 * (r - 2) - 4 else self.f_s
        dc.setColor(self.text, -1)
        dc.drawText(x, y + p(L.GAUGE_VALUE_DY), fnt, value, CENTER | VCENTER)
        dc.setColor(col, -1)
        dc.drawText(x, y + p(L.GAUGE_LABEL_DY), self.f_xs, self.str["LabelDay" if is_day else "LabelNight"],
                    CENTER | VCENTER)

    def moon(self, dc, x, y, now):
        """Mirror of drawMoon."""
        p = self.p
        k, waxing, age = calc.moon_phase(now)
        s = 1.0 if waxing else -1.0
        sweep = int(360.0 * age / calc.SYNODIC)
        if sweep >= 2:
            dc.setColor(self.moon_cols[2], -1)
            dc.setPenWidth(self.pen(L.GAUGE_PEN))
            dc.drawArc(x, y, p(L.GAUGE_R), CLOCKWISE, 90, (90 - sweep) % 360)
            dc.setPenWidth(1)
        cy, mr = y + p(L.MOON_DY), p(L.MOON_R)
        dc.setColor(self.moon_cols[1], -1); dc.fillCircle(x, cy, mr)
        dc.setColor(self.moon_cols[0], -1)
        e = 1.0 - 2.0 * k
        for dy in range(-mr, mr + 1):
            h = math.sqrt(mr * mr - dy * dy)
            a0, a1 = sorted((s * h, s * e * h))
            x0, x1 = int(math.floor(a0 + 0.5)), int(math.floor(a1 + 0.5))
            if x1 > x0:
                dc.drawLine(x + x0, cy + dy, x + x1, cy + dy)
        dc.setColor(self.text, -1)
        dc.drawText(x, y + p(L.MOON_LABEL_DY), self.f_xs, "%d%%" % int(math.floor(k * 100 + 0.5)), CENTER | VCENTER)

    # ---- digital e-paper face of Connect IQ 3 watches (mirror of drawDigital)
    def digital_dark(self, now, watch_offset):
        s = self.s
        t = s.get("digital_theme", 0)
        if t:
            return t == 2
        local = now + watch_offset
        m = (local % 86400) // 60
        if s["lat"] == 0 and s["lon"] == 0:
            return m < 7 * 60 or m >= 19 * 60
        offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
        day = calc.local_epoch_day(now, offset)
        t = self.day_times(day, offset / 3600.0)
        rise, sset = calc.to_minutes(t[calc.SUNRISE]), calc.to_minutes(t[calc.SUNSET])
        if rise is None or sset is None:
            return m < 7 * 60 or m >= 19 * 60
        return m < rise or m >= sset

    def render_digital(self, now, watch_offset, sensors, awake=True, mip=True):
        size, p, s = self.size, self.p, self.s
        f_t, f_m, f_s = font("dg_time", size), font("dg_m", size), font("dg_s", size)
        dc = Dc(size, size)
        dark = self.digital_dark(now, watch_offset)
        paper, ink = (0x000000, 0xFFFFFF) if dark else (0xFFFFFF, 0x000000)
        dc.setColor(paper, paper); dc.clear()
        band_path = os.path.join(font_dir(size), "..", "drawables", "band_%s.png" % ("dark" if dark else "light"))
        if os.path.exists(band_path):
            b = Image.open(band_path).convert("RGBA")
            big = b.resize((b.width * S, b.height * S), Image.NEAREST)
            dc.img.paste(big, (0, p(L.DG_BAND_Y0) * S), big)
        cx = size // 2
        local = now + watch_offset
        hour, minute, sec = (local % 86400) // 3600, (local % 3600) // 60, local % 60
        is24 = s.get("is24", True)
        hh = hour if is24 else (hour % 12 or 12)
        time = ("%02d" % hh if is24 else str(hh)) + ":%02d" % minute
        dc.setColor(ink, -1); dc.setPenWidth(1)
        dc.drawCircle(cx, cx, p(L.DG_RIM_R))
        for i in range(12):
            x, y = self.polar(L.DG_DOT_R, i * math.pi / 6)
            dc.fillCircle(x, y, self.pen(2.6) if i % 3 == 0 else self.pen(1.6))
        ty, o = p(L.DG_TIME_Y), self.pen(L.DG_HALO)
        dc.setColor(paper, -1)
        for dx in (-o, 0, o):
            for dy in (-o, 0, o):
                if dx or dy:
                    dc.drawText(cx + dx, ty + dy, f_t, time, CENTER | VCENTER)
        dc.setColor(ink, -1)
        dc.drawText(cx, ty, f_t, time, CENTER | VCENTER)
        k, waxing, age = calc.moon_phase(now)
        sg = 1.0 if waxing else -1.0
        my, mr = p(L.DG_MOON_Y), p(L.DG_MOON_R)
        e = 1.0 - 2.0 * k
        for dy in range(-mr, mr + 1):
            h = math.sqrt(mr * mr - dy * dy)
            a0, a1 = sorted((sg * h, sg * e * h))
            x0, x1 = int(math.floor(a0 + 0.5)), int(math.floor(a1 + 0.5))
            if x1 > x0:
                dc.drawLine(cx + x0, my + dy, cx + x1, my + dy)
        dc.drawCircle(cx, my, mr)
        day = local // 86400
        y_, m_, d_ = calc.civil_from_days(day)
        dc.drawText(cx, p(L.DG_DATE_Y), f_m, "%s %d %s" % (self.str["Day%d" % calc.day_of_week(day)], d_,
                                                          self.str["Month%d" % m_]), CENTER | VCENTER)
        hy, hm, hd = calc.hijri_for_epoch_day(day, s["hijri_corr"])
        if s.get("hijri_arabic", True):
            ar = (lambda n: str(n)) if s.get("hijri_digits", 0) == 1 else \
                (lambda n: "".join(chr(ord(ch) - 48 + 97) for ch in str(n)))
            dc.drawText(cx, p(L.DG_HIJRI_Y), self.f_ar, "M %s %s %s" % (ar(hy), chr(ord("A") + hm - 1), ar(hd)), CENTER | VCENTER)
        else:
            dc.drawText(cx, p(L.DG_HIJRI_Y), f_s, "%d %s %d %s" % (hd, self.str["Hijri%d" % hm], hy, self.str["HijriSuffix"]),
                        CENTER | VCENTER)
        if awake:
            by = p(L.DG_SEC_Y)
            dc.fillRectangle(p(L.DG_SEC_X0), by - self.pen(2), p(L.DG_SEC_W) * sec // 59, self.pen(4))
            dc.fillRectangle(p(L.DG_SEC_X0 + L.DG_SEC_W), by - self.pen(2), 1, self.pen(4))
        # next prayer
        y = p(L.DG_PRAYER_Y)
        if s["lat"] == 0 and s["lon"] == 0:
            dc.drawText(cx, y, f_s, self.str["SetLocation"] + " " + self.str["SetLocation2"], CENTER | VCENTER)
        else:
            offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
            pday = calc.local_epoch_day(now, offset)
            days = [self.day_times(pday + i, offset / 3600.0) for i in range(3)]
            nxt = None
            for dd in range(3):
                for pr in calc.PRAYERS:
                    mo = calc.moment(pday + dd, days[dd][pr], offset / 3600.0)
                    if mo is not None and mo > now:
                        nxt = (pr, mo, dd)
                        break
                if nxt:
                    break
            if nxt:
                jum = nxt[0] == calc.DHUHR and self.is_jumuah(pday + nxt[2])
                if s.get("prayer_names", 0) == 0:
                    kk = 5 if jum else [0, -1, 1, 2, -1, 3, 4][nxt[0]]
                    dc.drawText(cx + p(L.DG_NAME_DX), y, self.f_ar, chr(ord("N") + kk), CENTER | VCENTER)
                else:
                    dc.drawText(cx + p(L.DG_NAME_DX), y, f_s, self.str["Prayer7" if jum else PRAYER_NAMES[nxt[0]]], CENTER | VCENTER)
                dc.drawText(cx + p(L.DG_PTIME_DX), y, f_m, format_time(calc.to_minutes(days[nxt[2]][nxt[0]]), is24),
                            CENTER | VCENTER)
                pw, ph = p(L.DG_PILL_W), p(L.DG_PILL_H)
                dc.fillRoundedRectangle(cx + p(L.DG_PILL_DX) - pw // 2, y - ph // 2, pw, ph, self.pen(4))
                dc.setColor(paper, -1)
                dc.drawText(cx + p(L.DG_PILL_DX), y, f_m, calc.countdown_text(nxt[1] - now), CENTER | VCENTER)
                dc.setColor(ink, -1)
        # status row
        y, ly = p(L.DG_STATUS_Y), p(L.DG_LABEL_Y)
        sx, r = cx - p(L.DG_STATUS_DX), p(L.DG_RING_R)
        st = sensors.get(0, {})
        pr = min(1.0, st["value"] / float(st["goal"])) if st.get("goal") else 0.0
        sweep = int(360.0 * pr)
        dc.setPenWidth(self.pen(3))
        if sweep >= 2:
            dc.drawArc(sx, y, r, CLOCKWISE, 90, (90 - sweep) % 360)
        dc.setPenWidth(self.pen(1))
        for a in range(0, 360, 20):
            if a > sweep:
                s0 = 90 - a
                dc.drawArc(sx, y, r, CLOCKWISE, (s0 + 360) % 360, (s0 - 6 + 360) % 360)
        dc.setPenWidth(1)
        dc.drawText(sx, y, f_s, str(int(pr * 100)), CENTER | VCENTER)
        dc.drawText(sx, ly, f_s, str(st.get("value", "--")), CENTER | VCENTER)
        hr = sensors.get(1, {}).get("value")
        dc.drawText(cx, y, f_m, str(hr) if hr is not None else "--", CENTER | VCENTER)
        dc.drawText(cx, ly, f_s, self.str["LabelHeart"], CENTER | VCENTER)
        batt = sensors.get(3, {}).get("battery", 0.0)
        bx, by, bw, bh = cx + p(L.DG_STATUS_DX) - p(14), y - p(6), p(28), p(12)
        dc.fillRectangle(bx, by, bw, 1); dc.fillRectangle(bx, by + bh - 1, bw, 1)
        dc.fillRectangle(bx, by, 1, bh); dc.fillRectangle(bx + bw - 1, by, 1, bh)
        dc.fillRectangle(bx + bw, by + bh // 2 - p(2), self.pen(3), p(5))
        dc.fillRectangle(bx + self.pen(2), by + self.pen(2), int((bw - 2 * self.pen(2)) * batt / 100.0), bh - 2 * self.pen(2))
        dc.drawText(cx + p(L.DG_STATUS_DX), ly, f_s, "%d%%" % int(round(batt)), CENTER | VCENTER)
        img = dc.bitmap()
        return to_mip(img) if mip else img

    def battery_line(self, dc, sensors):
        """Mirror of drawBatteryLine."""
        p, c = self.p, self.c
        value, progress, warn = read_source(3, sensors)
        pct = progress * 100.0
        txt = value + "%"
        fill_col = c[T["WARN"]] if warn else (0x55FF55 if pct > 30 else 0xFFAA00)
        w = self.f_s.width(txt)
        x0 = p(140) - (w + p(20)) // 2
        y = p(L.BATT_Y)
        dc.setColor(c[T["WARN"]] if warn else self.text, -1)
        dc.setPenWidth(1)
        dc.drawRoundedRectangle(x0, y - p(4), p(14), p(9), 2)
        dc.fillRectangle(x0 + p(14), y - p(2), p(2), p(5))
        fill = int(p(10) * pct / 100.0)
        if fill > 0:
            dc.setColor(fill_col, -1)
            dc.fillRectangle(x0 + p(2), y - p(2), fill, p(5))
        dc.setColor(c[T["WARN"]] if warn else self.text, -1)
        dc.drawText(x0 + p(20) + w // 2, y, self.f_s, txt, CENTER | VCENTER)

    def sun_icon(self, dc, x, y, rising):
        p = self.p
        if self.hd is not None:
            return
        dc.setColor(self.c[T["GOLD"]], -1)
        dc.setPenWidth(self.pen(2)); dc.drawArc(x, y + p(2), p(5), COUNTER_CLOCKWISE, 0, 180)
        dc.setPenWidth(self.pen(1))
        dc.drawLine(x - p(8), y + p(2), x + p(8), y + p(2))
        for ang in (30, 90, 150):
            a = math.radians(ang)
            dc.drawLine(x + int(round(p(7) * math.cos(a))), y + p(2) - int(round(p(7) * math.sin(a))),
                        x + int(round(p(9) * math.cos(a))), y + p(2) - int(round(p(9) * math.sin(a))))
        dc.setPenWidth(1)
        if rising:
            dc.fillPolygon([(x, y + p(3)), (x - p(2), y + p(6)), (x + p(2), y + p(6))])
        else:
            dc.fillPolygon([(x, y + p(7)), (x - p(2), y + p(4)), (x + p(2), y + p(4))])

    def panel_icon(self, dc, x, y, kind):
        p = self.p
        if self.hd is not None:
            return
        dc.setColor(self.c[T["GOLD"]], -1)
        if kind == 0:   # small mosque: dome + base + finial
            dc.fillCircle(x, y, p(4)); dc.fillRectangle(x - p(5), y, p(10) + 1, p(6))
            dc.fillRectangle(x, y - p(7), 1, p(3))
        else:           # crescent and star
            dc.fillCircle(x, y, p(5))
            dc.setColor(self.c[T["PLATE"]], -1); dc.fillCircle(x + p(2), y - p(2), p(4))
            dc.setColor(self.c[T["GOLD"]], -1); dc.fillCircle(x + p(4), y + p(2), 1)

    def draw_panel(self, dc, cx, kind, prayer, value, value_color, jum=False):
        p = self.p
        x0 = cx - p(L.PANEL_W) // 2
        self.panel_icon(dc, x0 + p(11), p(L.PANEL_Y0 + L.PANEL_H // 2), kind)
        tx = x0 + p(20) + (p(L.PANEL_W) - p(22)) // 2
        dc.setColor(self.text, -1)
        if self.s.get("prayer_names", 0) == 0:   # ArSmall "N".."R"
            k = 5 if jum else [0, -1, 1, 2, -1, 3, 4][prayer]
            dc.drawText(tx, p(L.PANEL_Y0 + 8), self.f_ar, chr(ord("N") + k), CENTER | VCENTER)
        else:
            dc.drawText(tx, p(L.PANEL_Y0 + 8), self.f_xs, self.str["Prayer7" if jum else PRAYER_NAMES[prayer]], CENTER | VCENTER)
        dc.setColor(value_color, -1)
        dc.drawText(tx, p(L.PANEL_Y0 + 20), self.f_s, value, CENTER | VCENTER)

    def draw_prayers(self, dc, now, watch_offset):
        c, s, p = self.c, self.s, self.p
        is24 = s.get("is24", True)
        if s["lat"] == 0 and s["lon"] == 0:
            dc.setColor(c[T["DIM"]], -1)
            dc.drawText(p(140 - L.PANEL_DX), p(L.PANEL_Y0 + 8), self.f_xs, self.str["SetLocation"], CENTER | VCENTER)
            dc.drawText(p(140 - L.PANEL_DX), p(L.PANEL_Y0 + 20), self.f_xs, self.str["SetLocation2"], CENTER | VCENTER)
            return None
        offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
        tz = offset / 3600.0
        day = calc.local_epoch_day(now, offset)
        days = [self.day_times(day + k, tz) for k in range(3)]
        found = []
        for dd in range(3):
            for pr in calc.PRAYERS:
                mo = calc.moment(day + dd, days[dd][pr], tz)
                if mo is not None and mo > now:
                    found.append((pr, mo, dd))
                    if len(found) == 2:
                        break
            if len(found) == 2:
                break
        if found:
            nxt = found[0]
            self.draw_panel(dc, p(140 - L.PANEL_DX), 0, nxt[0],
                            calc.countdown_text(nxt[1] - now), self.accent,
                            nxt[0] == calc.DHUHR and self.is_jumuah(day + nxt[2]))
        if len(found) > 1:
            fol = found[1]
            self.draw_panel(dc, p(140 + L.PANEL_DX), 1, fol[0],
                            format_time(calc.to_minutes(days[fol[2]][fol[0]]), is24), self.text,
                            fol[0] == calc.DHUHR and self.is_jumuah(day + fol[2]))
        for sgn, idx in ((-1, 1), (1, 4)):
            x = p(140 + sgn * L.SUN_DX)
            self.sun_icon(dc, x, p(L.SUN_ICON_Y), sgn < 0)
            dc.setColor(self.text, -1)
            dc.drawText(x, p(L.SUN_TIME_Y), self.f_s, format_time(calc.to_minutes(days[0][idx]), is24), CENTER | VCENTER)
        return found[0] if found else None

    def hand_outline(self, ln, w, tail, g):
        style = self.s.get("hand_style", 0)
        if style == 1:
            return [(0, tail + g), (-w - 1.5 - g, -ln * 0.18), (0, -ln - g), (w + 1.5 + g, -ln * 0.18)]
        if style == 2:
            return [(-w * 0.6 - g, tail + g), (w * 0.6 + g, tail + g), (w + 0.8 + g, -ln * 0.62), (0, -ln - 2 - g),
                    (-w - 0.8 - g, -ln * 0.62)]
        return [(-w - g, tail + g), (w + g, tail + g), (w - 0.5 + g, -ln - g), (0, -ln - 4 - g), (-w + 0.5 - g, -ln - g)]

    def hand(self, dc, a, ln, w, tail):
        c = self.c
        off = self.pen(2)
        dc.setColor(0, -1)
        dc.fillPolygon([(x + off, y + off) for x, y in self.rotate_poly(self.hand_outline(ln, w, tail, 1), a)])
        dc.setColor(c[T["PLATE"]], -1); dc.fillPolygon(self.rotate_poly(self.hand_outline(ln, w, tail, 1), a))
        dc.setColor(self.hand_light, -1); dc.fillPolygon(self.rotate_poly(self.hand_outline(ln, w, tail, 0), a))
        style = self.s.get("hand_style", 0)
        if style == 1:
            dc.setColor(self.hand_dark, -1)
            dc.fillPolygon(self.rotate_poly([(0, tail), (0, -ln), (w + 1.5, -ln * 0.18)], a))
        elif style == 2:
            dc.setColor(self.hand_dark, -1)
            dc.fillPolygon(self.rotate_poly([(0, tail), (w * 0.6, tail), (w + 0.8, -ln * 0.62), (0, -ln - 2)], a))
            dc.setColor(0xFFFFFF, -1)
            dc.fillPolygon(self.rotate_poly([(-1.2, -12), (1.2, -12), (1.2, -ln * 0.6), (-1.2, -ln * 0.6)], a))
        else:
            dc.setColor(0xFFFFFF, -1)
            dc.fillPolygon(self.rotate_poly([(-w + 1.5, -14), (w - 1.5, -14), (w - 1.5, -ln + 3), (-w + 1.5, -ln + 3)], a))

    def seconds_hand(self, dc, sec):
        c, p = self.c, self.p
        a = sec * math.pi / 30
        tip, tail = self.polar(L.SEC_LEN, a), self.polar(-L.SEC_TAIL, a)
        weight = self.polar(-(L.SEC_TAIL - L.SEC_WEIGHT_R - 2), a)
        dc.setColor(self.sec, -1)
        dc.setPenWidth(self.pen(L.SEC_PEN)); dc.drawLine(tail[0], tail[1], tip[0], tip[1])
        dc.setPenWidth(self.pen(2)); dc.drawCircle(weight[0], weight[1], p(L.SEC_WEIGHT_R)); dc.setPenWidth(1)
        cx = self.size // 2
        dc.setColor(self.hand_light, -1); dc.fillCircle(cx, cx, p(L.CAP_R))
        dc.setColor(self.sec, -1); dc.fillCircle(cx, cx, p(L.CAP_INNER_R))
        dc.setColor(c[T["PLATE"]], -1); dc.fillCircle(cx, cx, max(1, p(1.5)))

    def render(self, now, watch_offset, sensors, show_seconds=True, mip=True):
        dc = Dc(self.size, self.size)
        fri = self.friday_now(now, watch_offset)
        if fri != self.friday:
            self.apply(fri)
        c, s, p = self.c, self.s, self.p
        self.draw_static(dc)
        local = now + watch_offset
        day = local // 86400
        hour, minute, sec = (local % 86400) // 3600, (local % 3600) // 60, local % 60
        # date block
        y, m, d = calc.civil_from_days(day)
        dc.setColor(self.text, -1)
        dc.drawText(p(140), p(L.DAY_NAME_Y), self.f_dxs, self.str["Day%d" % calc.day_of_week(day)], CENTER | VCENTER)
        dc.drawText(p(140), p(L.DAY_NUM_Y), self.f_dl, str(d), CENTER | VCENTER)
        dc.drawText(p(140), p(L.MONTH_Y), self.f_dxs, self.str["Month%d" % m], CENTER | VCENTER)
        hy, hm, hd = calc.hijri_for_epoch_day(day, s["hijri_corr"])
        dc.setColor(c[T["GOLD"]], -1)
        dc.setColor(self.text, -1)
        if s.get("hijri_arabic", True):
            ar = (lambda n: str(n)) if s.get("hijri_digits", 0) == 1 else \
                (lambda n: "".join(chr(ord(ch) - 48 + 97) for ch in str(n)))   # mirror of arDigits
            # two lines (mirror of drawLive): "day month", then "year AH"
            dc.drawText(p(140), p(L.HIJRI_Y), self.f_ar, "%s %s" % (chr(ord("A") + hm - 1), ar(hd)), CENTER | VCENTER)
            dc.drawText(p(140), p(L.HIJRI_Y2), self.f_ar, "M %s" % ar(hy), CENTER | VCENTER)
        else:
            dc.drawText(p(140), p(L.HIJRI_Y), self.f_s, "%d %s" % (hd, self.str["Hijri%d" % hm]), CENTER | VCENTER)
            dc.drawText(p(140), p(L.HIJRI_Y2), self.f_s, "%d %s" % (hy, self.str["HijriSuffix"]), CENTER | VCENTER)
        nxt = self.draw_prayers(dc, now, watch_offset)
        g = s["gauges"]
        for (x, yy), src in zip(self.gauge_centres(), g):
            if src == SUN_RING:
                self.sun_ring(dc, x, yy, now, watch_offset)
            elif src == MOON:
                self.moon(dc, x, yy, now)
            else:
                self.draw_gauge(dc, x, yy, src, sensors)
        # Ayah (mirror of drawAyah), then the battery line when no gauge shows the battery
        idx = ayah_pick(s.get("ayah_mode", 0), s.get("ayah_fixed", 18), s.get("ayah_included", [True] * 39),
                        local // 3600)
        self.ayah_index = -2 if self.friday else idx
        if self.friday:
            # the Friday greeting (not a verse): slot 7 of the Ayah4 font, in the text colour
            dc.setColor(self.text, -1)
            dc.drawText(p(140), p(L.AYAH_Y), font("ayah4", self.size), "".join(chr(ord("A") + 28 + j) for j in range(4)),
                        CENTER | VCENTER)
        elif idx >= 0:
            fa = font("ayah%d" % (idx // 8), self.size)
            dc.setColor(c[T["GOLD"]], -1)
            dc.drawText(p(140), p(L.AYAH_Y), fa, "".join(chr(ord("A") + 4 * (idx % 8) + j) for j in range(4)),
                        CENTER | VCENTER)
        if 3 not in g:
            self.battery_line(dc, sensors)
        # hands
        self.hand(dc, ((hour % 12) + minute / 60.0) * math.pi / 6, L.HOUR_LEN, L.HOUR_W, L.HOUR_TAIL)
        self.hand(dc, minute * math.pi / 30, L.MIN_LEN, L.MIN_W, L.MIN_TAIL)
        cx = self.size // 2
        dc.setColor(self.hand_light, -1); dc.fillCircle(cx, cx, p(L.CAP_R))
        dc.setColor(self.hand_dark, -1); dc.fillCircle(cx, cx, p(L.CAP_INNER_R))
        if show_seconds and s.get("seconds_mode", 0) != 2:
            self.seconds_hand(dc, sec)
        img = dc.bitmap()
        return (to_mip(img) if mip else img), {"next": nxt, "hijri": (hy, hm, hd), "time": (hour, minute, sec)}

    def render_aod(self, now, watch_offset):
        """AMOLED always-on (burn-in protection) frame: mirror of drawAlwaysOn()."""
        dc = Dc(self.size, self.size)
        c, p = self.c, self.p
        dc.setColor(0, 0); dc.clear()
        local = now + watch_offset
        hour, minute = (local % 86400) // 3600, (local % 3600) // 60
        shift = (minute % 5) - 2
        cx = self.size // 2 + shift
        cy = self.size // 2 + shift
        dc.setColor(c[T["DIM"]], -1)
        for h in range(0, 12, 3):
            x, y = self.polar(L.NUM_R + 6, h * math.pi / 6)
            dc.fillCircle(x + shift, y + shift, max(1, p(2)))
        dc.setPenWidth(self.pen(2))
        for a, ln in ((((hour % 12) + minute / 60.0) * math.pi / 6, L.HOUR_LEN), (minute * math.pi / 30, L.MIN_LEN)):
            tip = self.polar(ln, a)
            dc.setColor(c[T["GOLD"]], -1)
            dc.drawLine(cx, cy, tip[0] + shift, tip[1] + shift)
        dc.setPenWidth(1)
        dc.setColor(c[T["GOLD"]], -1); dc.drawCircle(cx, cy, p(4))
        img = dc.bitmap()
        lit = sum(1 for px in img.getdata() if max(px) > 16) / float(self.size * self.size)
        return img, {"lit_fraction": lit}


DEFAULT_SETTINGS = dict(preset=0, background=0, gauges=[0, 1, MOON, SUN_RING], hijri_corr=0, ayah_mode=1, ayah_fixed=18, method=0, asr=1,
                        highlat=1, lat=33.8754, lon=10.8575, tz_manual=False, utc_offset=3600, is24=True)

# Simulated sensor values for previews (clearly NOT live data)
DEFAULT_SENSORS = {
    0: {"value": 7385, "goal": 10000},
    1: {"value": 72},
    2: {"value": 1450},
    3: {"battery": 76.0},
    4: {"value": 642000},
    5: {"value": 7, "goal": 10},
    6: {"value": 72},
    7: {"value": 24},
}
