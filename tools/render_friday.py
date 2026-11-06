#!/usr/bin/env python3
"""Friday dial (HD), shown from 00:00 until Asr on Fridays (setting FridayDesign).

A wrought-iron grille painted Sidi Bou Said blue — a diamond lattice with forged lyres in one
diamond out of two — on a dark wall, a few sprigs of jasmine and geranium along the rim, and the
hour ring (chapter ring, minute track, indices) in gold. The live content is drawn by the watch
with the Themes.FRIDAY palette; the gold numerals are those of the Royal Gold style.
Uses the layers and the Art canvas of tools/render_hd.py.
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_hd as R  # noqa: E402
from render_hd import Art, hexc  # noqa: E402

S = 62.0                     # lattice spacing (dial units)
IRON = ("#9cc8ff", "#2a6cc8", "#0b2c66")
GOLD = ("#fff2c4", "#e2b04a", "#8a5a14")
STYLE = dict(name="friday", base=("#12233f", "#03070f"), ring=("#0b1a38", "#02060f"), metal=IRON,
             glow="#000000", tick="#e6f6ff", sky=("#020717", "#1d4588"), pattern="#1b3f80",
             recess=("#081230", "#01040c"), track="#13254d", panel=("#0c1a3c", "#030914"))
RING = dict(STYLE, metal=GOLD, tick="#f3e1a8")      # the hour ring in gold


def spiral(c, r0, a0, turns, sign, n=50):
    pts = []
    for i in range(n + 1):
        t = i / float(n)
        ang = a0 + sign * t * turns * 2 * math.pi
        rr = r0 * (1 - 0.82 * t)
        pts.append((c[0] + rr * math.cos(ang), c[1] + rr * math.sin(ang)))
    return pts


def leaf(p, ang, ln, w, bend=0.25):
    """Pointed leaf (or petal) polygon from p, direction ang, length ln, half width w."""
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    side1, side2 = [], []
    for i in range(13):
        t = i / 12.0
        bx = p[0] + dx * ln * t + nx * ln * bend * t * t
        by = p[1] + dy * ln * t + ny * ln * bend * t * t
        ww = w * math.sin(math.pi * t) ** 0.7 * (1 - 0.35 * t)
        side1.append((bx + nx * ww, by + ny * ww))
        side2.append((bx - nx * ww, by - ny * ww))
    return side1 + side2[::-1]


def lattice_lines():
    out = []
    for k in range(-8, 9):
        c = 280 + k * S
        out.append(((-20, c + 20), (c + 20, -20)))          # x + y = c
        out.append(((-20 + k * S, -20), (300 + k * S, 300)))   # x - y = k S
    return out


def crossings():
    pts = [(140 + (a + b) * S / 2.0, 140 + (a - b) * S / 2.0) for a in range(-8, 9) for b in range(-8, 9)]
    return [(x, y) for x, y in pts if math.hypot(x - 140, y - 140) < 145]


def lyres():
    """Forged lyre in one diamond out of two: from the top vertex two C-scrolls open outwards and
    curl in, with a bar down to the bottom vertex."""
    paths = []
    for a in range(-8, 9):
        for b in range(-8, 9):
            cx, cy = 140 + (a + b + 1) * S / 2.0, 140 + (a - b) * S / 2.0
            if math.hypot(cx - 140, cy - 140) > 150 or int(round((cx - 140) / S + (cy - 140) / S)) % 2:
                continue
            top = (cx, cy - 0.5 * S)
            for sx in (-1, 1):
                c = (cx + sx * 0.15 * S, cy + 0.02 * S)
                start = (top[0], top[1] + 0.12 * S)
                a0 = math.atan2(start[1] - c[1], start[0] - c[0])
                paths.append([top] + spiral(c, math.hypot(start[0] - c[0], start[1] - c[1]), a0, 1.1, sx))
            paths.append([(cx, cy - 0.38 * S), (cx, cy + 0.5 * S)])
    return paths


def plants(seed=5):
    """Four short jasmine sprigs along the rim (clear of the numerals and texts) and two small
    geranium clusters near 5 and 7 o'clock."""
    rng = np.random.default_rng(seed)
    stems, leaves, jas, buds, gers, gleaves = [], [], [], [], [], []
    for (x, y), ang in [((30, 228), -0.75), ((250, 228), -2.4), ((30, 100), -1.15), ((250, 100), -1.99)]:
        pts = [(x, y)]
        for _ in range(5):
            ang += rng.uniform(-0.5, 0.5)
            x += 9 * math.cos(ang)
            y += 9 * math.sin(ang)
            pts.append((x, y))
        stems.append(pts)
        for i, (px1, py1) in enumerate(pts[1:], 1):
            px0, py0 = pts[i - 1]
            t = math.atan2(py1 - py0, px1 - px0)
            side = 1 if i % 2 else -1
            leaves.append(leaf((px1, py1), t + side * 0.8, rng.uniform(7, 9), 2.4, bend=0.2 * side))
            if i % 2 == 0:
                jas.append((px1 + 6 * math.cos(t - side * 1.2), py1 + 6 * math.sin(t - side * 1.2),
                            rng.uniform(4.0, 4.8), rng.uniform(0, 1.2)))
            if i == 3:
                buds.append((px1 + 4 * math.cos(t + side * 1.6), py1 + 4 * math.sin(t + side * 1.6)))
        jas.append((pts[-1][0], pts[-1][1], 4.8, rng.uniform(0, 1.2)))
    for (gx, gy) in [(54, 236), (226, 236)]:
        for k in range(2):
            a = math.radians(200 + 140 * k) if gx < 140 else math.radians(-20 - 140 * k)
            gleaves.append((gx + 8 * math.cos(a), gy + 8 * math.sin(a) + 3, 6.5))
        for k in range(7):
            r, a = rng.uniform(0, 5), rng.uniform(0, 2 * math.pi)
            gers.append((gx + r * math.cos(a), gy - 3 + r * math.sin(a), rng.uniform(2.4, 2.9)))
    return stems, leaves, jas, buds, gers, gleaves


def layer_grille(art):
    w = lambda x: max(1, int(art.u(x)))
    bars = art.mask(lambda d, u: [d.line([(u(a[0]), u(a[1])), (u(b[0]), u(b[1]))], fill=255, width=w(1.8))
                                  for a, b in lattice_lines()])
    curls = art.mask(lambda d, u: [d.line([(u(x), u(y)) for x, y in pts], fill=255, width=w(1.1), joint="curve")
                                   for pts in lyres()])
    cross = crossings()
    collars = art.mask(lambda d, u: [d.polygon([(u(x), u(y - 2.4)), (u(x + 2.4), u(y)), (u(x), u(y + 2.4)),
                                                (u(x - 2.4), u(y))], fill=255) for x, y in cross])
    iron = np.clip(bars + curls + collars, 0, 1)
    art.paint(np.zeros(3), art.blur(np.roll(iron, (int(art.u(1.2)), int(art.u(1.2))), (0, 1)), 1.0), 0.5)
    art.paint(art.metal(0, 280, IRON) * 0.7, iron, 0.75)
    art.paint(hexc(IRON[0]), np.clip(iron - np.roll(iron, int(art.u(1)), 0), 0, 1), 0.25)
    art.paint(hexc("#d8ecff"), art.mask(lambda d, u: [R.circle(d, u, x, y, 1.0, fill=255) for x, y in cross]), 0.5)


def layer_plants(art):
    w = lambda x: max(1, int(art.u(x)))
    stems, leaves, jas, buds, gers, gleaves = plants()
    stem_m = art.mask(lambda d, u: [d.line([(u(x), u(y)) for x, y in pts], fill=255, width=w(1.3), joint="curve")
                                    for pts in stems])
    leaf_m = art.mask(lambda d, u: [d.polygon([(u(x), u(y)) for x, y in pts], fill=255) for pts in leaves])
    vein_m = art.mask(lambda d, u: [d.line([(u(x), u(y)) for x, y in pts[1:11]], fill=255, width=w(0.5)) for pts in leaves])

    def geranium_leaves(d, u):
        for x, y, r in gleaves:
            pts = [(x + r * (1 + 0.1 * math.cos(9 * t)) * math.cos(t), y + r * (1 + 0.1 * math.cos(9 * t)) * math.sin(t))
                   for t in np.linspace(0, 2 * math.pi, 60)]
            d.polygon([(u(a), u(b)) for a, b in pts], fill=255)

    def jasmine(d, u):
        for x, y, r, rot in jas:
            for i in range(5):
                pts = leaf((x, y), rot + i * 2 * math.pi / 5, r, r * 0.3, bend=0.15)
                d.polygon([(u(px), u(py)) for px, py in pts], fill=255)

    def geranium(d, u):
        for x, y, r in gers:
            for i in range(5):
                a = i * 2 * math.pi / 5
                R.circle(d, u, x + r * 0.5 * math.cos(a), y + r * 0.5 * math.sin(a), r * 0.5, fill=255)

    gl_m = art.mask(geranium_leaves)
    gl_zone = art.mask(lambda d, u: [R.circle(d, u, x, y, r * 0.55, outline=255, width=w(1.3)) for x, y, r in gleaves])
    jas_m = art.mask(jasmine)
    jc_m = art.mask(lambda d, u: [R.circle(d, u, x, y, 0.9, fill=255) for x, y, r, rot in jas])
    bud_m = art.mask(lambda d, u: [d.ellipse([u(x - 1.3), u(y - 2.4), u(x + 1.3), u(y + 2.4)], fill=255) for x, y in buds])
    ger_m = art.mask(geranium)
    gc_m = art.mask(lambda d, u: [R.circle(d, u, x, y, r * 0.28, fill=255) for x, y, r in gers])
    plant = np.clip(stem_m + leaf_m + gl_m + jas_m + bud_m + ger_m, 0, 1)
    art.paint(np.zeros(3), art.blur(np.roll(plant, (int(art.u(1.2)), int(art.u(1.2))), (0, 1)), 1.0), 0.6)
    art.paint(hexc("#2f6b1e"), stem_m)
    art.paint(art.vertical(0, 280, hexc("#6fcf4a"), hexc("#1f7a2c")), gl_m)
    art.paint(hexc("#174f1c"), gl_zone * gl_m, 0.7)
    art.paint(art.vertical(0, 280, hexc("#8be05a"), hexc("#2a8f35")), leaf_m)
    art.paint(hexc("#1c5a1f"), vein_m * leaf_m, 0.7)
    art.paint(hexc("#ff2a3a"), ger_m)
    art.paint(hexc("#ffb0b8"), gc_m * ger_m, 0.8)
    art.paint(hexc("#ffc9d8"), bud_m)
    art.paint(hexc("#ffffff"), jas_m)
    art.paint(hexc("#ffd84a"), jc_m)


def render(size):
    art = Art(size)
    R.layer_base(art, STYLE)
    art.rgb = np.clip(art.rgb + (art.fractal(3, 5, 30) - 0.5)[..., None] * 0.05, 0, 1)   # plaster wall
    layer_grille(art)
    layer_plants(art)
    vig = np.clip((np.hypot(art.x - 140, art.y - 140) - 70) / 60.0, 0, 1) ** 2
    art.rgb *= (1 - 0.2 * vig)[..., None]
    R.legibility_shadows(art)
    R.chapter_ring(art, RING)
    R.gauge_recesses(art, STYLE)
    R.cartouches(art, STYLE)
    R.indices(art, RING)
    R.fixed_icons(art, STYLE, hub_diamond=True)
    outside = art.mask(lambda d, u: R.circle(d, u, 140, 140, 140, fill=255))
    art.rgb *= outside[..., None]
    return art.finish()


if __name__ == "__main__":
    size = int(sys.argv[1]) if len(sys.argv) > 1 else 280
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/friday.png"
    img = render(size)
    (R.to_mip(R.mip_grade(img)) if size < R.AMOLED_FROM else img).convert("RGB").save(out)
    print(out)
