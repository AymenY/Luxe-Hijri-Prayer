# Release checklist

Legend: ✅ done · ⬜ to do by the owner (needs the SDK simulator, the watch or the Store account).

## Done

* ✅ Static checks — `python3 tools/check_project.py` (resources, settings, menu, fonts, Monkey C syntax)
* ✅ Algorithms validated against independent libraries — `python3 tools/validate_calculations.py`
  (prayer times, sunrise/sunset, Hijri calendar, Moon phase)
* ✅ Layout validated for 9 screen sizes (218–466 px), 3 font families, EN/FR — `python3 tools/check_layout.py`
* ✅ Compiles without errors with Connect IQ SDK 9.3.0 (GitHub Actions): 8 preview devices and the
  unit-test build
* ✅ Runs on a fēnix 7X Pro (sideloaded): dial, gauges, prayers, verse, Moon, daylight ring
* ✅ No network access, one permission (SensorHistory), settings validated with fallbacks
* ✅ Store texts EN/FR and privacy statement — `docs/STORE.md`

## Before submission

* ⬜ Create your permanent developer key **once** and keep it safe, outside the repository (README,
  “Store package”). Every future update must be signed with the same key.
* ⬜ Add it as the GitHub secret `CIQ_DEVELOPER_KEY`, then run *Actions → Build → Run workflow*
  with mode `all` (every listed device must compile) and mode `iq` (the Store package)
* ⬜ On the watch: watch face → Customise opens the settings menu; change a few settings
* ⬜ Simulator (SDK on a computer): unit tests `monkeydo bin/LuxeHijriPrayer-tests.prg fenix7xpro -t`
  (7 tests); *File → View Memory* on the largest AMOLED (454 px) and on fr255s (218 px)
* ⬜ Simulator: *File → View Watchface Diagnostics* — partial update below the power budget (MIP),
  no burn-in warning (AMOLED always-on)
* ⬜ Real screenshots (simulator *File → Save Screenshot*, or the watch) to replace `store/screenshot-*.png`
* ⬜ Rights to the background illustration (`docs/STORE.md`, “Rights to check”)

## Store

* ⬜ Upload `bin/LuxeHijriPrayer.iq` at <https://apps.garmin.com/developer/> as a **beta** first,
  install it from the Store link, test, then publish
* ⬜ Listing texts and privacy statement from `docs/STORE.md`
* ⬜ The app id in `manifest.xml` must never change after the first upload
