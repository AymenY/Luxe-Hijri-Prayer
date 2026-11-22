"""Shared geometry (280-px dial units) for the HD artwork (render_hd.py) and the vector fallback
(build_assets.py): the Moorish window of the dial.

The window is a keyhole-shaped multi-foil arch: straight sides between the side gauges, shoulders
that pass under the upper gauges, a narrow neck between them, and a cusped (lobed) pointed arch
whose apex sits under the 12 numeral.
"""
import math


def window_points(L, inset=0.0):
    x0, x1 = L["WINDOW_X0"] + inset, L["WINDOW_X1"] - inset
    nx0, nx1 = L["WINDOW_NECK_X0"] + inset, L["WINDOW_NECK_X1"] - inset
    top, bottom = L["WINDOW_TOP"] + inset, L["WINDOW_BOTTOM"]
    sh_y, nk_y = L["WINDOW_SHOULDER_Y"] + inset * 0.5, L["WINDOW_NECK_Y"] + inset * 0.5

    left = [(x0, bottom), (x0, sh_y)]
    # shoulder: quarter ellipse from the side to the neck
    for i in range(1, 9):
        t = i / 8.0 * math.pi / 2
        left.append((x0 + (nx0 - x0) * math.sin(t), sh_y - (sh_y - nk_y) * (1 - math.cos(t))))
    # cusped pointed arch from the neck to the apex: a pointed (two-centred) curve with three
    # lobes carved into it
    half = 140 - nx0
    height = nk_y - top
    rad = (half * half + height * height) / (2.0 * half)       # circle through neck and apex
    cx = nx0 + rad
    a0 = math.pi
    a1 = math.atan2(top - nk_y, 140 - cx)
    if a1 < a0:
        a1 += 2 * math.pi
    n = 60
    lobes = 3
    for i in range(1, n + 1):
        t = i / float(n)
        a = a0 + (a1 - a0) * t
        r = rad - 3.2 * abs(math.sin(t * lobes * math.pi)) * (1 - t * 0.35)
        left.append((cx + r * math.cos(a), nk_y + r * math.sin(a)))
    right = [(280 - x, y) for (x, y) in reversed(left[:-1])]
    return left + right


def point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / float(yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def window_fill_parts(L):
    """The window area as convex polygons (for devices that only fill convex polygons):
    lower body, two shoulders, neck and the unlobed pointed top."""
    x0, x1 = L["WINDOW_X0"], L["WINDOW_X1"]
    nx0, nx1 = L["WINDOW_NECK_X0"], L["WINDOW_NECK_X1"]
    top, bottom = L["WINDOW_TOP"], L["WINDOW_BOTTOM"]
    sh_y, nk_y = L["WINDOW_SHOULDER_Y"], L["WINDOW_NECK_Y"]
    parts = [[(x0, sh_y), (x1, sh_y), (x1, bottom), (x0, bottom)],
             [(nx0, nk_y), (nx1, nk_y), (nx1, sh_y), (nx0, sh_y)]]
    for side in (-1, 1):
        sx, nx = (x0, nx0) if side < 0 else (x1, nx1)
        pts = [(sx, sh_y)]
        for i in range(1, 9):
            t = i / 8.0 * math.pi / 2
            pts.append((sx + (nx - sx) * math.sin(t), sh_y - (sh_y - nk_y) * (1 - math.cos(t))))
        pts.append((nx, sh_y))
        parts.append(pts)
    half = 140 - nx0
    height = nk_y - top
    rad = (half * half + height * height) / (2.0 * half)
    cx = nx0 + rad
    a0, a1 = math.pi, math.atan2(top - nk_y, 140 - cx)
    if a1 < a0:
        a1 += 2 * math.pi
    left = [(cx + rad * math.cos(a0 + (a1 - a0) * i / 12.0), nk_y + rad * math.sin(a0 + (a1 - a0) * i / 12.0))
            for i in range(13)]
    parts.append(left + [(280 - x, y) for (x, y) in reversed(left[:-1])])
    return parts
