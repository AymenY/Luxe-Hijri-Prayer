# Changelog

Remaining release steps: `docs/RELEASE_CHECKLIST.md`.

## 1.0.0 — release candidate (2026-11-05)
* New style **Scarlet Noir** (black, red and white).
* **About** at the end of the watch menu: version (also set in manifest.xml), "Proudly Made By
  A. Y.", thanks to the author's family, prayer times computed
  on the watch, tabular Hijri calendar, Quran text from Tanzil.net (CC BY 3.0), fonts (SIL OFL),
  privacy (no data leaves the watch).
* New style **E-Ink**: black ink on white paper like an electronic-paper screen; flat palette
  colours without shadow or glow, the mosque illustration printed as an inverted ink drawing,
  daylight ring and Moon dial in greys, red seconds hand.
* Connect IQ 3 watches (51 models, 96–128 KB of memory): a **digital e-paper face** replaces the
  simplified vector dial — 1-bit IBM Plex fonts, dithered band behind the time, date and Hijri
  date, next prayer (Jumu'ah on Fridays) and countdown pill, steps ring, heart rate, battery, Moon
  phase; setting Digital face: automatic (dark between sunset and sunrise), light or dark; AMOLED
  always-on: the time alone, shifted every minute. No analog fonts or vector art in memory there.
* Digits everywhere in **IBM Plex Sans Condensed** (owner feedback: with Barlow, 6, 8 and 9 — and
  sometimes 5 and 6 — looked alike on the fenix 7X Pro): text fonts of the three families, the
  Western digits of the Hijri date and the 12 / 3 / 6 / 9 numerals; same digit height, layout unchanged.
* Hijri date on two lines (day and month, then the year and AH) and larger: Arabic pieces 14 px
  at 280 px (was 12), Latin script in the small text font (was the extra-small one).
* **Friday**: Dhuhr becomes Jumu'ah (الجمعة) at a fixed time, 12:30 by default (setting
  Jumu'ah time, HHMM, 0 = computed Dhuhr). From 00:00 until Asr the Friday dial is shown: Sidi Bou
  Said blue wrought iron with forged lyres, a few sprigs of jasmine and geranium, gold hour ring,
  and the greeting جمعة مباركة (not a verse) in the verse area. Setting Friday design to turn it
  off. Vector version on Connect IQ 3 watches. Unit test for the Jumu'ah time.
* Two high-contrast styles readable without the backlight on MIP screens: **Ember Gold** (black,
  white, red, orange, gold) and **Oasis Gold** (black, white, blue, green, gold). Flat colours
  taken from the 64-colour palette, no gradient, glow or dithering.
* Black marble background: plain stone slab, without the arch window and the rosette.
* MIP watches: blues made purer before the palette conversion (Luxury Blue looked green on the
  fēnix 7X Pro); black marble with bold gold and quartz veins; night sky with a Milky Way and
  larger stars (both backgrounds were nearly empty on MIP screens).
* Store preparation: listing and privacy texts (EN/FR), release checklist, Store package signed
  with the owner's permanent key (GitHub secret `CIQ_DEVELOPER_KEY`, key file deleted after
  each job), development notes removed.
* Hijri date with Arabic numerals by default.
* Vector variant for 51 Connect IQ 3 watches (fēnix 5 / 6, Forerunner 245 / 645 / 745 / 935 /
  945, MARQ Gen 1, Venu, vívoactive 3 / 4…): no HD images or buffers, selected per device in
  `monkey.jungle`; string resources reduced from 646 to 219 (Connect IQ 3 limit about 254); the
  per-prayer adjustments are numbers (settings renamed AdjustFajr…AdjustIsha). 121 models.
* 70 watch models from the SDK catalogue (was 33): fēnix 8 Pro, fēnix 9 / 9 Pro / E, Enduro 4,
  Forerunner 170 / 570 / 70 / 970, Venu 4, vívoactive 6, MARQ 3, Instinct AMOLED, D2 Mach 2,
  Descent Mk3 / G2, Approach S50 / S70 / S72; new 466 px resource set (fēnix 9 Pro 51 mm).

## Preview 0.9
* Date block in a lighter weight (Barlow Semi Condensed Medium), month without the year.
* Hijri date larger (12 px at 280 px instead of 11) and in the text colour.
* Prayer names in Arabic in the cartouches (setting *Prayer names*: Arabic / Latin script).

## Preview 0.8
* Per-prayer adjustment (−30…+30 min for Fajr, Dhuhr, Asr, Maghrib, Isha) in the settings and the
  watch menu (Prayers), to match a mosque timetable; unit test `testPrayerAdjustment`.

## Preview 0.7
* Moon dial (phase drawn as seen tonight, lunation ring, illuminated fraction) as a gauge source,
  default for gauge 3 instead of calories; validated against astral (Moon age within 0.8 days).
* Automatic location: the prayer times follow the watch's GPS position (setting *Location*).
* Battery line: larger text in the text colour, coloured level (green, orange, warning).
* Hour and minute hands longer and wider, with white lume inserts.
* Mawaqit: not integrated — its API is private (search endpoint answers 401 without a token).

## Preview 0.6
* On-watch settings menu (watch face → Settings): every setting, verse check boxes, and the
  prayer location from the watch's last GPS position — works for sideloaded builds.
* Dial numerals in Arabic (12 3 6 9) or Indian (Eastern Arabic) digits, drawn as HD bitmaps.
* Hijri date (Arabic script) with Indian or Arabic digits.
* The verse is drawn as 4 adjacent glyphs (a wide crisp glyph was split on the watch).

## Preview 0.5 (after the first test on a fēnix 7X Pro)
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
