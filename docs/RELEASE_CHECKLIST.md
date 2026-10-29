# Build, test and release checklist

Legend: ✅ done in this repository · ⬜ to do on a machine with the Connect IQ SDK / the watch.

## Done without the SDK

* ✅ Audit and baseline commit (`docs/AUDIT.md`)
* ✅ Static project checks pass — `python3 tools/check_project.py`
* ✅ Monkey C syntax of all sources parses (open-source parser, part of the check above)
* ✅ Prayer/sun/Hijri algorithms validated against independent libraries — `python3 tools/validate_calculations.py`
* ✅ Circular layout validated for all 8 screen sizes (218–454 px) — `python3 tools/check_layout.py`
* ✅ Circular layout validated for 3 font families, both Hijri scripts and all 39 verses
* ✅ Reference renders: styles, backgrounds, 8 screen sizes, AMOLED always-on, verses, customisation, edge cases — `python3 tools/make_previews.py`
* ✅ Build automation: `tools/ci_build.sh` and the GitHub Actions workflow `.github/workflows/build.yml`

## Compile (requires the SDK)

* ⬜ Either run the GitHub Actions build (README, “Compile a preview…”), or install the Connect IQ SDK Manager, the current SDK and the device files
* ⬜ `python3 tools/update_products.py --write`, review the selected devices
* ⬜ Generate a developer key (keep it **outside** the repository, never commit it)
* ⬜ Build at least one device per screen size and type: fenix7s (240 MIP), fenix7 (260 MIP), fenix7xpro (280 MIP), fr255s (218 MIP), venu2s (360 AMOLED), fr165 (390 AMOLED), epix2pro47mm (416 AMOLED), epix2pro51mm / fr965 (454 AMOLED)
* ⬜ `monkeyc -f monkey.jungle -d <device> -o bin/<device>.prg -y <key.der> -w`
* ⬜ Fix every compiler error or warning (none could be checked here: types and API signatures
  were reviewed by hand only)
* ⬜ Check memory in the simulator (*File → View Memory*); the watch-face limit is shown there
* ⬜ The compiler accepts `packingFormat="jpg"` / `"png"` on the dial bitmaps (otherwise remove the attribute)
* ⬜ `.prg` size per device is acceptable (HD dials: ~1.2 MB at 454 px, ~0.5 MB on MIP)
* ⬜ The HD dial loads on every device (if not, the vector fallback is shown: compare with `docs/previews/`)

## Simulator tests

* ⬜ Unit tests: `monkeyc ... --unit-test -o bin/test.prg` then `monkeydo bin/test.prg fenix7xpro -t` (6 tests in `test/LuxeTests.mc`)
* ⬜ Compare the simulator with `docs/previews/*` for each style and background
* ⬜ *Settings → Trigger App Settings* (or the settings editor): change every setting, confirm the dial updates
* ⬜ *Settings → Low Power Mode* on MIP: seconds hand keeps moving (option “Always”) or disappears (“Only after wrist raise”)
* ⬜ Low power on AMOLED: always-on frame only; *File → View Watchface Diagnostics* shows no burn-in warning
* ⬜ Memory on the largest AMOLED (454 px): the static and frame buffers must be allocated (otherwise the face falls back to direct drawing)
* ⬜ *File → View Watchface Diagnostics*: partial-update time below the budget; if not, the face disables low-power seconds by itself
* ⬜ *Simulation → Activity Data*: steps/calories/floors/distance; HR and sensor history present and absent
* ⬜ Set the simulator time to 23:59 → 00:00, the end of a Hijri month and 1 Muharram; check the dates and the Isha → Fajr countdown
* ⬜ Battery below 15 % (warning colour), charging
* ⬜ Latitude/longitude = 0/0 → “SET LOCATION”
* ⬜ Language French, 12-hour time, statute units
* ⬜ Take real 280 × 280 screenshots for the Store (replace `store/screenshot-*.png`)

## Real device (fēnix 7X Pro)

* ⬜ Sideload `bin/LuxeHijriPrayer.prg` to `GARMIN/APPS/` over USB, select the watch face
* ⬜ Readability outdoors and indoors (MIP display, backlight off)
* ⬜ Arabic verse legibility for each selection
* ⬜ Compare the prayer times with the local timetable for a few days
* ⬜ Battery drain over 24 h with seconds “Always” vs. “Only after wrist raise”
* ⬜ Settings from Garmin Connect (phone) reach the watch

## Store

* ⬜ `monkeyc -f monkey.jungle -e -r -o bin/LuxeHijriPrayer.iq -y <key.der>` (official export)
* ⬜ Upload as a **beta** app first, install from the Store link, re-test, then publish
* ⬜ Listing texts: `docs/STORE.md` (EN/FR); privacy statement included there
* ⬜ The app id in `manifest.xml` must never change after the first upload
