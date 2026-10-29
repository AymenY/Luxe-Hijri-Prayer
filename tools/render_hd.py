#!/usr/bin/env python3
"""High-definition static dial artwork, rendered offline (numpy + Pillow).

For every screen size, style preset and background this renders the complete static layer of
the dial — background art, arch scene, chapter ring, indices, numerals, gauge recesses,
cartouches and fixed icons — with 3x supersampling, gradients, glows, bevels, inner shadows
and textures. The watch draws only the live content (texts, gauge arcs, hands) on top, at the
positions of source/Layout.mc, which this module reads.

Images are produced in full colour; for MIP screens the Connect IQ compiler converts them to the
palette of each device. to_mip() simulates the 64-colour case for the previews.
"""
import math
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shapes  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_SRC = os.path.join(ROOT, "tools", "fonts-src")
SS = 3                       # supersampling factor
AMOLED_FROM = 360


def layout():
    src = open(os.path.join(ROOT, "source", "Layout.mc")).read()
    return {k: int(v) for k, v in re.findall(r"const\s+(\w+)\s*=\s*(-?\d+)\s*;", src)}


L = layout()


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


# HD palettes per style preset (order of source/Themes.mc)
STYLES = [
    dict(name="luxury-blue", base=("#123063", "#030a1c"), ring=("#0b1a38", "#02060f"),
         metal=("#fff2c4", "#e2b04a", "#8a5a14"), glow="#3aa0ff", tick="#cfe8ff",
         sky=("#020717", "#1d4588"), pattern="#1b3f80", recess=("#081230", "#01040c"), track="#13254d",
         panel=("#0c1a3c", "#030914")),
    dict(name="royal-gold", base=("#2a2210", "#030302"), ring=("#17120a", "#020201"),
         metal=("#fff4cf", "#e6b34c", "#80520f"), glow="#ffb347", tick="#e8d9a8",
         sky=("#050403", "#3d2c0e"), pattern="#3a2d12", recess=("#16120a", "#020201"), track="#3a2e14",
         panel=("#1d170c", "#050403")),
    dict(name="emerald-night", base=("#0b4a33", "#010d08"), ring=("#06261a", "#010604"),
         metal=("#fff2c4", "#e2b04a", "#8a5a14"), glow="#2ee59d", tick="#c9f5df",
         sky=("#010a07", "#0f4a35"), pattern="#0f5a3e", recess=("#05261a", "#010604"), track="#0e3d2b",
         panel=("#082a1d", "#020a07")),
    dict(name="burgundy-royale", base=("#5c1027", "#14030a"), ring=("#2e0812", "#080104"),
         metal=("#ffe1d2", "#de9a7e", "#7a3f2c"), glow="#ff5c8a", tick="#ffd6dc",
         sky=("#14030a", "#5a1436"), pattern="#6e1a33", recess=("#2c0712", "#070104"), track="#4a1222",
         panel=("#2d0914", "#0a0205")),
    dict(name="ice-silver", base=("#173a63", "#02070f"), ring=("#0c1d33", "#020509"),
         metal=("#ffffff", "#c2cfdc", "#56677a"), glow="#9ee7ff", tick="#e6f6ff",
         sky=("#020611", "#21497a"), pattern="#21456e", recess=("#0b1a2e", "#010409"), track="#1c3352",
         panel=("#0e2038", "#030810")),
    dict(name="stealth", base=("#2a2f35", "#050607"), ring=("#16191c", "#030404"),
         metal=("#f2f4f6", "#9aa1a8", "#3a3f44"), glow="#d8e2ec", tick="#d0d4d8",
         sky=("#040506", "#283038"), pattern="#30363d", recess=("#121417", "#020303"), track="#2a2f35",
         panel=("#16191c", "#040505")),
]
BACKGROUNDS = ["mosque", "geometric", "marble", "night"]


class Art:
    """A float RGB canvas with compositing helpers, in supersampled pixels."""

    def __init__(self, size):
        self.size = size
        self.n = size * SS
        self.k = size / 280.0 * SS
        self.rgb = np.zeros((self.n, self.n, 3))
        yy, xx = np.mgrid[0:self.n, 0:self.n]
        self.x = (xx + 0.5) / self.k          # coordinates in 280-px dial units
        self.y = (yy + 0.5) / self.k

    # -- geometry helpers (all inputs in dial units)
    def u(self, v):
        return v * self.k

    def mask(self, draw_fn):
        m = Image.new("L", (self.n, self.n), 0)
        draw_fn(ImageDraw.Draw(m), self.u)
        return np.asarray(m, dtype=np.float64) / 255.0

    def blur(self, m, radius):
        img = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
        return np.asarray(img.filter(ImageFilter.GaussianBlur(self.u(radius))), dtype=np.float64) / 255.0

    # -- compositing
    def paint(self, color, m, alpha=1.0):
        a = np.clip(m * alpha, 0, 1)[..., None]
        col = color if isinstance(color, np.ndarray) and color.ndim == 3 else np.broadcast_to(color, self.rgb.shape)
        self.rgb = self.rgb * (1 - a) + col * a

    def add(self, color, m, amount=1.0):
        """Additive light (glows)."""
        self.rgb = np.clip(self.rgb + np.clip(m * amount, 0, 1)[..., None] * color, 0, 1)

    def radial(self, cx, cy, r, c0, c1, power=1.0):
        d = np.clip(np.hypot(self.x - cx, self.y - cy) / r, 0, 1) ** power
        return c0 * (1 - d[..., None]) + c1 * d[..., None]

    def vertical(self, y0, y1, c0, c1):
        t = np.clip((self.y - y0) / float(y1 - y0), 0, 1)[..., None]
        return c0 * (1 - t) + c1 * t

    def metal(self, y0, y1, pal):
        """Polished metal: light band near the top, darker below, a second soft highlight."""
        light, mid, dark = (hexc(c) for c in pal)
        t = np.clip((self.y - y0) / float(max(1e-3, y1 - y0)), 0, 1)
        w1 = np.exp(-((t - 0.18) / 0.16) ** 2)
        w2 = np.exp(-((t - 0.72) / 0.22) ** 2) * 0.35
        base = mid * (1 - t[..., None]) + dark * t[..., None]
        return np.clip(base + (light - mid) * (w1 + w2)[..., None], 0, 1)

    def noise(self, scale, seed):
        rng = np.random.default_rng(seed)
        small = max(2, int(self.n / (scale * SS)))
        arr = rng.random((small, small))
        img = Image.fromarray((arr * 255).astype(np.uint8)).resize((self.n, self.n), Image.BICUBIC)
        return np.asarray(img, dtype=np.float64) / 255.0

    def fractal(self, seed, octaves=5, base=40.0):
        out = np.zeros((self.n, self.n))
        amp, tot = 1.0, 0.0
        for o in range(octaves):
            out += self.noise(base / (2 ** o), seed + o) * amp
            tot += amp
            amp *= 0.5
        return out / tot

    def finish(self):
        img = Image.fromarray((np.clip(self.rgb, 0, 1) * 255).astype(np.uint8), "RGB")
        img = img.resize((self.size, self.size), Image.LANCZOS)
        return img


# ------------------------------------------------------------------ shapes
def arch_points(inset=0.0):
    """The Moorish window of the dial (see tools/shapes.py)."""
    return shapes.window_points(L, inset)


def poly(draw, u, pts, **kw):
    draw.polygon([(u(x), u(y)) for x, y in pts], **kw)


def circle(draw, u, cx, cy, r, **kw):
    draw.ellipse([u(cx - r), u(cy - r), u(cx + r), u(cy + r)], **kw)


def ring_mask(art, cx, cy, r, width):
    return art.mask(lambda d, u: circle(d, u, cx, cy, r + width / 2.0, outline=255, width=max(1, int(u(width)))))


def star8(cx, cy, r, inner=0.0):
    """8-point star polygon (two squares) or Rub el Hizb outline points."""
    pts = []
    for i in range(16):
        a = -math.pi / 2 + i * math.pi / 8
        rr = r if i % 2 == 0 else r * (0.7071 / math.cos(math.pi / 8)) * 0.92
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def gauge_centres():
    return [(140 - L["GAUGE_UP_DX"], L["GAUGE_UP_Y"]), (140 + L["GAUGE_UP_DX"], L["GAUGE_UP_Y"]),
            (140 - L["GAUGE_SIDE_DX"], L["GAUGE_SIDE_Y"]), (140 + L["GAUGE_SIDE_DX"], L["GAUGE_SIDE_Y"])]


# ------------------------------------------------------------------ layers
def layer_base(art, st):
    c0, c1 = hexc(st["base"][0]), hexc(st["base"][1])
    art.rgb = art.radial(140, 120, 150, c0, c1, power=1.3)
    art.rgb = np.clip(art.rgb + (art.noise(1.2, 7) - 0.5)[..., None] * 0.025, 0, 1)


def lattice_mask(art, step, r, width=0.6):
    def draw(d, u):
        for gy in range(-step, 281 + step, step):
            for gx in range(-step, 281 + step, step):
                ox = step / 2.0 if (gy // step) % 2 else 0
                pts = star8(gx + ox, gy, r)
                d.line([(u(x), u(y)) for x, y in pts + pts[:1]], fill=255, width=max(1, int(u(width))))
                d.ellipse([u(gx + ox - r * 0.32), u(gy - r * 0.32), u(gx + ox + r * 0.32), u(gy + r * 0.32)],
                          outline=255, width=max(1, int(u(width))))
    return art.mask(draw)


def layer_pattern(art, st, bg):
    pat = hexc(st["pattern"])
    if bg == "mosque":
        m = lattice_mask(art, 34, 11)
        # embossed: highlight up-left, shadow down-right
        art.paint(pat * 1.6, np.roll(m, (-SS, -SS), (0, 1)), 0.22)
        art.paint(np.zeros(3), np.roll(m, (SS, SS), (0, 1)), 0.25)
        art.paint(pat, m, 0.55)
    elif bg == "geometric":
        m = lattice_mask(art, 28, 9, 0.8)
        metal = art.metal(0, 280, st["metal"])
        art.add(hexc(st["glow"]) * 0.35, art.blur(m, 1.6), 0.6)
        art.paint(metal * 0.55, m, 0.75)
    elif bg == "marble":
        f = art.fractal(11, 6, 70)
        veins = np.abs(np.sin((art.x * 0.035 + art.y * 0.022 + f * 7.5) * math.pi))
        dark = hexc(st["recess"][1]) * 0.6 + 0.012
        cloud = hexc(st["pattern"]) * 0.55
        art.rgb = dark + (cloud - dark) * (f ** 1.6)[..., None]
        thin = np.clip(1 - veins / 0.035, 0, 1)
        gold = hexc(st["metal"][1])
        art.add(gold * 0.45, art.blur(thin, 0.9), 0.8)
        art.paint(gold, thin, 0.75)
        grey = np.clip(1 - np.abs(np.sin((art.x * 0.05 - art.y * 0.03 + f * 5) * math.pi)) / 0.05, 0, 1)
        art.paint(np.array([0.55, 0.57, 0.6]), grey, 0.18)
    elif bg == "night":
        sky = art.radial(170, 90, 230, hexc(st["sky"][1]) * 0.8, hexc(st["sky"][0]), 0.9)
        art.rgb = sky
        band = np.exp(-(((art.x - 280 + art.y) / math.sqrt(2) - 0) / 34.0) ** 2)
        mw = band * art.fractal(23, 5, 30) ** 2
        art.add(np.array([0.55, 0.62, 0.85]), art.blur(mw, 2.0), 0.55)
        stars(art, 260, 31, st, big=10)


def stars(art, count, seed, st, big=6, region=None):
    rng = np.random.default_rng(seed)
    m = np.zeros((art.n, art.n))
    glow = np.zeros((art.n, art.n))
    for i in range(count):
        x, y = rng.uniform(0, 280), rng.uniform(0, 280)
        if region is not None and not region(x, y):
            continue
        cx, cy = int(art.u(x)), int(art.u(y))
        if 0 <= cx < art.n and 0 <= cy < art.n:
            b = rng.uniform(0.35, 1.0)
            m[cy, cx] = b
            if i < big:
                glow[cy, cx] = 1.0
    core = art.blur(m, 0.35) * 9
    art.add(np.array([1.0, 0.98, 0.92]), core, 1.0)
    halo = art.blur(glow, 2.2) * 120
    art.add(hexc(st["glow"]) * 0.6, halo, 1.0)
    return m


def arch_window(art, st, bg):
    win = art.mask(lambda d, u: poly(d, u, arch_points(), fill=255))
    inside = lambda x, y: L["WINDOW_X0"] < x < L["WINDOW_X1"] and L["WINDOW_TOP"] < y < L["WINDOW_BOTTOM"]
    sky0, sky1 = hexc(st["sky"][0]), hexc(st["sky"][1])
    save = art.rgb.copy()
    # sky
    art.rgb = art.vertical(L["WINDOW_TOP"], 200, sky0, sky1)
    art.add(hexc(st["glow"]) * 0.25, np.exp(-((art.y - 186) / 14.0) ** 2), 1.0)
    if bg == "mosque":
        stars(art, 220, 5, st, big=4, region=lambda x, y: inside(x, y) and y < 160)
        crescent(art, st, 158, 132, 9)
        mosque(art, st)
    elif bg == "geometric":
        stars(art, 140, 9, st, big=3, region=lambda x, y: inside(x, y) and y < 175)
        rosette(art, st, 140, 165)
    elif bg == "marble":
        layer_pattern(art, st, "marble")
        art.rgb *= 0.8
        rosette(art, st, 140, 162, simple=True)
    else:
        stars(art, 320, 13, st, big=8, region=inside)
        crescent(art, st, 152, 160, 20)
    scene = art.rgb
    art.rgb = save
    art.paint(scene, win)
    # gold frame: double line with glow
    outer = art.mask(lambda d, u: d.line([(u(x), u(y)) for x, y in arch_points(-2.5)], fill=255, width=max(1, int(u(1.6)))))
    inner = art.mask(lambda d, u: d.line([(u(x), u(y)) for x, y in arch_points(0.5)], fill=255, width=max(1, int(u(0.8)))))
    art.add(hexc(st["glow"]) * 0.5, art.blur(outer, 2.4), 0.9)
    art.paint(art.metal(L["WINDOW_TOP"], L["WINDOW_BOTTOM"], st["metal"]), outer)
    art.paint(art.metal(L["WINDOW_TOP"], L["WINDOW_BOTTOM"], st["metal"]), inner, 0.8)


def crescent(art, st, cx, cy, r):
    m = art.mask(lambda d, u: circle(d, u, cx, cy, r, fill=255))
    cut = art.mask(lambda d, u: circle(d, u, cx + r * 0.42, cy - r * 0.3, r * 0.86, fill=255))
    c = np.clip(m - cut, 0, 1)
    art.add(hexc(st["metal"][0]) * 0.35, art.blur(c, r * 0.35), 1.0)
    art.paint(art.metal(cy - r, cy + r, st["metal"]), c)


def mosque(art, st):
    sil = np.array([0.012, 0.016, 0.03])
    rim = hexc(st["glow"]) * 0.5
    base = 186

    def build(d, u):
        for mx in (110, 170):
            d.rectangle([u(mx - 3.2), u(140), u(mx + 3.2), u(base)], fill=255)
            for by in (152, 166):
                d.rectangle([u(mx - 5), u(by), u(mx + 5), u(by + 2)], fill=255)
            poly(d, u, [(mx - 3.2, 140), (mx + 3.2, 140), (mx, 129)], fill=255)
            d.line([(u(mx), u(129)), (u(mx), u(125))], fill=255, width=max(1, int(u(0.8))))
        d.rectangle([u(114), u(174), u(166), u(base)], fill=255)
        circle(d, u, 122, 175, 8, fill=255)
        circle(d, u, 158, 175, 8, fill=255)
        d.rectangle([u(126), u(162), u(154), u(base)], fill=255)
        circle(d, u, 140, 162, 14, fill=255)
        poly(d, u, [(138.5, 149), (141.5, 149), (140.6, 143), (139.4, 143)], fill=255)
        d.line([(u(140), u(143)), (u(140), u(138))], fill=255, width=max(1, int(u(0.8))))
        for (px, lean) in ((101, 3), (179, -3)):
            d.line([(u(px), u(base)), (u(px + lean / 2), u(173)), (u(px + lean), u(160))], fill=255,
                   width=max(1, int(u(1.6))))
            tx, ty = px + lean, 160
            for ang, ln in [(-165, 12), (-135, 11), (-100, 8), (-60, 11), (-25, 12), (-5, 9), (-175, 9)]:
                a = math.radians(ang)
                pts = [(tx, ty), (tx + ln * 0.5 * math.cos(a), ty + ln * 0.5 * math.sin(a) - 2.2),
                       (tx + ln * math.cos(a), ty + ln * math.sin(a) + 3.5)]
                d.line([(u(x), u(y)) for x, y in pts], fill=255, width=max(1, int(u(1.4))))
    m = art.mask(build)
    # rim light on the upper edges
    edge = np.clip(m - np.roll(m, SS * 2, 0), 0, 1)
    art.paint(sil, m)
    art.add(rim, art.blur(edge, 0.5), 0.9)
    # lit windows with bloom
    win = art.mask(lambda d, u: [d.rectangle([u(x), u(y), u(x + w), u(y + h)], fill=255) for (x, y, w, h) in
                                 [(129, 167, 1.8, 3.6), (134, 167, 1.8, 3.6), (144.2, 167, 1.8, 3.6), (149.2, 167, 1.8, 3.6)]
                                 + [(x, 179, 1.8, 3.6) for x in range(117, 166, 6) if abs(x - 140) > 5]
                                 + [(110, 145, 0.9, 2.6), (170, 145, 0.9, 2.6), (110, 158, 0.9, 2.6), (170, 158, 0.9, 2.6),
                                    (110, 171, 0.9, 2.6), (170, 171, 0.9, 2.6)]])
    gate = art.mask(lambda d, u: (d.rectangle([u(137.2), u(177), u(142.8), u(186)], fill=255),
                                  circle(d, u, 140, 177, 2.8, fill=255)))
    warm = np.array([1.0, 0.76, 0.38])
    art.add(warm * 0.8, art.blur(win + gate, 2.2), 1.2)
    art.paint(warm, np.clip(win + gate, 0, 1))
    crescent(art, st, 140, 136, 2.2)
    # water: mirrored, rippled and darkened reflection of the scene above the shore line
    water = art.mask(lambda d, u: d.rectangle([u(96), u(base), u(184), u(212)], fill=255))
    yb = int(art.u(base))
    depth = int(art.u(26))
    src = art.rgb[max(0, yb - depth):yb][::-1].copy()
    rows = np.arange(src.shape[0])
    shift = (np.sin(rows / art.u(1.1)) * art.u(0.9) * (rows / max(1, depth))).astype(int)
    for i, sh in enumerate(shift):
        src[i] = np.roll(src[i], sh, axis=0)
    fade = np.linspace(0.55, 0.12, src.shape[0])[:, None, None]
    refl = art.rgb.copy()
    end = min(art.n, yb + src.shape[0])
    refl[yb:end] = src[: end - yb] * fade[: end - yb] + hexc(st["sky"][0]) * (1 - fade[: end - yb]) * 0.6
    art.paint(refl, water)
    # a few horizontal glints
    glint = art.mask(lambda d, u: [d.line([(u(x), u(y)), (u(x + ln), u(y))], fill=255, width=max(1, int(u(0.6))))
                                   for x, y, ln in [(124, 191, 5), (133, 191, 4), (143, 192, 5), (152, 191, 4),
                                                    (128, 196, 7), (141, 197, 6), (136, 202, 6)]])
    art.add(warm * 0.6, glint, 0.9)


def rosette(art, st, cx, cy, simple=False):
    metal = art.metal(cy - 34, cy + 34, st["metal"])
    for r, w in ((34, 1.2), (25, 0.9), (16, 0.9), (7, 0.8))[: (2 if simple else 4)]:
        pts = star8(cx, cy, r)
        m = art.mask(lambda d, u, pts=pts, w=w: d.line([(u(x), u(y)) for x, y in pts + pts[:1]], fill=255,
                                                        width=max(1, int(u(w)))))
        art.add(hexc(st["glow"]) * 0.4, art.blur(m, 1.5), 0.8)
        art.paint(metal, m)
    if not simple:
        art.paint(metal, art.mask(lambda d, u: circle(d, u, cx, cy, 2.5, fill=255)))


def chapter_ring(art, st):
    r0, r1 = hexc(st["ring"][0]), hexc(st["ring"][1])
    band = art.mask(lambda d, u: (circle(d, u, 140, 140, 140, fill=255), circle(d, u, 140, 140, 127, fill=0)))
    ang = np.arctan2(art.y - 140, art.x - 140)
    brushed = 0.5 + 0.5 * np.cos(2 * ang + 0.6)
    ring = r1 + (r0 - r1) * brushed[..., None]
    ring = np.clip(ring + (art.noise(0.5, 17) - 0.5)[..., None] * 0.02, 0, 1)
    art.paint(ring, band)
    # inner shadow under the bezel
    edge = art.mask(lambda d, u: circle(d, u, 140, 140, 127, outline=255, width=max(1, int(u(1.0)))))
    art.paint(np.zeros(3), art.blur(edge, 2.5), 0.6)
    metal = art.metal(0, 280, st["metal"])
    for r, w in ((127.2, 0.9), (139.0, 1.2)):
        m = art.mask(lambda d, u, r=r, w=w: circle(d, u, 140, 140, r, outline=255, width=max(1, int(u(w)))))
        art.paint(metal, m)
    # minute ticks
    tick = hexc(st["tick"])
    def ticks(d, u):
        for i in range(60):
            if i % 5:
                a = i * math.pi / 30
                p0 = (140 + L["TICK_R_IN"] * math.sin(a), 140 - L["TICK_R_IN"] * math.cos(a))
                p1 = (140 + L["TICK_R_OUT"] * math.sin(a), 140 - L["TICK_R_OUT"] * math.cos(a))
                d.line([(u(p0[0]), u(p0[1])), (u(p1[0]), u(p1[1]))], fill=255, width=max(1, int(u(1.0))))
    art.paint(tick, art.mask(ticks), 0.9)


def rot(pts, a):
    sn, cs = math.sin(a), math.cos(a)
    return [(140 + x * cs - y * sn, 140 + x * sn + y * cs) for x, y in pts]


def indices_and_numerals(art, st):
    metal = art.metal(0, 280, st["metal"])
    dark = hexc(st["metal"][2])
    left, right = [], []
    for h in range(12):
        if h % 3 == 0:
            continue
        a = h * math.pi / 6
        wi, wo, ri, ro = 2.2, 4.4, L["IDX_R_IN"] - 1, L["IDX_R_OUT"]
        left.append(rot([(-wi, -ri), (0, -ri), (0, -ro - 0.5), (-wo, -ro)], a))
        right.append(rot([(0, -ri), (wi, -ri), (wo, -ro), (0, -ro - 0.5)], a))
    whole = art.mask(lambda d, u: [poly(d, u, p, fill=255) for p in left + right])
    art.paint(np.zeros(3), art.blur(np.roll(whole, (SS, SS), (0, 1)), 1.0), 0.7)
    art.paint(metal, art.mask(lambda d, u: [poly(d, u, p, fill=255) for p in left]))
    art.paint(metal * 0.55 + dark * 0.45, art.mask(lambda d, u: [poly(d, u, p, fill=255) for p in right]))
    # numerals
    font = ImageFont.truetype(os.path.join(FONT_SRC, "BarlowSemiCondensed-Bold.ttf"), int(art.u(27)))
    for txt, a in (("12", 0), ("3", 90), ("6", 180), ("9", 270)):
        cx = 140 + L["NUM_R"] * math.sin(math.radians(a))
        cy = 140 - L["NUM_R"] * math.cos(math.radians(a))
        m = art.mask(lambda d, u, txt=txt, cx=cx, cy=cy: d.text((u(cx), u(cy)), txt, font=font, fill=255, anchor="mm"))
        art.paint(np.zeros(3), art.blur(np.roll(m, (SS, SS), (0, 1)), 1.2), 0.8)
        art.add(hexc(st["metal"][0]) * 0.25, art.blur(m, 2.0), 0.7)
        art.paint(art.metal(cy - 11, cy + 11, st["metal"]), m)
        hi = np.clip(m - np.roll(m, SS, 0), 0, 1)
        art.add(np.ones(3) * 0.35, hi, 1.0)


def gauge_recesses(art, st):
    rc0, rc1 = hexc(st["recess"][0]), hexc(st["recess"][1])
    track = hexc(st["track"])
    for (cx, cy) in gauge_centres():
        r = L["GAUGE_DISC_R"]
        outer = art.mask(lambda d, u, cx=cx, cy=cy: circle(d, u, cx, cy, r + 1.6, fill=255))
        disc = art.mask(lambda d, u, cx=cx, cy=cy: circle(d, u, cx, cy, r, fill=255))
        bezel = np.clip(outer - disc, 0, 1)
        art.paint(np.zeros(3), np.clip(art.blur(outer, 2.5) - disc, 0, 1), 0.55)  # drop shadow outside
        art.paint(art.metal(cy - r - 2, cy + r + 2, st["metal"]), bezel)         # metal bezel ring
        art.paint(art.radial(cx, cy - 6, r * 1.3, rc0, rc1), disc, 0.72)          # smoked-glass recess
        top = np.clip(disc - np.roll(disc, SS * 3, 0), 0, 1)
        art.paint(np.zeros(3), art.blur(top, 2.0) * disc, 0.5)                   # inner shadow
        tr = art.mask(lambda d, u, cx=cx, cy=cy: circle(d, u, cx, cy, L["GAUGE_R"] + L["GAUGE_PEN"] / 2.0,
                                                         outline=255, width=max(1, int(u(L["GAUGE_PEN"])))))
        art.paint(track, tr, 0.9)


def glass_panel(art, st, pts, y0, y1, radius=None, rect=None):
    if rect is not None:
        x0, ya, x1, yb = rect
        m = art.mask(lambda d, u: d.rounded_rectangle([u(x0), u(ya), u(x1), u(yb)], radius=u(radius), fill=255))
        line = art.mask(lambda d, u: d.rounded_rectangle([u(x0), u(ya), u(x1), u(yb)], radius=u(radius), outline=255,
                                                         width=max(1, int(u(1.0)))))
    else:
        m = art.mask(lambda d, u: poly(d, u, pts, fill=255))
        line = art.mask(lambda d, u: d.line([(u(x), u(y)) for x, y in pts + pts[:1]], fill=255, width=max(1, int(u(1.0)))))
    p0, p1 = hexc(st["panel"][0]), hexc(st["panel"][1])
    art.paint(np.zeros(3), art.blur(m, 2.5), 0.5)
    art.paint(art.vertical(y0, y1, p0, p1), m, 0.93)
    sheen = np.clip(m - np.roll(m, SS * 2, 0), 0, 1)
    art.add(np.ones(3) * 0.18, art.blur(sheen, 0.6), 1.0)
    art.add(hexc(st["glow"]) * 0.3, art.blur(line, 1.6), 0.7)
    art.paint(art.metal(y0, y1, st["metal"]), line)


def cartouches(art, st):
    w, h, y0 = L["PANEL_W"], L["PANEL_H"], L["PANEL_Y0"]
    for sgn in (-1, 1):
        x0 = 140 + sgn * L["PANEL_DX"] - w / 2.0
        glass_panel(art, st, None, y0, y0 + h, radius=7, rect=(x0, y0, x0 + w, y0 + h))
    # no Ayah cartouche: a soft, shapeless shadow keeps the verse readable over the pattern
    shade = art.mask(lambda d, u: d.ellipse([u(72), u(L["AYAH_Y"] - 16), u(208), u(L["AYAH_REF_Y"] + 9)], fill=255))
    art.paint(np.zeros(3), art.blur(shade, 9), 0.55)


def fixed_icons(art, st, hub_diamond=True):
    """Crescent under 12, sunrise/sunset suns, cartouche icons, hub diamond."""
    crescent(art, st, 140, L["CRESCENT_Y"], 6)
    metal = art.metal(80, 120, st["metal"])
    for sgn, rising in ((-1, True), (1, False)):
        x, y = 140 + sgn * L["SUN_DX"], L["SUN_ICON_Y"]

        def sun(d, u, x=x, y=y, rising=rising):
            d.pieslice([u(x - 5), u(y + 2 - 5), u(x + 5), u(y + 2 + 5)], 180, 360, fill=255)
            d.line([(u(x - 8.5), u(y + 2.6)), (u(x + 8.5), u(y + 2.6))], fill=255, width=max(1, int(u(1.0))))
            for ang in (20, 55, 90, 125, 160):
                a = math.radians(ang)
                d.line([(u(x + 7 * math.cos(a)), u(y + 2 - 7 * math.sin(a))),
                        (u(x + 9.5 * math.cos(a)), u(y + 2 - 9.5 * math.sin(a)))], fill=255, width=max(1, int(u(1.0))))
            if rising:
                poly(d, u, [(x, y + 4), (x - 2.2, y + 7), (x + 2.2, y + 7)], fill=255)
            else:
                poly(d, u, [(x, y + 8), (x - 2.2, y + 5), (x + 2.2, y + 5)], fill=255)
        m = art.mask(sun)
        art.add(hexc("#ffb347") * 0.5, art.blur(m, 2.0), 0.8)
        art.paint(metal, m)
    # cartouche icons
    iy = L["PANEL_Y0"] + L["PANEL_H"] / 2.0
    lx = 140 - L["PANEL_DX"] - L["PANEL_W"] / 2.0 + 11
    rx = 140 + L["PANEL_DX"] - L["PANEL_W"] / 2.0 + 11
    m = art.mask(lambda d, u: (circle(d, u, lx, iy - 1, 4.2, fill=255),
                               d.rectangle([u(lx - 5.5), u(iy - 1), u(lx + 5.5), u(iy + 6)], fill=255),
                               d.line([(u(lx), u(iy - 5)), (u(lx), u(iy - 8.5))], fill=255, width=max(1, int(u(1.0))))))
    art.add(hexc(st["glow"]) * 0.3, art.blur(m, 1.5), 0.8)
    art.paint(art.metal(iy - 8, iy + 6, st["metal"]), m)
    crescent(art, st, rx, iy, 5)
    if not hub_diamond:
        return
    # hub diamond
    dy = L["HUB_DIAMOND_Y"]
    art.paint(art.metal(dy - 4, dy + 4, st["metal"]),
              art.mask(lambda d, u: poly(d, u, [(140, dy - 4.5), (144.5, dy), (140, dy + 4.5), (135.5, dy)], fill=255)))


# ------------------------------------------------------------------ illustrated background
ILLUSTRATION = os.path.join(ROOT, "tools", "art-src", "mosque-night.png")   # supplied by the owner
ILLU_CENTRE = (626.0, 617.0)
ILLU_RADIUS = 623.0

# colour grading of the illustration per style: (deep, mid, light) for the blue night tones and
# the colour the warm golden lights are pulled towards (None = keep them golden)
GRADES = [
    None,                                                                   # Luxury Blue: original
    (("#050403", "#2d2210", "#8a6a34"), None),                              # Royal Gold
    (("#010c08", "#0b3b28", "#5fae86"), None),                              # Emerald Night
    (("#0e0207", "#4a0f26", "#c2708c"), "#ffc7b0"),                         # Burgundy Royale (rose gold)
    (("#020814", "#1b3a63", "#b8d4ee"), "#e8eef5"),                         # Ice Silver
    (("#040506", "#24282d", "#a9b0b8"), "#e6e8ea"),                         # Stealth
]


def layer_illustration(art, style_index):
    img = Image.open(ILLUSTRATION).convert("RGB")
    s = 280.0 / (2 * ILLU_RADIUS)
    left, top = ILLU_CENTRE[0] - ILLU_RADIUS, ILLU_CENTRE[1] - ILLU_RADIUS
    crop = img.crop((int(left), int(top), int(left + 2 * ILLU_RADIUS), int(top + 2 * ILLU_RADIUS)))
    a = np.asarray(crop.resize((art.n, art.n), Image.LANCZOS), dtype=np.float64) / 255.0
    g = GRADES[style_index]
    if g is not None:
        (deep, mid, light), warm = g
        deep, mid, light = hexc(deep), hexc(mid), hexc(light)
        lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
        t = np.clip(lum / 0.6, 0, 1)[..., None]
        mapped = np.where(t < 0.5, deep + (mid - deep) * (t * 2), mid + (light - mid) * ((t - 0.5) * 2))
        blue = np.clip((a[..., 2] - a[..., 0]) / 0.25 + 0.15, 0, 1)[..., None]   # night / sky tones
        out = a * (1 - blue) + mapped * blue
        if warm is not None:
            wv = hexc(warm)
            warmth = np.clip((a[..., 0] - a[..., 2]) / 0.3, 0, 1)[..., None]
            out = out * (1 - warmth) + (lum[..., None] * 1.15 * wv) * warmth
        a = np.clip(out, 0, 1)
    art.rgb = a


def legibility_shadows(art):
    """Soft, shapeless shadows under the live texts so they stay readable over the illustration."""
    for (x0, y0, x1, y1, r, alpha) in [
            (112, 44, 168, 100, 8, 0.55),                    # date block
            (70, 100, 210, 124, 7, 0.55),                    # Hijri date
            (24, 88, 72, 120, 7, 0.5), (208, 88, 256, 120, 7, 0.5),   # sunrise / sunset
            (70, 206, 210, L["AYAH_REF_Y"] + 10, 9, 0.6)]:   # Ayah
        m = art.mask(lambda d, u, b=(x0, y0, x1, y1): d.ellipse([u(b[0]), u(b[1]), u(b[2]), u(b[3])], fill=255))
        art.paint(np.zeros(3), art.blur(m, r), alpha)


def render(size, style_index, bg):
    st = STYLES[style_index]
    art = Art(size)
    if bg == "mosque":
        layer_illustration(art, style_index)
        legibility_shadows(art)
    else:
        layer_base(art, st)
        layer_pattern(art, st, bg)
        # soft vignette towards the bezel
        vig = np.clip((np.hypot(art.x - 140, art.y - 140) - 70) / 60.0, 0, 1) ** 2
        art.rgb *= (1 - 0.35 * vig)[..., None]
        arch_window(art, st, bg)
    chapter_ring(art, st)
    gauge_recesses(art, st)
    cartouches(art, st)
    indices_and_numerals(art, st)
    fixed_icons(art, st, hub_diamond=(bg != "mosque"))
    # outside the round display: black
    outside = art.mask(lambda d, u: circle(d, u, 140, 140, 140, fill=255))
    art.rgb *= outside[..., None]
    return art.finish()


# ------------------------------------------------------------------ MIP palette
MIP = np.array([(r, g, b) for r in (0, 85, 170, 255) for g in (0, 85, 170, 255) for b in (0, 85, 170, 255)],
               dtype=np.uint8)


def to_mip(img):
    pal = Image.new("P", (1, 1))
    flat = MIP.flatten().tolist() + [0] * (768 - MIP.size)
    pal.putpalette(flat)
    return img.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG)


def render_for_device(size, style_index, bg):
    img = render(size, style_index, bg)
    return to_mip(img) if size < AMOLED_FROM else img


if __name__ == "__main__":
    import sys
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 454
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/hd.png"
    style = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    bg = sys.argv[4] if len(sys.argv) > 4 else "mosque"
    render_for_device(size, style, bg).convert("RGB").save(out)
    print(out)
