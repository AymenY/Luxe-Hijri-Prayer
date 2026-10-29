# Luxe Hijri Prayer

Luxury analog-digital Connect IQ **watch face** for the Garmin **fēnix 7X Pro / 7X Pro
Sapphire Solar (51 mm, 280 × 280 round 64-colour MIP display)**, written in Monkey C.

![Six styles (reference renders)](docs/previews/overview-styles.png)

> **Status.** The source is complete, but it **has not been compiled yet**: the Connect IQ SDK
> could not be downloaded in the environment where it was written. The images in
> `docs/previews/` are **reference renders** produced by a Python mirror of the drawing code
> (same layout, fonts, colours and data), **not** simulator screenshots. See
> [`docs/AUDIT.md`](docs/AUDIT.md) and [`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md).

## Features

* Analog clock: gold faceted hour and minute hands, long seconds hand (122 px, 87 % of the
  radius) with counterweight; double baton at 12, batons at 3 and 9, 8-point star at 6
* Next prayer name and countdown, schedule of the five prayers (next one highlighted, past ones
  dimmed), sunrise and sunset
* Gregorian date and Hijri date, Hijri correction −2…+2 days
* Four gauges, each selectable: steps, heart rate, calories, battery, distance, floors,
  Body Battery, stress (defaults: steps, heart rate, calories, battery); large battery value
* Six style presets that recolour every element, four vector backgrounds, eight Ayah choices
  (seven verses or hidden)
* English and French
* Excluded by design: weather, temperature, wind, altitude, compass

## Settings (Garmin Connect app → watch face → Settings)

| Group | Setting | Default |
|---|---|---|
| Appearance | Style Preset | Luxury Blue |
| Appearance | Background | Mosque and crescent moon |
| Appearance | Seconds hand: always / only after wrist raise | Always |
| Data Fields | Gauge 1–4 | Steps, Heart rate, Calories, Battery |
| Faith & Calendar | Hijri Date Correction | 0 days |
| Faith & Calendar | Ayah Selection | Taha 20:114 |
| Faith & Calendar | Prayer calculation method (14) | Tunisia 18°/18° |
| Faith & Calendar | Asr convention | Standard |
| Faith & Calendar | High-latitude rule | Middle of the night |
| Faith & Calendar | Latitude / Longitude | 33.8754 / 10.8575 (Houmt Souk, Djerba) |
| Faith & Calendar | Time zone: watch (auto, DST) / manual UTC offset | Watch |

Coordinates are entered manually (decimal degrees, north and east positive). 0 / 0 is treated as
“not set” and the dial shows **SET LOCATION**.

## Project layout

```
manifest.xml, monkey.jungle     project (target: fenix7xpro, min API 4.0.0)
source/
  LuxeHijriPrayerApp.mc         app, settings-changed hook, power-budget delegate
  LuxeHijriPrayerView.mc        drawing, buffered rendering, low-power seconds hand
  PrayerTimes.mc                prayer/sun algorithm + PrayerSchedule cache
  HijriCalendar.mc, CivilDate.mc
  DataFields.mc                 gauge data sources
  Settings.mc                   validated settings
  Themes.mc, Layout.mc          six presets (MIP palette), dial geometry
  Backgrounds.mc                vector background interpreter
test/LuxeTests.mc               Monkey C unit tests (:test)
resources/                      strings, settings, properties, fonts, background data, icon
resources-fre/                  French strings
tools/                          asset build, validation, layout check, previews (Python)
docs/                           audit, calculations, Ayat, store texts, checklist, previews
store/                          store artwork (reference renders)
```

## Build and run (needs the Connect IQ SDK)

1. Install the [Connect IQ SDK Manager](https://developer.garmin.com/connect-iq/sdk/), download
   the current SDK and the **fēnix 7X Pro** device, and install the *Monkey C* VS Code extension.
2. Create a developer key once, **outside** this repository:
   ```sh
   openssl genrsa -out ~/garmin/developer_key.pem 4096
   openssl pkcs8 -topk8 -inform PEM -outform DER -in ~/garmin/developer_key.pem \
       -out ~/garmin/developer_key.der -nocrypt
   ```
3. Compile and start the simulator:
   ```sh
   monkeyc -f monkey.jungle -d fenix7xpro -o bin/LuxeHijriPrayer.prg -y ~/garmin/developer_key.der -w
   connectiq &
   monkeydo bin/LuxeHijriPrayer.prg fenix7xpro
   ```
   (In VS Code: *Monkey C: Build for Device* / *Run*.)
4. Unit tests:
   ```sh
   monkeyc -f monkey.jungle -d fenix7xpro -o bin/test.prg -y ~/garmin/developer_key.der --unit-test
   monkeydo bin/test.prg fenix7xpro -t
   ```
5. Install on the watch: connect it by USB and copy `bin/LuxeHijriPrayer.prg` to
   `GARMIN/APPS/` (macOS: use an MTP tool such as OpenMTP), then select the face on the watch.
6. Store package: `monkeyc -f monkey.jungle -e -r -o bin/LuxeHijriPrayer.iq -y ~/garmin/developer_key.der`
   and upload it at <https://apps.garmin.com/developer/> (beta first). Texts: `docs/STORE.md`.

Never commit the developer key: `*.der`, `*.pem`, `*.prg` and `*.iq` are git-ignored.

## Tools (no SDK needed)

```sh
pip install -r tools/requirements.txt      # Pillow (with raqm), adhanpy, astral, convertdate, hijridate
(cd tools && npm install)                   # optional: Monkey C parser for the syntax check
python3 tools/build_assets.py               # fonts, Ayah glyphs, background geometry, icon
python3 tools/check_project.py              # resources, settings, palette, fonts, syntax
python3 tools/validate_calculations.py      # -> docs/validation-report.md
python3 tools/check_layout.py               # -> docs/layout-report.md
python3 tools/make_previews.py              # -> docs/previews/, store/
```

`tools/face.py` and `tools/luxe_ref/calc.py` mirror the Monkey C drawing code and algorithms;
keep them in sync when changing `source/`.

## Documentation

* [Audit report](docs/AUDIT.md) — starting point, environment limits, design decisions
* [Calculations](docs/CALCULATIONS.md) — prayer method, Hijri convention, limitations
* [Ayah selection](docs/AYAT.md) — verified Arabic text, sources, French translation
* [Validation report](docs/validation-report.md) · [Layout report](docs/layout-report.md)
* [Store listing (EN/FR)](docs/STORE.md) · [Release checklist](docs/RELEASE_CHECKLIST.md)

## Licences

Code: © the author. Fonts: Barlow Semi Condensed and Amiri, SIL Open Font License 1.1
(`tools/fonts-src/OFL-*.txt`); the bitmap fonts in `resources/fonts/` are derived from them.
Arabic text: Tanzil (CC BY 3.0, unmodified text). French translation: M. Hamidullah via Tanzil
(documentation only).
