"""Reference renderer: a Python mirror of source/LuxeHijriPrayerView.mc.

It reads the real layout constants (source/Layout.mc), presets (source/Themes.mc), strings
(resources*/strings/strings.xml), background geometry (resources/jsonData/*.json) and the
generated bitmap fonts (resources/fonts/*.fnt/png), and draws a 280 x 280 frame with the
same primitives and order as the Monkey C code. Shapes are rasterised with 4x supersampling
(approximating the device anti-aliasing) and the frame is reduced to the 64-colour palette
of the fenix 7X Pro MIP display.

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


def _consts(path):
    src = open(os.path.join(ROOT, path)).read()
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", src)}


L = type("Layout", (), _consts("source/Layout.mc"))
T = _consts("source/Themes.mc")


def presets():
    src = open(os.path.join(ROOT, "source", "Themes.mc")).read()
    body = src[src.index("PRESETS"):]
    rows = re.findall(r"\[([^\[\]]+)\]", body)
    return [[int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{6}", r)] for r in rows]


PRESETS = presets()
PRESET_NAMES = ["Luxury Blue", "Royal Gold", "Emerald Night", "Burgundy Royale", "Ice Silver", "Stealth"]
BACKGROUNDS = ["bg_mosque", "bg_geometric", "bg_marble", "bg_night"]


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
    def __init__(self, name):
        path = os.path.join(ROOT, "resources", "fonts", name + ".fnt")
        self.chars = {}
        for line in open(path):
            kv = dict(re.findall(r"(\w+)=(\"[^\"]*\"|\S+)", line))
            if line.startswith("common"):
                self.height = int(kv["lineHeight"])
            elif line.startswith("char "):
                self.chars[int(kv["id"])] = {k: int(v) for k, v in kv.items() if k != "page"}
        self.atlas = Image.open(os.path.join(ROOT, "resources", "fonts", name + ".png")).getchannel("A")

    def width(self, text):
        return sum(self.chars.get(ord(ch), self.chars[32])["xadvance"] for ch in text)


FONTS = {}


def font(name):
    if name not in FONTS:
        FONTS[name] = BmFont(name)
    return FONTS[name]


# ------------------------------------------------------------------ Dc emulation
LEFT, CENTER, RIGHT, VCENTER = 2, 1, 0, 4
CLOCKWISE, COUNTER_CLOCKWISE = 1, 0


class Dc:
    def __init__(self, w=280, h=280):
        self.w, self.h = w, h
        self.img = Image.new("RGB", (w * S, h * S))
        self.d = ImageDraw.Draw(self.img)
        self.fg = (255, 255, 255)
        self.pen = 1
        self.text_ops = []

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
        if self.pen > 1:  # round caps
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
    """Nearest of the 64 MIP colours per pixel (no dithering)."""
    lut = [min(MIP_LEVELS, key=lambda l: abs(l - v)) for v in range(256)]
    return img.point(lut * 3)


def circular(img, outside=(18, 18, 18)):
    mask = Image.new("L", (img.width * 4, img.height * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, img.width * 4 - 1, img.height * 4 - 1], fill=255)
    mask = mask.resize(img.size, Image.LANCZOS)
    out = Image.new("RGB", img.size, outside)
    out.paste(img, (0, 0), mask)
    return out


# ------------------------------------------------------------------ face (mirror of the view)
def polar(r, a, side=0):
    return [int(round(L.CX + r * math.sin(a) + side * math.cos(a))),
            int(round(L.CY - r * math.cos(a) + side * math.sin(a)))]


def rotate_poly(pts, a):
    sn, cs = math.sin(a), math.cos(a)
    return [(int(round(L.CX + x * cs - y * sn)), int(round(L.CY + x * sn + y * cs))) for x, y in pts]


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


class Face:
    def __init__(self, settings, lang="eng"):
        self.s = settings
        self.c = PRESETS[settings["preset"]]
        self.str = strings(lang)
        self.bg_ops = json.load(open(os.path.join(ROOT, "resources", "jsonData",
                                                  BACKGROUNDS[settings["background"]] + ".json")))
        self.f_xs, self.f_s, self.f_m = font("luxe_xs"), font("luxe_s"), font("luxe_m")
        self.f_l, self.f_ayah = font("luxe_l"), font("ayah")

    # ---- background interpreter (mirror of Backgrounds.draw)
    def draw_background(self, dc):
        c = self.c
        for op in self.bg_ops:
            code = op[0]
            dc.setColor(c[op[1]], -1)
            if code == 0:
                dc.fillPolygon([(op[k], op[k + 1]) for k in range(2, len(op) - 1, 2)])
            elif code == 1:
                dc.fillCircle(op[2], op[3], op[4])
            elif code == 2:
                dc.setPenWidth(op[2]); dc.drawLine(op[3], op[4], op[5], op[6])
            elif code == 3:
                dc.setPenWidth(op[2])
                for k in range(3, len(op) - 3, 2):
                    dc.drawLine(op[k], op[k + 1], op[k + 2], op[k + 3])
            elif code == 4:
                size = op[2]
                for k in range(3, len(op) - 1, 2):
                    if size <= 1:
                        dc.drawPoint(op[k], op[k + 1])
                    else:
                        dc.fillRectangle(op[k], op[k + 1], size, size)
            elif code == 5:
                dc.setPenWidth(op[2]); dc.drawCircle(op[3], op[4], op[5])
            elif code == 6:
                dc.fillRectangle(op[2], op[3], op[4], op[5])
            elif code == 7:
                dc.setPenWidth(op[2])
                x, y, r = op[3], op[4], op[5]
                d = int(r * 0.7071 + 0.5)
                for (a, b, e, f) in [(x, y - r, x + r, y), (x + r, y, x, y + r), (x, y + r, x - r, y),
                                     (x - r, y, x, y - r), (x - d, y - d, x + d, y - d), (x + d, y - d, x + d, y + d),
                                     (x + d, y + d, x - d, y + d), (x - d, y + d, x - d, y - d)]:
                    dc.drawLine(a, b, e, f)
            elif code == 8:
                dc.fillRectangle(0, 0, 280, 280)
            elif code == 9:
                dc.fillCircle(op[3], op[4], op[5])
                dc.setColor(c[op[2]], -1)
                dc.fillCircle(op[3] + op[6], op[4] + op[7], op[8])
        dc.setPenWidth(1)

    def draw_chapter_ring(self, dc):
        c = self.c
        dc.setPenWidth(1)
        dc.setColor(c[T["GOLD_DK"]], -1)
        for i in range(60):
            if i % 5:
                a = i * math.pi / 30
                p0, p1 = polar(L.TRACK_R_IN, a), polar(L.TRACK_R_OUT, a)
                dc.drawLine(p0[0], p0[1], p1[0], p1[1])
        dc.drawCircle(L.CX, L.CY, L.TRACK_R_OUT + 1)
        dc.setColor(c[T["GOLD"]], -1)
        for h in range(1, 12):
            a = h * math.pi / 6
            if h in (3, 9):
                dc.fillPolygon(rotate_poly([(-2.5, -L.IDX_CARD_R_IN), (2.5, -L.IDX_CARD_R_IN),
                                            (2.5, -L.IDX_R_OUT), (-2.5, -L.IDX_R_OUT)], a))
            elif h != 6:
                dc.fillPolygon(rotate_poly([(-1.5, -L.IDX_R_IN), (1.5, -L.IDX_R_IN),
                                            (L.IDX_W, -L.IDX_R_OUT), (-L.IDX_W, -L.IDX_R_OUT)], a))
        g = L.IDX_12_GAP
        for sgn in (-1, 1):
            dc.fillPolygon(rotate_poly([(sgn * g - 2, -L.IDX_CARD_R_IN), (sgn * g + 2, -L.IDX_CARD_R_IN),
                                        (sgn * g + 2, -L.IDX_R_OUT), (sgn * g - 2, -L.IDX_R_OUT)], 0.0))
        x, y, r = L.CX, L.STAR6_Y, L.STAR6_R
        d = int(r * 0.7071 + 0.5)
        dc.fillPolygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)])
        dc.fillPolygon([(x - d, y - d), (x + d, y - d), (x + d, y + d), (x - d, y + d)])
        dc.setColor(c[T["BG"]], -1)
        dc.fillCircle(x, y, 2)

    def two_tone(self, dc, x, y, f, a, ca, b, cb):
        wa, wb, sp = f.width(a), f.width(b), f.width(" ")
        x0 = x - (wa + sp + wb) // 2
        dc.setColor(ca, -1); dc.drawText(x0, y, f, a, LEFT | VCENTER)
        dc.setColor(cb, -1); dc.drawText(x0 + wa + sp, y, f, b, LEFT | VCENTER)

    def draw_gauge(self, dc, x, y, src, sensors):
        c = self.c
        r = L.GAUGE_R
        dc.setColor(c[T["PLATE"]], -1); dc.fillCircle(x, y, L.GAUGE_DISC_R)
        dc.setPenWidth(L.GAUGE_PEN)
        dc.setColor(c[T["TRACK"]], -1); dc.drawArc(x, y, r, CLOCKWISE, 225, 315)
        value, progress, flag = read_source(src, sensors)
        if progress is not None:
            p = min(progress, 1.0)
            sweep = int(270.0 * p)
            if sweep >= 2:
                end = 225 - sweep
                if end < 0:
                    end += 360
                warn = src == 3 and flag == 1
                dc.setColor(c[T["WARN"]] if warn else c[T["ACCENT"]], -1)
                dc.drawArc(x, y, r, CLOCKWISE, 225, end)
        dc.setPenWidth(1)
        color = c[T["TEXT"]]
        if value is None:
            value, color = "--", c[T["DIM"]]
        elif flag == 1:
            color = c[T["WARN"]] if src == 3 else c[T["DIM"]]
        f = self.f_l if src == 3 else self.f_m
        inner = 2 * (r - L.GAUGE_PEN // 2) - 2
        if f.width(value) > inner:
            f = self.f_m
            if f.width(value) > inner:
                f = self.f_s
        dc.setColor(color, -1)
        dc.drawText(x, y + L.GAUGE_VALUE_DY, f, value, CENTER | VCENTER)
        dc.setColor(c[T["ACCENT2"]], -1)
        self.draw_gauge_icon(dc, x, y + L.GAUGE_ICON_DY, src)

    def draw_gauge_icon(self, dc, x, y, src):
        unit = {2: self.str["LabelCalories"], 3: self.str["LabelBattery"],
                4: self.str["LabelMi" if self.s.get("statute") else "LabelKm"]}.get(src)
        if unit is not None:
            dc.drawText(x, y, font("luxe_xxs"), unit, CENTER | VCENTER)
            return
        if src == 0:
            dc.fillEllipse(x - 3, y + 1, 2, 4); dc.fillEllipse(x + 3, y - 1, 2, 4)
        elif src == 1:
            dc.fillCircle(x - 2, y - 2, 3); dc.fillCircle(x + 2, y - 2, 3)
            dc.fillPolygon([(x - 5, y - 1), (x + 5, y - 1), (x, y + 5)])
        elif src == 5:
            dc.setPenWidth(2)
            pts = [(x - 6, y + 4), (x - 3, y + 4), (x - 3, y + 1), (x, y + 1), (x, y - 2), (x + 3, y - 2),
                   (x + 3, y - 5), (x + 6, y - 5)]
            for i in range(len(pts) - 1):
                dc.drawLine(*pts[i], *pts[i + 1])
            dc.setPenWidth(1)
        elif src == 6:
            dc.fillPolygon([(x + 2, y - 6), (x - 3, y + 1), (x + 1, y + 1)])
            dc.fillPolygon([(x - 1, y - 1), (x + 3, y - 1), (x - 2, y + 6)])
        elif src == 7:
            dc.setPenWidth(2)
            pts = [(x - 6, y + 1), (x - 3, y - 3), (x, y + 3), (x + 3, y - 3), (x + 6, y + 1)]
            for i in range(len(pts) - 1):
                dc.drawLine(*pts[i], *pts[i + 1])
            dc.setPenWidth(1)

    def draw_sun(self, dc, rising, minutes):
        c = self.c
        text = format_time(minutes, self.s.get("is24", True))
        tw = self.f_xs.width(text)
        gw = L.SUN_ICON_W + 3 + tw
        left = L.CX - L.SUN_GAP // 2 - gw if rising else L.CX + L.SUN_GAP // 2
        y = L.SUN_Y
        ix = left + L.SUN_ICON_W // 2
        dc.setColor(c[T["GOLD"]], -1)
        dc.setPenWidth(2); dc.drawArc(ix, y + 3, 4, COUNTER_CLOCKWISE, 0, 180)
        dc.setPenWidth(1); dc.drawLine(ix - 6, y + 3, ix + 7, y + 3)
        if rising:
            dc.fillPolygon([(ix, y - 7), (ix - 3, y - 3), (ix + 3, y - 3)])
        else:
            dc.fillPolygon([(ix, y - 2), (ix - 3, y - 6), (ix + 3, y - 6)])
        dc.setColor(c[T["TEXT"]], -1)
        dc.drawText(left + L.SUN_ICON_W + 3, y, self.f_xs, text, LEFT | VCENTER)

    def draw_prayers(self, dc, now, watch_offset):
        c, s = self.c, self.s
        if s["lat"] == 0 and s["lon"] == 0:
            dc.setColor(c[T["DIM"]], -1)
            dc.drawText(L.CX, L.NEXT_Y, self.f_m, self.str["SetLocation"], CENTER | VCENTER)
            return
        offset = s["utc_offset"] if s.get("tz_manual") else watch_offset
        tz = offset / 3600.0
        day = calc.local_epoch_day(now, offset)
        days = [calc.compute_day(day + k, s["lat"], s["lon"], tz, s["method"], s["asr"], s["highlat"])
                for k in range(3)]
        nxt = None
        for dd in range(3):
            for p in calc.PRAYERS:
                mo = calc.moment(day + dd, days[dd][p], tz)
                if mo is not None and mo > now:
                    nxt = (p, mo, dd)
                    break
            if nxt:
                break
        next_idx, next_day = (nxt[0], nxt[2]) if nxt else (-1, 0)
        cell = L.SCHED_W // 5
        x0 = L.CX - L.SCHED_W // 2 + cell // 2
        for k, p in enumerate(calc.PRAYERS):
            m = calc.to_minutes(days[next_day][p])
            color = c[T["TEXT"]]
            if p == next_idx:
                color = c[T["ACCENT2"]]
            elif nxt is None or (next_day == 0 and p < next_idx):
                color = c[T["DIM"]]
            x = x0 + k * cell
            dc.setColor(color, -1)
            dc.drawText(x, L.SCHED_Y, self.f_xs, format_time(m, s.get("is24", True)), CENTER | VCENTER)
            if p == next_idx:
                dc.fillRectangle(x - 8, L.SCHED_Y + 8, 16, 2)
        names = {0: "Prayer0", 2: "Prayer2", 3: "Prayer3", 5: "Prayer5", 6: "Prayer6"}
        if nxt:
            self.two_tone(dc, L.CX, L.NEXT_Y, self.f_m, self.str[names[next_idx]], c[T["ACCENT2"]],
                          calc.countdown_text(nxt[1] - now), c[T["ACCENT"]])
        else:
            dc.setColor(c[T["DIM"]], -1)
            dc.drawText(L.CX, L.NEXT_Y, self.f_m, "--", CENTER | VCENTER)
        self.draw_sun(dc, True, calc.to_minutes(days[0][1]))
        self.draw_sun(dc, False, calc.to_minutes(days[0][4]))
        return nxt

    def dauphine(self, dc, a, ln, tail, w):
        c = self.c
        dc.setColor(c[T["GOLD"]], -1); dc.fillPolygon(rotate_poly([(0, -ln), (-w, 0), (0, tail)], a))
        dc.setColor(c[T["GOLD_DK"]], -1); dc.fillPolygon(rotate_poly([(0, -ln), (w, 0), (0, tail)], a))

    def seconds_hand(self, dc, sec):
        c = self.c
        a = sec * math.pi / 30
        tip, tail = polar(L.SEC_LEN, a), polar(-L.SEC_TAIL, a)
        weight = polar(-(L.SEC_TAIL - L.SEC_WEIGHT_R - 2), a)
        dc.setColor(c[T["SECONDS"]], -1)
        dc.setPenWidth(L.SEC_PEN); dc.drawLine(tail[0], tail[1], tip[0], tip[1]); dc.setPenWidth(1)
        dc.fillCircle(weight[0], weight[1], L.SEC_WEIGHT_R)
        dc.fillCircle(L.CX, L.CY, L.CAP_R - 1)
        dc.setColor(c[T["PLATE"]], -1); dc.fillCircle(L.CX, L.CY, L.CAP_INNER_R)

    def render(self, now, watch_offset, sensors, show_seconds=True):
        """Returns (280x280 MIP-quantised image, info dict)."""
        dc = Dc()
        c, s = self.c, self.s
        dc.setColor(c[T["BG"]], c[T["BG"]]); dc.clear()
        self.draw_background(dc)
        self.draw_chapter_ring(dc)
        local = now + watch_offset
        day = local // 86400
        hour, minute, sec = (local % 86400) // 3600, (local % 3600) // 60, local % 60
        if s["ayah"] != 7:
            code = str(s["ayah"] + 1)
            if s["ayah"] == 5 and minute % 2 == 1:
                code = "8"
            dc.setColor(c[T["GOLD"]], -1)
            dc.drawText(L.CX, L.AYAH_Y, self.f_ayah, code, CENTER | VCENTER)
        y, m, d = calc.civil_from_days(day)
        months = [self.str["Month%d" % i] for i in range(1, 13)]
        self.two_tone(dc, L.CX, L.GREG_Y, self.f_s, self.str["Day%d" % calc.day_of_week(day)], c[T["ACCENT"]],
                      "%d %s %d" % (d, months[m - 1], y), c[T["TEXT"]])
        hy, hm, hd = calc.hijri_for_epoch_day(day, s["hijri_corr"])
        dc.setColor(c[T["ACCENT2"]], -1)
        dc.drawText(L.CX, L.HIJRI_Y, self.f_s, "%d %s %d %s" % (hd, self.str["Hijri%d" % hm], hy,
                                                                 self.str["HijriSuffix"]), CENTER | VCENTER)
        g = s["gauges"]
        self.draw_gauge(dc, L.CX - L.GAUGE_DX, L.GAUGE_TOP_Y, g[0], sensors)
        self.draw_gauge(dc, L.CX + L.GAUGE_DX, L.GAUGE_TOP_Y, g[1], sensors)
        self.draw_gauge(dc, L.CX - L.GAUGE_DX, L.GAUGE_BOT_Y, g[2], sensors)
        self.draw_gauge(dc, L.CX + L.GAUGE_DX, L.GAUGE_BOT_Y, g[3], sensors)
        nxt = self.draw_prayers(dc, now, watch_offset)
        self.dauphine(dc, ((hour % 12) + minute / 60.0) * math.pi / 6, L.HOUR_LEN, L.HOUR_TAIL, L.HOUR_W)
        self.dauphine(dc, minute * math.pi / 30, L.MIN_LEN, L.MIN_TAIL, L.MIN_W)
        dc.setColor(c[T["GOLD"]], -1); dc.fillCircle(L.CX, L.CY, L.CAP_R)
        dc.setColor(c[T["GOLD_DK"]], -1); dc.fillCircle(L.CX, L.CY, L.CAP_INNER_R)
        if show_seconds:
            self.seconds_hand(dc, sec)
        return to_mip(dc.bitmap()), {"next": nxt, "hijri": (hy, hm, hd), "time": (hour, minute, sec)}


DEFAULT_SETTINGS = dict(preset=0, background=0, gauges=[0, 1, 2, 3], hijri_corr=0, ayah=0, method=0, asr=1,
                        highlat=1, lat=33.8754, lon=10.8575, tz_manual=False, utc_offset=3600, is24=True)

# Simulated sensor values for previews (clearly NOT live data)
DEFAULT_SENSORS = {
    0: {"value": 8432, "goal": 10000},
    1: {"value": 68},
    2: {"value": 1840},
    3: {"battery": 87.0},
    4: {"value": 642000},
    5: {"value": 7, "goal": 10},
    6: {"value": 72},
    7: {"value": 24},
}
