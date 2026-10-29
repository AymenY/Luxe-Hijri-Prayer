# Build, test and release checklist

Legend: ✅ done in this repository · ⬜ to do on a machine with the Connect IQ SDK / the watch.

## Done without the SDK

* ✅ Audit and baseline commit (`docs/AUDIT.md`)
* ✅ Static project checks pass — `python3 tools/check_project.py`
* ✅ Monkey C syntax of all sources parses (open-source parser, part of the check above)
* ✅ Prayer/sun/Hijri algorithms validated against independent libraries — `python3 tools/validate_calculations.py`
* ✅ Circular layout validated with worst-case EN/FR content — `python3 tools/check_layout.py`
* ✅ Reference renders of 6 styles, 4 backgrounds, 8 Ayah states and 13 edge cases — `python3 tools/make_previews.py`

## Compile (requires the SDK)

* ⬜ Install the Connect IQ SDK Manager, the current SDK and the **fēnix 7X Pro** device files
* ⬜ Generate a developer key (keep it **outside** the repository, never commit it)
* ⬜ `monkeyc -f monkey.jungle -d fenix7xpro -o bin/LuxeHijriPrayer.prg -y <key.der> -w`
* ⬜ Fix every compiler error or warning (none could be checked here: types and API signatures
  were reviewed by hand only)
* ⬜ Check memory in the simulator (*File → View Memory*); the watch-face limit is shown there

## Simulator tests

* ⬜ Unit tests: `monkeyc ... --unit-test -o bin/test.prg` then `monkeydo bin/test.prg fenix7xpro -t` (5 tests in `test/LuxeTests.mc`)
* ⬜ Compare the simulator with `docs/previews/*` for each style and background
* ⬜ *Settings → Trigger App Settings* (or the settings editor): change every setting, confirm the dial updates
* ⬜ *Settings → Low Power Mode*: seconds hand keeps moving (option “Always”) or disappears (“Only after wrist raise”)
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
