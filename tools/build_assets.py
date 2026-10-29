#!/usr/bin/env python3
"""Generate the bundled resources of Luxe Hijri Prayer (reproducible, no network needed).

Outputs:
  resources/fonts/*.fnt + *.png     BMFont (AngelCode text format) bitmap fonts
  resources/fonts/ayah.fnt + png    one pre-shaped Arabic glyph per Ayah (HarfBuzz/raqm shaping)
  resources/jsonData/bg_*.json      vector geometry of the four backgrounds (colour roles)
  resources/drawables/launcher_icon.png

Fonts: Barlow Semi Condensed and Amiri, both SIL Open Font License (tools/fonts-src).
Arabic shaping uses Pillow's raqm layout engine (HarfBuzz + FriBiDi); the build fails if it
is unavailable, so a wrongly shaped (disconnected) Ayah can never be produced silently.
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_SRC = os.path.join(ROOT, "tools", "fonts-src")
RES = os.path.join(ROOT, "resources")

LATIN = "".join(chr(c) for c in range(32, 127)) + "ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜàâäçéèêëîïôöùûü·°’«»−"

# id, ttf, pixel size, character set
FONTS = [
    ("luxe_xxs", "BarlowSemiCondensed-Bold.ttf", 12, " KCALMI%"),
    ("luxe_xs", "BarlowSemiCondensed-SemiBold.ttf", 14, LATIN),
    ("luxe_s", "BarlowSemiCondensed-SemiBold.ttf", 17, LATIN),
    ("luxe_m", "BarlowSemiCondensed-Bold.ttf", 21, LATIN),
    ("luxe_l", "BarlowSemiCondensed-Bold.ttf", 28, "0123456789%-+.:kKh "),
]


def layout_consts():
    src = open(os.path.join(ROOT, "source", "Layout.mc")).read()
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", src)}


# ------------------------------------------------------------------ BMFont writer
def pack_and_write(name, glyphs, line_height, base, size, face):
    """glyphs: list of (char id, L-mode coverage image or None, xoffset, yoffset, xadvance)."""
    width = 256
    x = y = row_h = 0
    pad = 1
    placed = []
    for cid, img, xo, yo, adv in glyphs:
        w, h = (img.size if img is not None else (0, 0))
        if w > width:
            width = 1 << (w + 2 * pad - 1).bit_length()
    for cid, img, xo, yo, adv in glyphs:
        w, h = (img.size if img is not None else (0, 0))
        if x + w + pad > width:
            x = 0
            y += row_h + pad
            row_h = 0
        placed.append((cid, img, x, y, w, h, xo, yo, adv))
        x += w + pad
        row_h = max(row_h, h)
    height = 1 << max(5, (y + row_h + 1).bit_length())
    atlas = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    lines = [
        'info face="%s" size=%d bold=0 italic=0 charset="" unicode=1 stretchH=100 smooth=1 aa=1 '
        'padding=0,0,0,0 spacing=1,1 outline=0' % (face, size),
        "common lineHeight=%d base=%d scaleW=%d scaleH=%d pages=1 packed=0 alphaChnl=0 redChnl=4 "
        "greenChnl=4 blueChnl=4" % (line_height, base, width, height),
        'page id=0 file="%s.png"' % name,
        "chars count=%d" % len(placed),
    ]
    for cid, img, px, py, w, h, xo, yo, adv in placed:
        if img is not None:
            white = Image.new("RGBA", img.size, (255, 255, 255, 255))
            white.putalpha(img)
            atlas.paste(white, (px, py))
        lines.append("char id=%-5d x=%-4d y=%-4d width=%-4d height=%-4d xoffset=%-4d yoffset=%-4d "
                     "xadvance=%-4d page=0  chnl=15" % (cid, px, py, w, h, xo, yo, adv))
    lines.append("kernings count=0")
    atlas.save(os.path.join(RES, "fonts", name + ".png"), optimize=True)
    with open(os.path.join(RES, "fonts", name + ".fnt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return width, height


def build_latin_font(name, ttf, size, chars):
    font = ImageFont.truetype(os.path.join(FONT_SRC, ttf), size)
    ascent, descent = font.getmetrics()
    glyphs = []
    for ch in chars:
        adv = int(round(font.getlength(ch)))
        bbox = font.getbbox(ch)
        if ch == " " or bbox[2] <= bbox[0]:
            glyphs.append((ord(ch), None, 0, 0, adv))
            continue
        img = Image.new("L", (bbox[2] - bbox[0], bbox[3] - bbox[1]), 0)
        ImageDraw.Draw(img).text((-bbox[0], -bbox[1]), ch, font=font, fill=255)
        glyphs.append((ord(ch), img, bbox[0], bbox[1], adv))
    w, h = pack_and_write(name, glyphs, ascent + descent, ascent, size, os.path.splitext(ttf)[0])
    return {"id": name, "size": size, "lineHeight": ascent + descent, "atlas": [w, h]}


# ------------------------------------------------------------------ Ayah glyph font
def render_arabic_line(text, size):
    font = ImageFont.truetype(os.path.join(FONT_SRC, "Amiri-Bold.ttf"), size,
                              layout_engine=ImageFont.Layout.RAQM)
    bbox = font.getbbox(text, direction="rtl", language="ar")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("L", (w + 2, h + 2), 0)
    ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), text, font=font, fill=255,
                             direction="rtl", language="ar")
    return img.crop(img.getbbox())


def _stack(top, bottom, w):
    """Places `bottom` under `top` as high as possible while keeping >= 2 px between inks."""
    a = Image.new("L", (w, top.height), 0)
    a.paste(top, ((w - top.width) // 2, 0))
    grown = a.filter(ImageFilter.MaxFilter(3))   # 1 px clearance around every ink pixel
    bx = (w - bottom.width) // 2
    for y in range(0, top.height + 1):
        canvas = Image.new("L", (w, y + bottom.height), 0)
        canvas.paste(bottom, (bx, y))
        overlap = ImageChops.multiply(canvas.crop((0, 0, w, min(top.height, y + bottom.height))).point(
            lambda v: 255 if v > 40 else 0), grown.crop((0, 0, w, min(top.height, y + bottom.height))).point(
            lambda v: 255 if v > 40 else 0))
        if overlap.getbbox() is None:
            out = Image.new("L", (w, max(top.height, y + bottom.height)), 0)
            out.paste(a, (0, 0))
            out = ImageChops.lighter(out, canvas.resize(out.size) if canvas.size != out.size else canvas)
            return out
    raise AssertionError("stacking failed")


def _layouts(lines):
    """Candidate line breaks: the given lines, plus every 2-line split of a single line."""
    yield lines
    if len(lines) == 1:
        words = lines[0].split()
        for k in range(1, len(words)):
            yield [" ".join(words[:k]), " ".join(words[k:])]


def ayah_fits(w, h, L):
    """The Ayah box is centred on AYAH_Y; its top corners must stay inside a 124 px circle
    (clear of the 11 and 1 o'clock indices) and its height inside AYAH_MAX_H."""
    if h > L["AYAH_MAX_H"]:
        return False
    top = L["AYAH_Y"] - (h + 1) // 2
    dy = L["CY"] - top
    return w <= min(L["AYAH_MAX_W"], 2 * math.sqrt(max(0, 124 * 124 - dy * dy)))


def render_ayah(lines, L):
    """Largest font size (then fewest lines) for which the Ayah fits the dial."""
    for size in range(22, 11, -1):
        best = None
        for cand in _layouts(lines):
            imgs = [render_arabic_line(t, size) for t in cand]
            w = max(i.width for i in imgs)
            out = imgs[0] if len(imgs) == 1 else _stack(imgs[0], imgs[1], w)
            if ayah_fits(out.width, out.height, L):
                if best is None or len(cand) < best[2] or (len(cand) == best[2] and out.width < best[0].width):
                    best = (out, size, len(cand), cand)
        if best is not None:
            return best[0], best[1], best[3]
    raise SystemExit("Ayah does not fit: %s" % lines)


def build_ayah_font():
    if not features.check("raqm"):
        raise SystemExit("Pillow was built without raqm: Arabic shaping unavailable")
    L = layout_consts()
    data = json.load(open(os.path.join(ROOT, "tools", "ayat.json")))
    glyphs = []
    sizes = {}
    imgs = []
    for a in data["ayat"]:
        img, size, used = render_ayah(a["lines"], L)
        imgs.append((a, img))
        sizes[a["ref"]] = {"px": size, "w": img.width, "h": img.height, "lines": used}
    line_h = max(i.height for _, i in imgs)
    for a, img in imgs:
        glyphs.append((ord(a["code"]), img, 0, (line_h - img.height) // 2, img.width))
    glyphs.append((32, None, 0, 0, 4))
    pack_and_write("ayah", glyphs, line_h, line_h, line_h, "Amiri-Regular (pre-shaped Ayat)")
    return sizes


# ------------------------------------------------------------------ backgrounds
# Colour roles (see source/Themes.mc)
BG, PLATE, ORN, ORN2, GOLD, GOLD_DK, ACCENT, ACCENT2, TEXT, DIM, TRACK, SECONDS, SIL, STAR = range(14)
# Op codes interpreted by source/Backgrounds.mc and tools/face.py
OP_POLY, OP_CIRCLE, OP_LINE, OP_POLYLINE, OP_POINTS, OP_RING, OP_RECT, OP_STAR8, OP_FILL, OP_CRESCENT = range(10)


def inside(x, y, r=139):
    return (x - 140) ** 2 + (y - 140) ** 2 <= r * r


def bg_mosque():
    ops = []
    # stars in the sky (kept away from the text bands)
    rnd = random.Random(7)
    pts = []
    while len(pts) < 2 * 26:
        x, y = rnd.randint(30, 250), rnd.randint(22, 150)
        if inside(x, y, 128) and not (60 <= y <= 100 and 70 <= x <= 210) and not (36 <= y <= 60 and 76 <= x <= 204):
            pts += [x, y]
    ops.append([OP_POINTS, STAR, 2] + pts)
    ops.append([OP_CRESCENT, GOLD, BG, 218, 78, 11, 5, -3, 9])
    # mosque skyline rising from the bottom of the dial; it also darkens the prayer panel
    s = SIL
    ops.append([OP_CIRCLE, s, 140, 212, 27])                  # main dome
    ops.append([OP_RECT, s, 112, 210, 57, 30])                # drum
    ops.append([OP_POLY, s, 137, 186, 143, 186, 141, 176, 139, 176])  # finial base
    ops.append([OP_LINE, s, 2, 140, 176, 140, 166])          # finial
    ops.append([OP_CRESCENT, GOLD, BG, 140, 162, 4, 2, -1, 3])
    ops.append([OP_CIRCLE, s, 102, 226, 15])                  # side domes
    ops.append([OP_CIRCLE, s, 178, 226, 15])
    for mx in (104, 176):                                     # minarets
        ops.append([OP_RECT, s, mx - 4, 182, 9, 60])
        ops.append([OP_RECT, s, mx - 6, 196, 13, 3])          # balcony
        ops.append([OP_POLY, s, mx - 4, 182, mx + 4, 182, mx, 168])
    ops.append([OP_RECT, s, 20, 232, 240, 50])               # ground
    return ops


def bg_geometric():
    ops = []
    step = 46
    for gy in range(-step, 281 + step, step):
        for gx in range(-step, 281 + step, step):
            ox = (step // 2) if ((gy // step) % 2) else 0
            cx, cy = gx + ox, gy
            if inside(cx, cy, 150):
                ops.append([OP_STAR8, ORN, 1, cx, cy, 15])
                ops.append([OP_RING, ORN, 1, cx, cy, 6])
    ops.append([OP_RING, ORN2, 1, 140, 140, 120])
    return ops


def _vein(rnd, x, y, ang, n, step):
    pts = []
    for _ in range(n):
        pts += [int(round(x)), int(round(y))]
        ang += rnd.uniform(-0.45, 0.45)
        x += step * math.cos(ang)
        y += step * math.sin(ang)
    return pts


def bg_marble():
    rnd = random.Random(1448)
    ops = [[OP_FILL, PLATE]]
    for _ in range(9):   # faint grey veins
        ops.append([OP_POLYLINE, ORN, 1] + _vein(rnd, rnd.uniform(-20, 300), rnd.uniform(-20, 300),
                                                  rnd.uniform(0, 6.28), 22, 14))
    for _ in range(4):   # gold veins with branches
        x, y = rnd.uniform(0, 80), rnd.uniform(20, 260)
        main = _vein(rnd, x, y, rnd.uniform(-0.6, 0.6), 26, 12)
        ops.append([OP_POLYLINE, GOLD_DK, 1] + main)
        for b in range(2):
            i = rnd.randrange(4, 20) * 2
            ops.append([OP_POLYLINE, GOLD_DK, 1] + _vein(rnd, main[i], main[i + 1], rnd.uniform(0, 6.28), 6, 9))
    return ops


def bg_night():
    rnd = random.Random(29)
    ops = []
    faint, bright = [], []
    # milky way band (dense faint dots along a diagonal)
    for _ in range(140):
        t = rnd.uniform(0, 1)
        x = 10 + 260 * t + rnd.gauss(0, 14)
        y = 250 - 220 * t + rnd.gauss(0, 14)
        if inside(x, y, 134):
            faint += [int(x), int(y)]
    for _ in range(45):
        x, y = rnd.randint(16, 264), rnd.randint(16, 264)
        if inside(x, y, 130):
            bright += [x, y]
    ops.append([OP_POINTS, ORN2, 1] + faint)
    ops.append([OP_POINTS, STAR, 2] + bright)
    for (x, y) in [(40, 150), (236, 160), (172, 104), (110, 210)]:   # sparkles
        ops.append([OP_LINE, STAR, 1, x - 3, y, x + 3, y])
        ops.append([OP_LINE, STAR, 1, x, y - 3, x, y + 3])
    ops.append([OP_CRESCENT, GOLD, BG, 60, 80, 15, 7, -4, 12])
    return ops


def build_backgrounds():
    out = {}
    for name, fn in [("bg_mosque", bg_mosque), ("bg_geometric", bg_geometric), ("bg_marble", bg_marble),
                     ("bg_night", bg_night)]:
        ops = fn()
        for op in ops:
            assert op[0] != OP_POLY or len(op) - 2 <= 128, "polygon too large"
        path = os.path.join(RES, "jsonData", name + ".json")
        with open(path, "w") as fh:
            json.dump(ops, fh, separators=(",", ":"))
        out[name] = {"ops": len(ops), "bytes": os.path.getsize(path)}
    return out


# ------------------------------------------------------------------ launcher icon
def build_icon():
    s = 4
    n = 40 * s
    img = Image.new("RGB", (n, n), (0, 0, 0x55))
    d = ImageDraw.Draw(img)
    d.ellipse([2 * s, 2 * s, n - 2 * s, n - 2 * s], outline=(0xFF, 0xAA, 0), width=2 * s)
    # crescent
    d.ellipse([9 * s, 8 * s, 31 * s, 30 * s], fill=(0xFF, 0xAA, 0))
    d.ellipse([14 * s, 5 * s, 34 * s, 27 * s], fill=(0, 0, 0x55))
    # star
    cx, cy, r = 27 * s, 25 * s, 4 * s
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=(0, 0xFF, 0xFF))
    img = img.resize((40, 40), Image.LANCZOS)
    img.save(os.path.join(RES, "drawables", "launcher_icon.png"))


def main():
    os.makedirs(os.path.join(RES, "fonts"), exist_ok=True)
    os.makedirs(os.path.join(RES, "jsonData"), exist_ok=True)
    report = {"fonts": [build_latin_font(*f) for f in FONTS]}
    report["ayah"] = build_ayah_font()
    report["backgrounds"] = build_backgrounds()
    build_icon()
    with open(os.path.join(ROOT, "tools", "assets-report.json"), "w") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    json.dump(report, sys.stdout, indent=1, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
