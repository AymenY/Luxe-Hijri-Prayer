#!/usr/bin/env python3
"""Generates the reference previews in docs/previews/ (and store artwork).

Every image is a REFERENCE RENDER produced by tools/face.py (a Python mirror of the Monkey C
drawing code with the real fonts, layout, colours and vector art of each screen size). They
are not simulator or device screenshots. MIP sizes are quantised to the 64-colour palette;
AMOLED sizes (360 px and above) are shown in full colour. Pixels outside the round display
are black. Sensor values are simulated; dates, prayer times, sun times and Hijri dates are
computed for the stated time and place.
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
AMOLED_FROM = 360
manifest = []


def when(*a, tz=TUNIS):
    return int(dt.datetime(*a, tzinfo=tz).timestamp())


DEFAULT_NOW = when(2026, 9, 16, 10, 25, 37)


def render(name, title, settings=None, now=None, offset=3600, sensors=None, lang="fre", seconds=True, size=280):
    s = dict(face.DEFAULT_SETTINGS)
    s.update(settings or {})
    now = now or DEFAULT_NOW
    img, info = face.Face(s, lang, size).render(now, offset, sensors or face.DEFAULT_SENSORS,
                                                show_seconds=seconds, mip=size < AMOLED_FROM)
    face.circular(img).save(os.path.join(OUT, name + ".png"))
    local = dt.datetime.fromtimestamp(now, dt.timezone(dt.timedelta(seconds=offset)))
    nxt = info["next"]
    manifest.append({"file": "previews/%s.png" % name, "title": title, "size": size,
                     "local_time": local.isoformat(), "hijri": "%d-%02d-%02d" % info["hijri"],
                     "next_prayer": None if not nxt else ["Fajr", "", "Dhuhr", "Asr", "", "Maghrib", "Isha"][nxt[0]]})


def sheet(name, files, cols=3):
    ims = [Image.open(os.path.join(OUT, f + ".png")) for f in files]
    cell = max(max(i.width for i in ims), 280)
    rows = (len(ims) + cols - 1) // cols
    pad, cap = 8, 18
    g = Image.new("RGB", (cols * (cell + pad) + pad, rows * (cell + pad + cap) + pad), (24, 24, 24))
    d = ImageDraw.Draw(g)
    for i, (im, f) in enumerate(zip(ims, files)):
        x, y = pad + (i % cols) * (cell + pad), pad + (i // cols) * (cell + pad + cap)
        g.paste(im, (x + (cell - im.width) // 2, y + (cell - im.height) // 2))
        d.text((x + 4, y + cell + 2), f, fill=(200, 200, 200))
    g.save(os.path.join(OUT, name + ".png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".png"):
            os.remove(os.path.join(OUT, f))
    presets = []
    for i, n in enumerate(face.PRESET_NAMES):
        f = "style-%d-%s" % (i + 1, n.lower().replace(" ", "-"))
        render(f, "Style %s, background Mosque, 280 px" % n, {"preset": i})
        presets.append(f)
    bgs = []
    for i, n in enumerate(["mosque", "geometric", "marble", "night-sky"]):
        for pr in (0, 1, 3):
            f = "background-%s-%s" % (n, face.PRESET_NAMES[pr].lower().replace(" ", "-"))
            render(f, "Background %s, style %s" % (n, face.PRESET_NAMES[pr]), {"background": i, "preset": pr})
            bgs.append(f)
    sizes = []
    for size in face.RESOLUTIONS:
        f = "size-%d" % size
        render(f, "%d x %d px (%s)" % (size, size, "AMOLED, full colour" if size >= AMOLED_FROM else "MIP, 64 colours"),
               size=size)
        sizes.append(f)
    # AMOLED always-on frame
    for size in (390, 454):
        img, info = face.Face(dict(face.DEFAULT_SETTINGS), "fre", size).render_aod(DEFAULT_NOW, 3600)
        f = "aod-%d" % size
        face.circular(img).save(os.path.join(OUT, f + ".png"))
        manifest.append({"file": "previews/%s.png" % f, "title": "AMOLED always-on, %d px" % size,
                         "lit_pixels": "%.1f %%" % (100 * info["lit_fraction"])})
        sizes.append(f)
    ayat = []
    for a, minute in [(0, 25), (1, 25), (2, 25), (3, 25), (4, 25), (5, 24), (5, 25), (5, 26), (5, 27), (6, 25), (7, 25)]:
        f = "ayah-%d" % (a + 1) + ("-verse-%d" % (minute % 4 + 1) if a == 5 else "")
        render(f, "Ayah selection %d" % (a + 1), {"ayah": a, "background": 3}, now=when(2026, 9, 16, 10, minute, 37))
        ayat.append(f)
    states = []

    def st(f, title, **kw):
        render(f, title, **kw)
        states.append(f)
    st("state-low-battery", "Battery 9 % (warning colour), steps over goal, heart rate unavailable",
       sensors={**face.DEFAULT_SENSORS, 0: {"value": 12480, "goal": 10000}, 1: {"value": None}, 3: {"battery": 9.0}})
    st("state-all-sources", "Gauges: distance, floors, Body Battery, stress", settings={"gauges": [4, 5, 6, 7]})
    st("state-missing-sensors", "No optional data available", settings={"gauges": [1, 5, 6, 7]},
       sensors={3: {"battery": 55.0}})
    st("state-set-location", "Latitude and longitude left at 0/0", settings={"lat": 0.0, "lon": 0.0})
    st("state-english-12h", "English strings, 12-hour times", settings={"is24": False}, lang="eng")
    st("state-after-isha", "After Isha: countdown to tomorrow's Fajr", now=when(2026, 9, 16, 22, 40, 5))
    st("state-midnight", "00:00:30 local time", now=when(2026, 9, 17, 0, 0, 30))
    st("state-hijri-new-year", "1 Muharram 1448 (tabular) on 17 June 2026", now=when(2026, 6, 17, 9, 0, 0))
    st("state-hijri-new-year-minus2", "Same day with Hijri correction -2", settings={"hijri_corr": -2},
       now=when(2026, 6, 17, 9, 0, 0))
    st("state-makkah-ummalqura", "Makkah, Umm al-Qura, UTC+3",
       settings={"lat": 21.4225, "lon": 39.8262, "method": 4, "tz_manual": True, "utc_offset": 10800},
       now=when(2026, 9, 16, 16, 20, 0, tz=dt.timezone(dt.timedelta(hours=3))), offset=10800)
    st("state-oslo-no-highlat-rule", "Oslo in June, MWL, no high-latitude rule",
       settings={"lat": 59.9139, "lon": 10.7522, "method": 1, "highlat": 0},
       now=when(2026, 6, 21, 21, 0, 0, tz=dt.timezone(dt.timedelta(hours=2))), offset=7200)
    st("state-ayah-hidden", "Ayah hidden", settings={"ayah": 7})
    st("state-low-power-no-seconds", "MIP low power, 'Only after wrist raise': no seconds hand", seconds=False)

    sheet("overview-styles", presets)
    sheet("overview-backgrounds", bgs)
    sheet("overview-sizes", sizes, cols=4)
    sheet("overview-ayat", ayat, cols=4)
    sheet("overview-states", states)

    store = os.path.join(ROOT, "store")
    os.makedirs(store, exist_ok=True)
    for i, f in enumerate(presets):
        Image.open(os.path.join(OUT, f + ".png")).save(os.path.join(store, "screenshot-%d.png" % (i + 1)))
    hero = Image.new("RGB", (1440, 720), (0, 0, 0x22))
    for i, f in enumerate([presets[0], presets[1], presets[4]]):
        im = Image.open(os.path.join(OUT, f + ".png")).resize((420, 420), Image.LANCZOS)
        hero.paste(im, (60 + i * 460, 150))
    hero.save(os.path.join(store, "hero-1440x720.png"))
    big = face.Face(dict(face.DEFAULT_SETTINGS), "fre", 454).render(DEFAULT_NOW, 3600, face.DEFAULT_SENSORS, mip=False)[0]
    face.circular(big).resize((512, 512), Image.LANCZOS).save(os.path.join(store, "store-icon-512.png"))

    with open(os.path.join(ROOT, "docs", "previews.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)
    print("%d previews written to %s" % (len(manifest), OUT))
    for m in manifest:
        if "lit_pixels" in m:
            print(m["title"], "lit pixels:", m["lit_pixels"])


if __name__ == "__main__":
    main()
