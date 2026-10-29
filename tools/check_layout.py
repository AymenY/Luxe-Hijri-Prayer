#!/usr/bin/env python3
"""Geometric validation of the 280 x 280 circular layout with worst-case content.

For every text element the bounding box is computed from the real bitmap-font metrics
(resources/fonts/*.fnt) using the widest strings that can occur in English and French, and
checked against:
  * the circular safe area (radius Layout.SAFE_R around the centre),
  * the gauge discs and other elements it must not overlap,
  * the inside of the gauge rings (values) and the open bottom of the rings (labels).
Exit status is non-zero when a check fails.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import face  # noqa: E402

L = face.L
ROOT = face.ROOT
failures = []
report = []


def text_box(fontname, text, cx, cy, just="center"):
    f = face.font(fontname)
    w = f.width(text)
    # ink extent: glyph boxes
    x0 = cx - w // 2 if just == "center" else cx
    top = cy - f.height // 2
    ys = []
    x = x0
    xs = []
    for ch in text:
        g = f.chars.get(ord(ch), f.chars[32])
        if g["width"]:
            ys += [top + g["yoffset"], top + g["yoffset"] + g["height"]]
            xs += [x + g["xoffset"], x + g["xoffset"] + g["width"]]
        x += g["xadvance"]
    return (min(xs), min(ys), max(xs), max(ys))


def corners_inside(box, r, name):
    worst = max(math.hypot(x - L.CX, y - L.CY) for x in (box[0], box[2]) for y in (box[1], box[3]))
    ok = worst <= r
    report.append("| %s | (%d,%d)-(%d,%d) | %.1f | %s |" % (name, *box, worst, "ok" if ok else "OUTSIDE"))
    if not ok:
        failures.append("%s outside the safe circle (%.1f > %d)" % (name, worst, r))


def box_circle_gap(box, cx, cy, r):
    nx = min(max(cx, box[0]), box[2])
    ny = min(max(cy, box[1]), box[3])
    return math.hypot(nx - cx, ny - cy) - r


def boxes_overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def langs():
    return {"eng": face.strings("eng"), "fre": face.strings("fre")}


def widest(fontname, cands):
    f = face.font(fontname)
    return max(cands, key=f.width)


def main():
    S = langs()
    disc_r = L.GAUGE_DISC_R
    gauges = [(L.CX - L.GAUGE_DX, L.GAUGE_TOP_Y), (L.CX + L.GAUGE_DX, L.GAUGE_TOP_Y),
              (L.CX - L.GAUGE_DX, L.GAUGE_BOT_Y), (L.CX + L.GAUGE_DX, L.GAUGE_BOT_Y)]
    report.append("| Element (worst case) | Ink box | Max distance from centre | Safe area |")
    report.append("|---|---|---|---|")
    boxes = {}
    for lang, s in S.items():
        greg = widest("luxe_s", ["%s 28 %s 2026" % (s["Day%d" % d], s["Month%d" % m]) for d in range(7)
                                 for m in range(1, 13)])
        hijri = widest("luxe_s", ["30 %s 1448 %s" % (s["Hijri%d" % m], s["HijriSuffix"]) for m in range(1, 13)])
        nxt = widest("luxe_m", ["%s %s" % (s["Prayer%d" % p], t) for p in (0, 2, 3, 5, 6)
                                for t in ("23h59", "59m")] + [s["SetLocation"]])
        boxes["greg-" + lang] = text_box("luxe_s", greg, L.CX, L.GREG_Y)
        boxes["hijri-" + lang] = text_box("luxe_s", hijri, L.CX, L.HIJRI_Y)
        boxes["next-" + lang] = text_box("luxe_m", nxt, L.CX, L.NEXT_Y)
        report_names = {"greg-" + lang: greg, "hijri-" + lang: hijri, "next-" + lang: nxt}
        for k, v in report_names.items():
            corners_inside(boxes[k], L.SAFE_R, "%s: \"%s\"" % (k, v))
        # gauge units must fit the open bottom of the ring (icons are drawn within 13 x 12 px)
        for key in ["LabelCalories", "LabelBattery", "LabelKm", "LabelMi"]:
            b = text_box("luxe_xxs", s[key], 0, L.GAUGE_ICON_DY)
            end_x = L.GAUGE_R * math.sin(math.pi / 4) - L.GAUGE_PEN / 2.0 - 1
            end_y = L.GAUGE_R * math.cos(math.pi / 4) + L.GAUGE_PEN / 2.0
            if max(-b[0], b[2]) > end_x and b[1] < end_y:
                failures.append("gauge unit %s/%s (%d px wide) touches the ring ends" % (lang, s[key], b[2] - b[0]))
            if math.hypot(max(-b[0], b[2]), b[3]) > L.GAUGE_DISC_R + 1:
                failures.append("gauge unit %s/%s leaves the gauge disc" % (lang, s[key]))

    # schedule cells (24 h and 12 h worst cases), sun groups
    cell = L.SCHED_W // 5
    x0 = L.CX - L.SCHED_W // 2 + cell // 2
    for k in range(5):
        b = text_box("luxe_xs", "00:00", x0 + k * cell, L.SCHED_Y)
        boxes["sched-%d" % k] = (b[0], b[1], b[2], b[3] + 4)  # + underline
        corners_inside(boxes["sched-%d" % k], L.SAFE_R, "schedule cell %d \"00:00\"" % k)
    tw = face.font("luxe_xs").width("00:00")
    gw = L.SUN_ICON_W + 3 + tw
    tb = text_box("luxe_xs", "00:00", 0, L.SUN_Y)
    boxes["sunrise"] = (L.CX - L.SUN_GAP // 2 - gw, min(tb[1], L.SUN_Y - 7), L.CX - L.SUN_GAP // 2, max(tb[3], L.SUN_Y + 5))
    boxes["sunset"] = (L.CX + L.SUN_GAP // 2, min(tb[1], L.SUN_Y - 7), L.CX + L.SUN_GAP // 2 + gw, max(tb[3], L.SUN_Y + 5))
    corners_inside(boxes["sunrise"], L.SAFE_R, "sunrise group")
    corners_inside(boxes["sunset"], L.SAFE_R, "sunset group")

    # Ayah glyphs
    ayah = json.load(open(os.path.join(ROOT, "tools", "assets-report.json")))["ayah"]
    for ref, a in ayah.items():
        b = (L.CX - a["w"] // 2, L.AYAH_Y - a["h"] // 2, L.CX + (a["w"] + 1) // 2, L.AYAH_Y + (a["h"] + 1) // 2)
        boxes["ayah " + ref] = b
        corners_inside(b, 124, "Ayah %s (%dx%d px, %d px font)" % (ref, a["w"], a["h"], a["px"]))
        if b[1] <= L.CW_12_BOTTOM if hasattr(L, "CW_12_BOTTOM") else b[1] <= L.CY - L.IDX_R_OUT + (L.IDX_R_OUT - L.IDX_CARD_R_IN):
            failures.append("Ayah %s reaches the 12 o'clock batons" % ref)

    # gauges inside the safe circle
    for i, (gx, gy) in enumerate(gauges):
        far = math.hypot(gx - L.CX, gy - L.CY) + disc_r
        report.append("| gauge %d disc | centre (%d,%d) r=%d | %.1f | %s |" % (i + 1, gx, gy, disc_r, far,
                                                                            "ok" if far <= L.SAFE_R else "OUTSIDE"))
        if far > L.SAFE_R:
            failures.append("gauge %d outside the safe circle" % (i + 1))

    # gauge values must fit inside the ring
    inner = 2 * (L.GAUGE_R - L.GAUGE_PEN // 2) - 2
    for v in ["9999", "99.9k", "999k", "--", "200", "100", "88.8", "100%"]:
        w = min(face.font(f).width(v) for f in ("luxe_l", "luxe_m", "luxe_s"))
        if w > inner:
            failures.append("gauge value '%s' (%d px) wider than the ring interior (%d px)" % (v, w, inner))
        if face.font("luxe_m").width(v) > inner:
            report.append("| gauge value \"%s\" | steps down to the smaller font | | |" % v)

    # no element may overlap a gauge disc or another element
    for name, b in boxes.items():
        for i, (gx, gy) in enumerate(gauges):
            gap = box_circle_gap(b, gx, gy, disc_r)
            if gap < 1:
                failures.append("%s overlaps gauge %d disc (gap %.1f px)" % (name, i + 1, gap))
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            same_group = a.split("-")[0] == b.split("-")[0] or (a.startswith("ayah") and b.startswith("ayah"))
            if not same_group and boxes_overlap(boxes[a], boxes[b]):
                failures.append("%s overlaps %s" % (a, b))

    # seconds hand and indices
    if L.SEC_LEN >= L.IDX_R_IN + 2:
        failures.append("seconds hand runs into the hour indices")
    report.append("")
    report.append("Seconds hand: %d px from the centre (%.0f%% of the dial radius), tail %d px." %
                  (L.SEC_LEN, 100.0 * L.SEC_LEN / L.CX, L.SEC_TAIL))
    out = os.path.join(ROOT, "docs", "layout-report.md")
    with open(out, "w") as fh:
        fh.write("# Layout validation report\n\nGenerated by `tools/check_layout.py` (safe radius %d px).\n\n"
                 % L.SAFE_R + "\n".join(report) + "\n\n## Result\n\n**%s**\n" %
                 ("PASS" if not failures else "FAIL") + "".join("* %s\n" % f for f in failures))
    for f in failures:
        print("FAIL:", f)
    print("layout check:", "PASS" if not failures else "FAIL", "-", out)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
