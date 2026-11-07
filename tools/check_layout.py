#!/usr/bin/env python3
"""Geometric validation of the round layout, for every supported screen size, with
worst-case English and French content.

For each size the bounding boxes are computed from that size's bitmap fonts
(resources[-round-WxH]/fonts) and the scaled layout, and checked against:
  * the circular safe area (Layout.SAFE_R, scaled),
  * the gauge discs, the prayer cartouches and every other text element,
  * the inside of the gauge rings (icon, value, label) and of the cartouches.
Exit status is non-zero when a check fails. Report: docs/layout-report.md.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import face  # noqa: E402

L = face.L
ROOT = face.ROOT


class Check:
    def __init__(self, size, fam="luxe"):
        self.fam = fam
        self.size = size
        self.k = size / 280.0
        self.c = size / 2.0
        self.fail = []
        self.boxes = {}

    def p(self, v):
        return int(math.floor(v * self.k + 0.5))

    def text_box(self, fontname, text, cx, cy):
        f = face.font(fontname.replace("luxe_", self.fam + "_") if fontname[5:] in ("l", "m", "s", "xs", "dl", "dxs") else fontname,
                      self.size)
        w = f.width(text)
        x = cx - w // 2
        top = cy - f.height // 2
        xs, ys = [], []
        for ch in text:
            g = f.chars.get(ord(ch), f.chars[32])
            if g["width"]:
                xs += [x + g["xoffset"], x + g["xoffset"] + g["width"]]
                ys += [top + g["yoffset"], top + g["yoffset"] + g["height"]]
            x += g["xadvance"]
        return (min(xs), min(ys), max(xs), max(ys))

    def inside(self, box, name, r=None):
        r = (r or L.SAFE_R) * self.k
        worst = max(math.hypot(x - self.c, y - self.c) for x in (box[0], box[2]) for y in (box[1], box[3]))
        if worst > r:
            self.fail.append("%s outside the safe circle (%.1f > %.1f px)" % (name, worst, r))

    def add(self, name, box, check_circle=True):
        self.boxes[name] = box
        if check_circle:
            self.inside(box, name)


FAM = "luxe"


def fontname_for(fontname):
    return fontname.replace("luxe_", FAM + "_") if fontname[5:] in ("l", "m", "s", "xs", "dl", "dxs") else fontname


def widest(fontname, size, cands):
    f = face.font(fontname_for(fontname), size)
    return max(cands, key=f.width)


def box_circle_gap(box, cx, cy, r):
    nx = min(max(cx, box[0]), box[2])
    ny = min(max(cy, box[1]), box[3])
    return math.hypot(nx - cx, ny - cy) - r


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def check_size(size, report):
    ck = Check(size, FAM)
    p = ck.p
    S = {"eng": face.strings("eng"), "fre": face.strings("fre")}
    gauges = [(p(140 - L.GAUGE_UP_DX), p(L.GAUGE_UP_Y)), (p(140 + L.GAUGE_UP_DX), p(L.GAUGE_UP_Y)),
              (p(140 - L.GAUGE_SIDE_DX), p(L.GAUGE_SIDE_Y)), (p(140 + L.GAUGE_SIDE_DX), p(L.GAUGE_SIDE_Y))]
    disc = p(L.GAUGE_DISC_R)
    for i, (gx, gy) in enumerate(gauges):
        far = math.hypot(gx - ck.c, gy - ck.c) + disc
        if far > L.SAFE_R * ck.k:
            ck.fail.append("gauge %d disc outside the safe circle" % (i + 1))

    # numerals
    for name, txt, a in (("num12", "12", 0), ("num3", "3", 90), ("num6", "6", 180), ("num9", "9", 270)):
        x = int(math.floor(ck.c + L.NUM_R * ck.k * math.sin(math.radians(a)) + 0.5))
        y = int(math.floor(ck.c - L.NUM_R * ck.k * math.cos(math.radians(a)) + 0.5))
        ck.add(name, ck.text_box("luxe_num", txt, x, y), check_circle=False)
        ck.inside(ck.boxes[name], name, L.TICK_R_IN)

    for lang, s in S.items():
        ck.add("dayname-" + lang, ck.text_box("luxe_dxs", widest("luxe_dxs", size, [s["Day%d" % d] for d in range(7)]),
                                              p(140), p(L.DAY_NAME_Y)))
        ck.add("daynum-" + lang, ck.text_box("luxe_dl", "28", p(140), p(L.DAY_NUM_Y)))
        ck.add("month-" + lang, ck.text_box("luxe_dxs", widest("luxe_dxs", size, [s["Month%d" % m] for m in range(1, 13)]),
                                            p(140), p(L.MONTH_Y)))
        # Arabic pieces (language independent): widest Hijri date, on two lines
        ck.add("hijri", ck.text_box("ar_small", widest("ar_small", size, ["%s 30" % chr(ord("A") + m) for m in range(12)]),
                                    p(140), p(L.HIJRI_Y)))
        ck.add("hijri_year", ck.text_box("ar_small", "M 1448", p(140), p(L.HIJRI_Y2)))
        ck.add("hijri_latin-" + lang, ck.text_box("luxe_s", widest("luxe_s", size, [
            "30 %s" % s["Hijri%d" % m] for m in range(1, 13)]), p(140), p(L.HIJRI_Y)))
        ck.add("hijri_latin_year-" + lang, ck.text_box("luxe_s", "1448 %s" % s["HijriSuffix"], p(140), p(L.HIJRI_Y2)))
        # battery line under the verse: icon (20 units with its gap) then "100%"
        tb = ck.text_box("luxe_s", "100%", p(140) + p(10), p(L.BATT_Y))
        bb = (tb[0] - p(20), min(tb[1], p(L.BATT_Y) - p(4)), tb[2], max(tb[3], p(L.BATT_Y) + p(5)))
        ck.add("battery", bb)
        ck.inside(bb, "battery", L.AYAH_AREA_R)
        # gauge content must fit inside the ring
        rin = p(L.GAUGE_R) - max(1, p(L.GAUGE_PEN)) // 2
        for key in face.LABELS + ["LabelMi", "LabelDay", "LabelNight"]:
            b = ck.text_box("luxe_xs", s[key], 0, p(L.GAUGE_LABEL_DY))
            half = max(-b[0], b[2])
            yb = max(abs(b[1]), abs(b[3]))
            if math.hypot(half, yb) > rin:
                ck.fail.append("gauge label %s/%s (%d px) crosses the ring" % (lang, s[key], b[2] - b[0]))
        # cartouche text
        names = [s["Prayer%d" % i] for i in (0, 2, 3, 5, 6, 7)]   # 7: Jumu'ah (Fridays)
        area = p(L.PANEL_W) - p(22)
        for t, fn in [(widest("luxe_xs", size, names), "luxe_xs"), (widest("ar_small", size, list("NOPQRS")), "ar_small"),
                      ("23h59", "luxe_s"), ("00:00", "luxe_s"),
                      (s["SetLocation"], "luxe_xs"), (s["SetLocation2"], "luxe_xs")]:
            w = face.font(fontname_for(fn), size).width(t)
            limit = area if t not in (s["SetLocation"], s["SetLocation2"]) else p(L.PANEL_W) - 4
            if w > limit:
                ck.fail.append("cartouche text %s/'%s' (%d px) wider than its area (%d px)" % (lang, t, w, limit))

    # values inside the ring
    inner = 2 * (p(L.GAUGE_R) - max(1, p(L.GAUGE_PEN)) // 2) - 2
    for v in ["9999", "99.9k", "999k", "--", "200", "100", "88.8", "23h59"]:
        w = min(face.font(fontname_for(f), size).width(v) for f in ("luxe_l", "luxe_m", "luxe_s"))
        if w > inner:
            ck.fail.append("gauge value '%s' (%d px) wider than the ring interior (%d px)" % (v, w, inner))

    # inside a gauge: icon, value and label must not touch each other
    for fn, val, idy, ldy, lab in (("luxe_m", "9999", L.GAUGE_ICON_DY, L.GAUGE_LABEL_DY, "STRESS"),
                                   ("luxe_l", "100", L.GAUGE_BATT_ICON_DY, L.GAUGE_BATT_LABEL_DY, "%")):
        # real icon extents (dial units): generic icons 13 x 12, battery 13 x 7 (see drawGaugeIcon)
        top, bot = (-6, 5) if lab != "%" else (-3, 4)
        icon = (-p(7), p(idy) + p(top), p(7), p(idy) + p(bot))
        if math.hypot(p(7), p(idy) + p(top)) > p(L.GAUGE_R) - max(1, p(L.GAUGE_PEN)) // 2:
            ck.fail.append("gauge icon (%s) crosses the ring" % fn)
        vb = ck.text_box(fn, val, 0, p(L.GAUGE_VALUE_DY))
        lb = ck.text_box("luxe_xs", lab, 0, p(ldy))
        if math.hypot(max(-lb[0], lb[2]), lb[3]) > p(L.GAUGE_R) - max(1, p(L.GAUGE_PEN)) // 2:
            ck.fail.append("gauge label at %d crosses the ring (%s)" % (ldy, fn))
        if overlap(vb, lb):
            ck.fail.append("gauge value (%s) touches the label" % fn)
        if overlap(vb, icon):
            ck.fail.append("gauge value (%s) touches the icon" % fn)

    # sunrise / sunset groups
    for name, sgn in (("sunrise", -1), ("sunset", 1)):
        x = p(140 + sgn * L.SUN_DX)
        ck.add(name + "-time", ck.text_box("luxe_s", "00:00", x, p(L.SUN_TIME_Y)))
        ck.add(name + "-icon", (x - p(9), p(L.SUN_ICON_Y) - p(8), x + p(9), p(L.SUN_ICON_Y) + p(7)))

    # cartouches (prayer panels) and Ayah glyphs
    for name, sgn in (("panel-left", -1), ("panel-right", 1)):
        x0 = p(140 + sgn * L.PANEL_DX) - p(L.PANEL_W) // 2
        ck.add(name, (x0, p(L.PANEL_Y0), x0 + p(L.PANEL_W), p(L.PANEL_Y0 + L.PANEL_H)))
    rep = json.load(open(os.path.join(ROOT, "tools", "assets-report.json")))["fonts"][str(size)]["ayah"]
    for ref, a in rep.items():
        b = (p(140) - a["w"] // 2, p(L.AYAH_Y) - a["h"] // 2, p(140) + (a["w"] + 1) // 2, p(L.AYAH_Y) + (a["h"] + 1) // 2)
        ck.add("ayah " + ref, b)
        ck.inside(b, "ayah " + ref, L.AYAH_AREA_R)
        if b[3] > p(L.AYAH_AREA_BOTTOM):
            ck.fail.append("ayah %s below the Ayah area" % ref)

    # overlaps
    for name, b in ck.boxes.items():
        for i, (gx, gy) in enumerate(gauges):
            gap = box_circle_gap(b, gx, gy, disc)
            if gap < 1:
                ck.fail.append("%s overlaps gauge %d (gap %.1f px)" % (name, i + 1, gap))
    names = list(ck.boxes)
    # variants of the same slot (e.g. Arabic and Latin Hijri date) are never shown together
    group = lambda n: n.split("-")[0].split(" ")[0].split("_")[0]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            if group(a) == group(b):
                continue
            if overlap(ck.boxes[a], ck.boxes[b]):
                ck.fail.append("%s overlaps %s" % (a, b))
    report.append("| %d x %d | %s |" % (size, size, "PASS" if not ck.fail else "FAIL: " + "; ".join(ck.fail[:6])))
    return ck.fail


LITE_SIZES = [218, 240, 260, 280, 390]   # screens of the Connect IQ 3 watches (digital face)


def check_digital(size, report):
    """Digital e-paper face (drawDigital): worst-case texts inside the circle, no overlaps."""
    ck = Check(size)
    p = ck.p
    c = int(ck.c)
    S = {"eng": face.strings("eng"), "fre": face.strings("fre")}
    ck.add("time", ck.text_box("dg_time", "23:59", c, p(L.DG_TIME_Y)), check_circle=False)
    ck.inside(ck.boxes["time"], "time", L.DG_RIM_R - 4)
    tb = ck.boxes["time"]
    if tb[1] < p(L.DG_BAND_Y0) - 2 or tb[3] > p(L.DG_BAND_Y1) + 2:
        ck.fail.append("time digits leave the dithered band")
    for lang, s in S.items():
        date = max(["%s 28 %s" % (s["Day%d" % d], s["Month%d" % m]) for d in range(7) for m in range(1, 13)],
                   key=face.font("dg_m", size).width)
        ck.add("date-" + lang, ck.text_box("dg_m", date, c, p(L.DG_DATE_Y)))
        lat = max(["30 %s 1448 %s" % (s["Hijri%d" % m], s["HijriSuffix"]) for m in range(1, 13)], key=face.font("dg_s", size).width)
        ck.add("hijri_latin-" + lang, ck.text_box("dg_s", lat, c, p(L.DG_HIJRI_Y)))
        names = [s["Prayer%d" % i] for i in (0, 2, 3, 5, 6, 7)]
        ck.add("name-" + lang, ck.text_box("dg_s", max(names, key=face.font("dg_s", size).width), c + p(L.DG_NAME_DX), p(L.DG_PRAYER_Y)))
        ck.add("bpm-" + lang, ck.text_box("dg_s", s["LabelHeart"], c, p(L.DG_LABEL_Y)))
    ck.add("hijri", ck.text_box("ar_small", max(["M 1448 %s 30" % chr(ord("A") + m) for m in range(12)],
                                                 key=face.font("ar_small", size).width), c, p(L.DG_HIJRI_Y)))
    ck.add("name_ar", ck.text_box("ar_small", max(list("NOPQRS"), key=face.font("ar_small", size).width), c + p(L.DG_NAME_DX), p(L.DG_PRAYER_Y)))
    ck.add("ptime", ck.text_box("dg_m", "00:00", c + p(L.DG_PTIME_DX), p(L.DG_PRAYER_Y)))
    pw, ph = p(L.DG_PILL_W), p(L.DG_PILL_H)
    px = c + p(L.DG_PILL_DX)
    ck.add("pill", (px - pw // 2, p(L.DG_PRAYER_Y) - ph // 2, px + pw // 2, p(L.DG_PRAYER_Y) + ph // 2))
    cd = ck.text_box("dg_m", "23h59", px, p(L.DG_PRAYER_Y))
    if cd[0] < px - pw // 2 + 1 or cd[2] > px + pw // 2 - 1:
        ck.fail.append("countdown wider than its pill")
    r = p(L.DG_RING_R) + 2
    sx = c - p(L.DG_STATUS_DX)
    ck.add("steps_ring", (sx - r, p(L.DG_STATUS_Y) - r, sx + r, p(L.DG_STATUS_Y) + r))
    ck.add("steps", ck.text_box("dg_s", "99999", sx, p(L.DG_LABEL_Y)))
    ck.add("battery", (c + p(L.DG_STATUS_DX) - p(14), p(L.DG_STATUS_Y) - p(6), c + p(L.DG_STATUS_DX) + p(17), p(L.DG_STATUS_Y) + p(6)))
    ck.add("batt_pct", ck.text_box("dg_s", "100%", c + p(L.DG_STATUS_DX), p(L.DG_LABEL_Y)))
    ck.add("hr", ck.text_box("dg_m", "199", c, p(L.DG_STATUS_Y)))
    names = list(ck.boxes)
    grp = lambda n: n.split("-")[0]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if grp(a) == grp(b) or {grp(a), grp(b)} <= {"hijri", "hijri_latin", "name", "name_ar"} and grp(a)[:4] == grp(b)[:4]:
                continue
            if {grp(a), grp(b)} == {"pill", "ptime"} or "pill" in (grp(a), grp(b)) and "ptime" not in (grp(a), grp(b)) and False:
                pass
            if overlap(ck.boxes[a], ck.boxes[b]):
                ck.fail.append("%s overlaps %s" % (a, b))
    report.append("| digital | %d x %d | %s |" % (size, size, "PASS" if not ck.fail else "FAIL: " + "; ".join(ck.fail[:6])))
    return ck.fail


def main():
    global FAM
    report = ["| Font | Screen | Result |", "|---|---|---|"]
    failures = []
    for fam in face.FAMILIES:
        FAM = fam
        for size in face.RESOLUTIONS:
            rows = []
            f = check_size(size, rows)
            report += ["| %s %s" % (fam, r) for r in rows]
            failures += ["%s %d: %s" % (fam, size, x) for x in f]
    for size in LITE_SIZES:
        rows = []
        failures += ["digital %d: %s" % (size, x) for x in check_digital(size, rows)]
        report += rows
    out = os.path.join(ROOT, "docs", "layout-report.md")
    with open(out, "w") as fh:
        fh.write("# Layout validation report\n\nGenerated by `tools/check_layout.py`: worst-case English and French "
                 "content, every supported round screen size, safe radius %d px at 280 px (scaled).\n\n" % L.SAFE_R
                 + "\n".join(report) + "\n\n## Result\n\n**%s**\n" % ("PASS" if not failures else "FAIL")
                 + "".join("* %s\n" % f for f in failures))
    for f in failures:
        print("FAIL:", f)
    print("layout check:", "PASS" if not failures else "FAIL (%d)" % len(failures), "-", out)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
