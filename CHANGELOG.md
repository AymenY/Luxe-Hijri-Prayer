# Changelog

All dates 2026-10-29. Nothing has been compiled with the Connect IQ SDK yet; see
`docs/RELEASE_CHECKLIST.md`.

## Unreleased — preview 0.5 (after the first test on a fēnix 7X Pro)
* Daylight / darkness ring (24 h) as a gauge source, default for gauge 4 (replaces the battery
  gauge); small battery line under the verse when no gauge shows the battery.
* Verse without surah name and verse number.
* Thinner chapter ring (4 px at 280 px); indices and numerals moved outwards.
* Crisp Arabic glyphs on MIP screens; darker shadows behind the Hijri date and the verse.
* First real builds: SDK 9.3.0, 8 preview devices, no errors; `enduro2` removed (unknown id).

## Preview 0.4
* 39 complete short verses with hourly rotation, a fixed verse or none; Arabic references.
* Hijri date in Arabic (Eastern Arabic digits, month names, هـ) or Latin.
* Full customisation (64 settings): fonts, colours, hands, seconds hand, gauges.
* Owner's mosque illustration as the default background, colour-graded per style; smoked-glass
  gauges; lobed Moorish window for the other backgrounds.
* Build automation: `tools/ci_build.sh`, GitHub Actions workflow.

## 0.3 — HD artwork
* Static dial rendered offline in HD for every screen size, style and background.
* MIP images left in full colour so the compiler uses each device's own palette.

## 0.2 — concept layout, all round colour watches
* Layout of the approved concept (numerals, ring gauges, date block, arch scene, cartouches).
* 8 screen sizes (218–454 px), MIP and AMOLED, burn-in safe always-on mode.

## 0.1 — first implementation
* Prayer times (14 methods), tabular Hijri calendar, sunrise/sunset, four gauges, six styles,
  four backgrounds, settings in English and French, validation tooling.
