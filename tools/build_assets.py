#!/usr/bin/env python3
"""Generate the bundled resources of Luxe Hijri Prayer (reproducible, no network needed).

Outputs (one font set per supported round screen size, selected by Connect IQ resource
qualifiers; 280 x 280 is the base set in resources/):
  resources[-round-WxH]/fonts/*.fnt + *.png + fonts.xml   BMFont bitmap fonts
  resources[-round-WxH]/fonts/ayah.*                     one pre-shaped Arabic glyph per Ayah
  resources/jsonData/*.json                              vector art in 280 x 280 coordinates
                                                          (scaled at runtime to the screen)
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
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont, features

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shapes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_SRC = os.path.join(ROOT, "tools", "fonts-src")
RES = os.path.join(ROOT, "resources")
BASE = 280
# Round colour screens of current Connect IQ watches (pixels). 280 is the base resource set.
RESOLUTIONS = [218, 240, 260, 280, 360, 390, 416, 454]

LATIN = "".join(chr(c) for c in range(32, 127)) + "ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜàâäçéèêëîïôöùûü·°’«»−"

# Text font families (setting "Font"): prefix, bold ttf, semibold ttf, (bold, semibold) variable
# weights or None, size factor (keeps every family inside the same layout; see check_layout.py)
FAMILIES = [
    ("luxe", "BarlowSemiCondensed-Bold.ttf", "BarlowSemiCondensed-SemiBold.ttf", None, 1.0),     # Modern
    ("classic", "Cinzel-Variable.ttf", "Cinzel-Variable.ttf", (700, 600), 0.8),                    # Classic
    ("sport", "Rajdhani-Bold.ttf", "Rajdhani-SemiBold.ttf", None, 0.95),                            # Sport
]
# role, bold?, pixel size at 280 px, character set
ROLES = [
    ("l", True, 30, " 0123456789%-"),
    ("m", True, 20, LATIN),
    ("s", False, 15, LATIN),
    ("xs", False, 12, LATIN),
]
# id, ttf, pixel size at 280 px, character set, variable weight
FONTS = [("luxe_num", "BarlowSemiCondensed-Bold.ttf", 25, " 0123456789", None)]
for _pre, _bold, _semi, _w, _f in FAMILIES:
    for _role, _isbold, _px, _chars in ROLES:
        if _pre == "classic" and _role in ("s", "xs"):
            # Cinzel is too wide for the small texts: the Classic family pairs the serif for the
            # large figures with Barlow for labels and small text
            FONTS.append(("%s_%s" % (_pre, _role), "BarlowSemiCondensed-SemiBold.ttf", _px, _chars, None))
            continue
        FONTS.append(("%s_%s" % (_pre, _role), _bold if _isbold else _semi, _px * _f, _chars,
                      None if _w is None else (_w[0] if _isbold else _w[1])))
FONT_IDS = {"luxe_num": "LuxeNum", "ar_small": "ArSmall"}
FONT_IDS.update({"ayah%d" % g: "Ayah%d" % g for g in range(5)})
FONT_IDS.update({"%s_%s" % (p, r): "%s%s" % (p.capitalize(), r.upper()) for p, *_ in FAMILIES for r, *_ in ROLES})


def layout_consts():
    src = open(os.path.join(ROOT, "source", "Layout.mc")).read()
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", src)}


def res_dir(size):
    return RES if size == BASE else os.path.join(ROOT, "resources-round-%dx%d" % (size, size))


# ------------------------------------------------------------------ BMFont writer
def pack_and_write(folder, name, glyphs, line_height, base, size, face):
    """glyphs: list of (char id, L-mode coverage image or None, xoffset, yoffset, xadvance)."""
    width = 256
    pad = 1
    for _, img, _, _, _ in glyphs:
        if img is not None and img.width + 2 * pad > width:
            width = 1 << (img.width + 2 * pad - 1).bit_length()
    x = y = row_h = 0
    placed = []
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
    atlas.save(os.path.join(folder, name + ".png"), optimize=True)
    with open(os.path.join(folder, name + ".fnt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build_latin_font(folder, name, ttf, size, chars, weight=None):
    font = ImageFont.truetype(os.path.join(FONT_SRC, ttf), size)
    if weight is not None:
        font.set_variation_by_axes([weight])
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
    pack_and_write(folder, name, glyphs, ascent + descent, ascent, size, os.path.splitext(ttf)[0])
    return {"id": name, "size": size, "lineHeight": ascent + descent}


# ------------------------------------------------------------------ Ayah glyph font
def render_arabic_line(text, size):
    font = ImageFont.truetype(os.path.join(FONT_SRC, "Amiri-Bold.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    bbox = font.getbbox(text, direction="rtl", language="ar")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("L", (w + 2, h + 2), 0)
    ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), text, font=font, fill=255, direction="rtl", language="ar")
    return img.crop(img.getbbox())


def ayah_fits(w, h, L, k):
    """Single line centred on AYAH_Y, inside the Ayah area circle with a 4 px margin (scaled by k)."""
    # on the smallest screens the 8 px floor of the reference costs one pixel of verse height
    max_h = L["AYAH_MAX_H"] * k - (1 if k < 0.9 else 0)
    if h > max_h or w > L["AYAH_MAX_W"] * k:
        return False
    bottom = (L["AYAH_Y"] - L["CY"]) * k + (h + 1) / 2.0
    return w <= 2 * math.sqrt(max(0.0, ((L["AYAH_AREA_R"] - 4) * k) ** 2 - bottom ** 2))


def render_small_arabic(text, size):
    """Arabic text on a common baseline: (image, yoffset, width) for the small Arabic pieces."""
    font = ImageFont.truetype(os.path.join(FONT_SRC, "Amiri-Bold.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    ascent, descent = font.getmetrics()
    bbox = font.getbbox(text, direction="rtl", language="ar", anchor="ls")
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    img = Image.new("L", (w + 2, h + 2), 0)
    ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), text, font=font, fill=255, direction="rtl",
                             language="ar", anchor="ls")
    return img, ascent + bbox[1] - 1, w, ascent + descent


AYAH_GROUP = 8
AYAH_REF_PX = 10   # at 280 px: surah name and verse number under the verse
AYAH_MIN_PX = 13   # at 280 px: complete verses below this size are not included


def build_ayah_fonts(folder, k, L):
    """One font per group of 8 verses (Ayah0..Ayah4): verse glyphs "A".."H" (as large as the Ayah
    area allows) and their Arabic references "a".."h" (surah name and verse number)."""
    if not features.check("raqm"):
        raise SystemExit("Pillow was built without raqm: Arabic shaping unavailable")
    data = json.load(open(os.path.join(ROOT, "tools", "ayat.json")))
    ref_px = max(8, int(AYAH_REF_PX * k))
    sizes = {}
    groups = {}
    for a in data["ayat"]:
        groups.setdefault(a["font"], []).append(a)
    for g, items in sorted(groups.items()):
        glyphs = []
        verse_imgs = []
        for a in items:
            for size in range(int(26 * k), 7, -1):
                img = render_arabic_line(a["lines"][0], size)
                if ayah_fits(img.width, img.height, L, k):
                    break
            else:
                raise SystemExit("Ayah %s does not fit at %d px" % (a["ref"], BASE * k))
            if k == 1.0 and size < AYAH_MIN_PX:
                raise SystemExit("Ayah %s would be %d px at 280 px (< %d)" % (a["ref"], size, AYAH_MIN_PX))
            verse_imgs.append((a, img))
            sizes[a["ref"]] = {"px": size, "w": img.width, "h": img.height}
        refs = [(a, render_small_arabic(a["ref_ar"], ref_px)) for a in items]
        line_h = max([i.height for _, i in verse_imgs] + [r[3] for _, r in refs])
        for a, img in verse_imgs:
            glyphs.append((ord(a["code"]), img, 0, (line_h - img.height) // 2, img.width))
        for a, (img, yoff, w, lh) in refs:
            # each reference is shown alone: centre its ink rather than sharing a baseline
            # (240 px: the 8 px floor leaves no room below, so the reference moves up 1 px)
            nudge = 1 if 0.8 < k < 0.9 else 0
            glyphs.append((ord(a["ref_code"]), img, -1, (line_h - img.height) // 2 - nudge, w + 2))
            sizes[a["ref"]]["ref_w"] = w
        glyphs.append((32, None, 0, 0, 4))
        pack_and_write(folder, "ayah%d" % g, glyphs, line_h, line_h, line_h, "Amiri-Bold (pre-shaped Ayat %d)" % g)
    return sizes


AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
AR_SMALL_PX = 11  # at 280 px


def build_arabic_small_font(folder, k):
    """Small Arabic font assembled at runtime: glyph "0".."9" = Eastern Arabic digits, "A".."L" =
    Hijri month names, "M" = the AH suffix. Every glyph is shaped with HarfBuzz and placed on a
    common baseline."""
    data = json.load(open(os.path.join(ROOT, "tools", "ayat.json")))
    size = max(8, int(AR_SMALL_PX * k))
    font = ImageFont.truetype(os.path.join(FONT_SRC, "Amiri-Bold.ttf"), size, layout_engine=ImageFont.Layout.RAQM)
    ascent, descent = font.getmetrics()
    items = [(str(i), AR_DIGITS[i]) for i in range(10)]
    items += [(chr(ord("A") + i), m) for i, m in enumerate(data["hijri_months_ar"])]
    items += [("M", data["hijri_suffix_ar"])]
    glyphs = []
    widths = {}
    for code, text in items:
        bbox = font.getbbox(text, direction="rtl", language="ar", anchor="ls")
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        img = Image.new("L", (w + 2, h + 2), 0)
        ImageDraw.Draw(img).text((1 - bbox[0], 1 - bbox[1]), text, font=font, fill=255, direction="rtl",
                                 language="ar", anchor="ls")
        glyphs.append((ord(code), img, -1, ascent + bbox[1] - 1, w + (1 if code.isdigit() else 2)))
        widths[code] = w
    glyphs.append((32, None, 0, 0, max(3, int(round(size * 0.3)))))
    pack_and_write(folder, "ar_small", glyphs, ascent + descent, ascent, size, "Amiri-Bold (pre-shaped Arabic pieces)")
    return {"px": size, "widths": widths}


def write_fonts_xml(folder):
    lines = ["<fonts>", "    <!-- Generated by tools/build_assets.py (Barlow Semi Condensed / Amiri, SIL OFL) -->"]
    for name in [f[0] for f in FONTS] + ["ar_small"] + ["ayah%d" % g for g in range(5)]:
        lines.append('    <font id="%s" filename="%s.fnt" antialias="true" />' % (FONT_IDS[name], name))
    lines.append("</fonts>")
    with open(os.path.join(folder, "fonts.xml"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build_font_sets():
    L = layout_consts()
    report = {}
    for size in RESOLUTIONS:
        k = size / float(BASE)
        folder = os.path.join(res_dir(size), "fonts")
        if size != BASE and os.path.isdir(folder):
            shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)
        for f in os.listdir(folder):
            if f.endswith((".fnt", ".png")):
                os.remove(os.path.join(folder, f))
        fonts = [build_latin_font(folder, n, t, max(9, int(s * k)), c, w) for n, t, s, c, w in FONTS]
        ayah = build_ayah_fonts(folder, k, L)
        arabic = build_arabic_small_font(folder, k)
        write_fonts_xml(folder)
        report[size] = {"fonts": fonts, "ayah": ayah, "ar_small": arabic}
    return report


# ------------------------------------------------------------------ vector art
# Colour roles (see source/Themes.mc)
(BG, PLATE, ORN, ORN2, GOLD, GOLD_DK, ACCENT, ACCENT2, TEXT, DIM, TRACK, SECONDS, SIL, STAR, WARN,
 TICK) = range(16)
# Op codes interpreted by source/Backgrounds.mc and tools/face.py
(OP_POLY, OP_CIRCLE, OP_LINE, OP_POLYLINE, OP_POINTS, OP_RING, OP_RECT, OP_STAR8, OP_FILL, OP_CRESCENT,
 OP_RRECT, OP_RRECT_LINE) = range(12)


def inside(x, y, r=139):
    return (x - 140) ** 2 + (y - 140) ** 2 <= r * r


def arch_points(L, inset=0):
    """Outline of the Moorish window (tools/shapes.py), rounded to whole dial units."""
    return [(int(round(x)), int(round(y))) for x, y in shapes.window_points(L, inset)]


def flat(pts):
    return [v for p in pts for v in p]


def frame_ops(L):
    """Elements common to every background: arch window frame and prayer cartouches."""
    ops = []
    ops.append([OP_POLYLINE, GOLD_DK, 1] + flat(arch_points(L)))
    ops.append([OP_POLYLINE, GOLD_DK, 1] + flat(arch_points(L, -3)))
    w, h, y0 = L["PANEL_W"], L["PANEL_H"], L["PANEL_Y0"]
    for sgn in (-1, 1):
        x0 = 140 + sgn * L["PANEL_DX"] - w // 2
        ops.append([OP_RRECT, PLATE, x0, y0, w, h, 7])
        ops.append([OP_RRECT_LINE, GOLD_DK, 1, x0, y0, w, h, 7])
    return ops


def lattice(role, step=34, r=11):
    ops = []
    for gy in range(-step, 281 + step, step):
        for gx in range(-step, 281 + step, step):
            ox = step // 2 if (gy // step) % 2 else 0
            cx, cy = gx + ox, gy
            if inside(cx, cy, 150):
                ops.append([OP_STAR8, role, 1, cx, cy, r])
    return ops


def arch_fill(L, role):
    """Window area as convex polygons (fillPolygon is only guaranteed for convex shapes)."""
    return [[OP_POLY, role] + flat([(int(round(x)), int(round(y))) for x, y in part])
            for part in shapes.window_fill_parts(L)]


def palm(x, base, top, lean):
    ops = [[OP_POLYLINE, SIL, 2, x, base, x + lean // 2, (base + top) // 2, x + lean, top]]
    tx, ty = x + lean, top
    for ang, ln in [(-160, 11), (-130, 10), (-95, 7), (-50, 10), (-20, 11)]:
        a = math.radians(ang)
        mx, my = tx + ln * 0.55 * math.cos(a), ty + ln * 0.55 * math.sin(a) - 2
        ex, ey = tx + ln * math.cos(a), ty + ln * math.sin(a) + 3
        ops.append([OP_POLYLINE, SIL, 2, tx, ty, int(round(mx)), int(round(my)), int(round(ex)), int(round(ey))])
    return ops


def mosque_scene(L):
    """Mosque, minarets, palms and water inside the arch window (centred under the pivot)."""
    ops = []
    s = SIL
    base = 186
    # water (dark) with golden reflections of the lit windows
    ops.append([OP_RECT, PLATE, 99, base, 83, 22])
    for x, ln, dy in [(124, 5, 4), (133, 4, 4), (143, 4, 4), (152, 5, 4), (128, 7, 9), (141, 6, 9), (137, 6, 14)]:
        ops.append([OP_LINE, GOLD_DK, 1, x, base + dy, x + ln, base + dy])
    # tall outer minarets with two balconies, lantern and cone
    for mx in (110, 170):
        ops.append([OP_RECT, s, mx - 3, 140, 7, base - 140])
        ops.append([OP_RECT, s, mx - 5, 152, 11, 2])
        ops.append([OP_RECT, s, mx - 5, 166, 11, 2])
        ops.append([OP_POLY, s, mx - 3, 140, mx + 4, 140, mx, 130])
        ops.append([OP_LINE, s, 1, mx, 130, mx, 126])
        for wy in (145, 158, 172):
            ops.append([OP_RECT, GOLD_DK, mx, wy, 1, 3])
    # prayer hall, side domes, drum and main dome
    ops.append([OP_RECT, s, 114, 174, 53, base - 174])
    ops.append([OP_CIRCLE, s, 122, 175, 8])
    ops.append([OP_CIRCLE, s, 158, 175, 8])
    ops.append([OP_RECT, s, 126, 163, 29, base - 163])
    ops.append([OP_CIRCLE, s, 140, 162, 14])
    ops.append([OP_POLY, s, 138, 149, 143, 149, 141, 143, 140, 143])
    ops.append([OP_LINE, s, 1, 140, 143, 140, 139])
    ops.append([OP_CRESCENT, GOLD, BG, 140, 137, 2, 1, -1, 2])
    # lit arched windows, arcade and gate
    for x in (129, 134, 146, 151):
        ops.append([OP_RECT, GOLD_DK, x, 167, 2, 4])
    for x in range(117, 166, 6):
        if abs(x - 140) > 5:
            ops.append([OP_RECT, GOLD_DK, x, 179, 2, 4])
    ops.append([OP_RECT, GOLD, 137, 177, 7, 9])
    ops.append([OP_CIRCLE, GOLD, 140, 177, 3])
    # palms at the sides of the window
    ops += palm(101, base, 160, 3)
    ops += palm(179, base, 160, -3)
    return ops


def stars_in_arch(L, rnd, n, role, size):
    pts = []
    tries = 0
    poly = arch_points(L, 6)
    while len(pts) < 2 * n and tries < 5000:
        tries += 1
        x, y = rnd.randint(L["WINDOW_X0"] + 5, L["WINDOW_X1"] - 5), rnd.randint(L["WINDOW_TOP"] + 6, 150)
        if point_in_poly(x, y, poly) and abs(x - 140) + abs(y - 140) > 10:
            pts += [x, y]
    return [OP_POINTS, role, size] + pts


def point_in_poly(x, y, poly):
    inside_ = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / float(yj - yi) + xi:
            inside_ = not inside_
        j = i
    return inside_


def bg_mosque(L):
    rnd = random.Random(7)
    ops = lattice(PLATE)
    ops += arch_fill(L, BG)
    ops.append(stars_in_arch(L, rnd, 14, STAR, 1))
    ops.append(stars_in_arch(L, rnd, 5, STAR, 2))
    ops.append([OP_CRESCENT, GOLD, BG, 157, 131, 8, 4, -3, 7])
    ops += mosque_scene(L)
    return ops


def bg_geometric(L):
    ops = lattice(ORN, 28, 9)
    ops += arch_fill(L, BG)
    for r in (34, 25, 16, 7):
        ops.append([OP_STAR8, ORN2, 1, 140, 160, r])
    ops.append([OP_RING, ORN2, 1, 140, 160, 30])
    return ops


def _vein(rnd, x, y, ang, n, step):
    pts = []
    for _ in range(n):
        pts += [int(round(x)), int(round(y))]
        ang += rnd.uniform(-0.45, 0.45)
        x += step * math.cos(ang)
        y += step * math.sin(ang)
    return pts


def bg_marble(L):
    rnd = random.Random(1448)
    ops = [[OP_FILL, PLATE]]
    cloud = []
    for _ in range(260):
        cx, cy = rnd.choice([(70, 90), (200, 70), (180, 200), (90, 210), (140, 140)])
        x, y = int(rnd.gauss(cx, 26)), int(rnd.gauss(cy, 20))
        if inside(x, y, 136):
            cloud += [x, y]
    ops.append([OP_POINTS, ORN, 1] + cloud)
    for _ in range(14):
        ops.append([OP_POLYLINE, ORN, 1] + _vein(rnd, rnd.uniform(-20, 300), rnd.uniform(-20, 300),
                                                  rnd.uniform(0, 6.28), 22, 14))
    for k in range(6):
        x, y = rnd.uniform(0, 80), rnd.uniform(20, 260)
        main = _vein(rnd, x, y, rnd.uniform(-0.6, 0.6), 26, 12)
        ops.append([OP_POLYLINE, GOLD_DK, 2 if k < 2 else 1] + main)
        for _ in range(3):
            i = rnd.randrange(4, 20) * 2
            ops.append([OP_POLYLINE, GOLD_DK, 1] + _vein(rnd, main[i], main[i + 1], rnd.uniform(0, 6.28), 6, 8))
    return ops


def bg_night(L):
    rnd = random.Random(29)
    ops = []
    faint, bright, small = [], [], []
    for _ in range(320):
        t = rnd.uniform(0, 1)
        x = 10 + 260 * t + rnd.gauss(0, 16)
        y = 250 - 220 * t + rnd.gauss(0, 16)
        if inside(x, y, 136):
            faint += [int(x), int(y)]
    for _ in range(70):
        x, y = rnd.randint(14, 266), rnd.randint(14, 266)
        if inside(x, y, 132):
            small += [x, y]
    stars = []
    for _ in range(26):
        x, y = rnd.randint(18, 262), rnd.randint(18, 262)
        if inside(x, y, 128):
            bright += [x, y]
            stars.append((x, y))
    ops.append([OP_POINTS, ORN2, 1] + faint)
    ops.append([OP_POINTS, STAR, 1] + small)
    ops.append([OP_POINTS, STAR, 2] + bright)
    # a constellation (faint lines between a few bright stars)
    con = sorted(stars, key=lambda p: p[0])[:5]
    ops.append([OP_POLYLINE, ORN2, 1] + flat(con))
    for (x, y) in [(40, 150), (236, 160), (172, 104), (110, 210), (60, 60), (222, 228)]:
        ops.append([OP_LINE, STAR, 1, x - 4, y, x + 4, y])
        ops.append([OP_LINE, STAR, 1, x, y - 4, x, y + 4])
        ops.append([OP_LINE, STAR, 1, x - 2, y - 2, x + 2, y + 2])
        ops.append([OP_LINE, STAR, 1, x - 2, y + 2, x + 2, y - 2])
    ops.append([OP_CRESCENT, GOLD, BG, 150, 168, 18, 8, -5, 15])
    return ops


def build_vector_art():
    L = layout_consts()
    out = {}
    jobs = [("bg_mosque", bg_mosque), ("bg_geometric", bg_geometric), ("bg_marble", bg_marble),
            ("bg_night", bg_night), ("frame", frame_ops)]
    os.makedirs(os.path.join(RES, "jsonData"), exist_ok=True)
    for name, fn in jobs:
        ops = fn(L)
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
    d.ellipse([9 * s, 8 * s, 31 * s, 30 * s], fill=(0xFF, 0xAA, 0))
    d.ellipse([14 * s, 5 * s, 34 * s, 27 * s], fill=(0, 0, 0x55))
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
    report = {"fonts": build_font_sets(), "vector": build_vector_art()}
    build_icon()
    with open(os.path.join(ROOT, "tools", "assets-report.json"), "w") as fh:
        json.dump(report, fh, indent=1, ensure_ascii=False)
    summary = {size: {k: v["px"] for k, v in r["ayah"].items()} for size, r in report["fonts"].items()}
    print(json.dumps({"ayah_px": summary, "vector": report["vector"]}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
