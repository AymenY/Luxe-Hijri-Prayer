#!/usr/bin/env python3
"""Generates the 280 x 280 reference previews in docs/previews/ (and store artwork).

Every image is a REFERENCE RENDER produced by tools/face.py (a Python mirror of the Monkey C
drawing code with the real fonts, layout, colours and background data, quantised to the
64-colour MIP palette). They are not simulator or device screenshots. Pixels outside the
round display are black, as on the watch. Sensor values are simulated; dates, prayer times,
sun times and Hijri dates are computed for the stated time and place.
"""
import datetime as dt
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import face  # noqa: E402

ROOT = face.ROOT
OUT = os.path.join(ROOT, "docs", "previews")
TUNIS = dt.timezone(dt.timedelta(hours=1))
manifest = []


def when(*a, tz=TUNIS):
    return int(dt.datetime(*a, tzinfo=tz).timestamp())


def render(name, title, settings=None, now=None, offset=3600, sensors=None, lang="eng", seconds=True):
    s = dict(face.DEFAULT_SETTINGS)
    s.update(settings or {})
    now = now or when(2026, 10, 29, 10, 8, 37)
    img, info = face.Face(s, lang).render(now, offset, sensors or face.DEFAULT_SENSORS, show_seconds=seconds)
    img = face.circular(img, outside=(0, 0, 0))
    img.save(os.path.join(OUT, name + ".png"))
    local = dt.datetime.fromtimestamp(now, dt.timezone(dt.timedelta(seconds=offset)))
    nxt = info["next"]
    manifest.append({"file": "previews/%s.png" % name, "title": title, "local_time": local.isoformat(),
                     "hijri": "%d-%02d-%02d" % info["hijri"],
                     "next_prayer": None if not nxt else ["Fajr", "", "Dhuhr", "Asr", "", "Maghrib", "Isha"][nxt[0]]})
    return img


def sheet(name, files, cols=4, label=True):
    ims = [Image.open(os.path.join(OUT, f + ".png")) for f in files]
    rows = (len(ims) + cols - 1) // cols
    pad, cap = 8, 18 if label else 0
    g = Image.new("RGB", (cols * (280 + pad) + pad, rows * (280 + pad + cap) + pad), (24, 24, 24))
    d = ImageDraw.Draw(g)
    for i, (im, f) in enumerate(zip(ims, files)):
        x, y = pad + (i % cols) * (280 + pad), pad + (i // cols) * (280 + pad + cap)
        g.paste(im, (x, y))
        if label:
            d.text((x + 4, y + 282), f, fill=(200, 200, 200))
    g.save(os.path.join(OUT, name + ".png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    presets = []
    for i, n in enumerate(face.PRESET_NAMES):
        f = "style-%d-%s" % (i + 1, n.lower().replace(" ", "-"))
        render(f, "Style preset %s, background Mosque" % n, {"preset": i})
        presets.append(f)
    bgs = []
    for i, n in enumerate(["mosque", "geometric", "marble", "night-sky"]):
        for p in (0, 1, 3):
            f = "background-%s-%s" % (n, face.PRESET_NAMES[p].lower().replace(" ", "-"))
            render(f, "Background %s, preset %s" % (n, face.PRESET_NAMES[p]), {"background": i, "preset": p})
            bgs.append(f)
    ayat = []
    for a in range(7):
        f = "ayah-%d" % (a + 1)
        render(f, "Ayah selection %d" % (a + 1), {"ayah": a, "background": 3})
        ayat.append(f)
    render("ayah-6b-ikhlas-verses-3-4", "Al-Ikhlas verses 3-4 (odd minutes)", {"ayah": 5, "background": 3},
           now=when(2026, 10, 29, 10, 9, 37))
    ayat.append("ayah-6b-ikhlas-verses-3-4")
    render("ayah-hidden", "Ayah hidden", {"ayah": 7})
    ayat.append("ayah-hidden")

    states = []

    def st(f, title, **kw):
        render(f, title, **kw)
        states.append(f)
    st("state-low-battery", "Battery 9 % (warning colour), steps over goal, heart rate unavailable",
       sensors={**face.DEFAULT_SENSORS, 0: {"value": 12480, "goal": 10000}, 1: {"value": None},
                3: {"battery": 9.0}})
    st("state-all-sources", "Gauges: distance, floors, Body Battery, stress",
       settings={"gauges": [4, 5, 6, 7]})
    st("state-missing-sensors", "No sensor history available (all optional data missing)",
       settings={"gauges": [1, 5, 6, 7]}, sensors={3: {"battery": 55.0}})
    st("state-set-location", "Latitude and longitude left at 0/0: location requested",
       settings={"lat": 0.0, "lon": 0.0})
    st("state-french-12h", "French strings, 12-hour schedule", settings={"is24": False}, lang="fre")
    st("state-after-isha", "After Isha: countdown to tomorrow's Fajr, tomorrow's schedule",
       now=when(2026, 10, 29, 22, 40, 5))
    st("state-midnight", "00:00:30 local time", now=when(2026, 10, 30, 0, 0, 30))
    st("state-before-maghrib", "Long prayer name (MAGHRIB) with short countdown",
       now=when(2026, 10, 29, 17, 15, 44))
    st("state-hijri-new-year", "1 Muharram 1448 (tabular) on 17 June 2026", now=when(2026, 6, 17, 9, 0, 0))
    st("state-hijri-new-year-minus2", "Same day with Hijri correction -2 (29 Dhu al-Hijjah 1447)",
       settings={"hijri_corr": -2}, now=when(2026, 6, 17, 9, 0, 0))
    st("state-makkah-ummalqura", "Makkah, Umm al-Qura method, UTC+3",
       settings={"lat": 21.4225, "lon": 39.8262, "method": 4, "tz_manual": True, "utc_offset": 10800},
       now=when(2026, 10, 29, 16, 20, 0, tz=dt.timezone(dt.timedelta(hours=3))), offset=10800)
    st("state-oslo-no-highlat-rule", "Oslo in June, MWL, no high-latitude rule: Fajr/Isha undefined",
       settings={"lat": 59.9139, "lon": 10.7522, "method": 1, "highlat": 0},
       now=when(2026, 6, 21, 21, 0, 0, tz=dt.timezone(dt.timedelta(hours=2))), offset=7200)
    st("state-low-power-no-seconds", "Low power with 'Only after wrist raise': no seconds hand", seconds=False)

    sheet("overview-styles", presets, cols=3)
    sheet("overview-backgrounds", bgs, cols=3)
    sheet("overview-ayat", ayat, cols=3)
    sheet("overview-states", states, cols=3)

    # store artwork (reference renders)
    store = os.path.join(ROOT, "store")
    os.makedirs(store, exist_ok=True)
    for i, f in enumerate([presets[0], presets[1], presets[2], presets[3], presets[4], presets[5]]):
        Image.open(os.path.join(OUT, f + ".png")).save(os.path.join(store, "screenshot-%d.png" % (i + 1)))
    hero = Image.new("RGB", (1440, 720), (0, 0, 0x22))
    for i, f in enumerate([presets[0], presets[1], presets[4]]):
        im = Image.open(os.path.join(OUT, f + ".png")).resize((420, 420), Image.LANCZOS)
        hero.paste(im, (60 + i * 460, 150))
    hero.save(os.path.join(store, "hero-1440x720.png"))
    icon = Image.open(os.path.join(OUT, presets[0] + ".png")).resize((512, 512), Image.LANCZOS)
    icon.save(os.path.join(store, "store-icon-512.png"))

    with open(os.path.join(ROOT, "docs", "previews.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print("%d previews written to %s" % (len(manifest), OUT))


if __name__ == "__main__":
    main()
