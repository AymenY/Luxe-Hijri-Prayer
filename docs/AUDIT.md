# Audit report — Luxe Hijri Prayer

Date: 2026-10-29. Repository `aymeny/luxe-hijri-prayer`, branch `claude/salut-mon-ami-b3pero`.

## 1. What existed before this work

| Item | Finding |
|---|---|
| Git history | One commit, `bf70ffb Initial commit` (the baseline checkpoint; nothing was overwritten). |
| Branches | `main` and `claude/salut-mon-ami-b3pero`, identical. |
| Files | `README.md` containing only the title `# Luxe-Hijri-Prayer`. |
| Monkey C sources, manifest, jungle | None. |
| Resources (strings, settings, fonts, images) | None. |
| Tests | None. |
| ZIP archives / earlier versions | None in the repository or in the working environment. The specification refers to archives, preview images and an earlier decision to avoid the Positioning API; none of these files were supplied to this session. |

### Classification

* **Working:** nothing (no implementation existed).
* **Incomplete:** the project name only.
* **Broken:** nothing to break; no placeholder or invalid code was found.

Consequence: the project was implemented from the master specification. All design decisions
stated in the specification were preserved (Luxury Blue default, analog-digital luxury dial,
long seconds hand, four gauges with the specified defaults, Gregorian + adjustable Hijri dates,
prayer countdown, sunrise/sunset, six presets, four backgrounds, eight Ayah choices, Djerba
default location, manual coordinates instead of a Positioning API call, excluded weather /
temperature / wind / altitude / compass data). The previously approved concept images were not
available; the new backgrounds are **generated vector graphics**, not reconstructions of those
images (see section 3).

## 2. Environment limitations (verified)

| Limitation | Effect |
|---|---|
| `developer.garmin.com` is blocked by the network policy of this environment (HTTP 403 at the proxy). | The Connect IQ SDK, the device files (`fenix7xpro`) and the simulator could not be installed. **Nothing was compiled with `monkeyc`; no `.prg` or `.iq` file exists.** |
| No physical watch. | No on-device test results. |

What was done instead (all reproducible, see `README.md`):

* Monkey C syntax of every source file parsed with the open-source
  `@markw65/prettier-plugin-monkeyc` parser (`tools/check_project.py`).
* Static project checks: XML validity, resource ids, `@Strings`/`@Properties` references,
  property usage, list sizes vs. code tables, 64-colour palette, font glyph coverage,
  background data (`tools/check_project.py`).
* Algorithms validated against independent libraries through a line-by-line Python mirror
  (`tools/validate_calculations.py`, report in `docs/validation-report.md`).
* Circular layout validated with worst-case English/French content (`tools/check_layout.py`,
  report in `docs/layout-report.md`).
* 280 × 280 reference renders from a Python mirror of the drawing code (`tools/face.py`,
  `docs/previews/`). These are **not** simulator screenshots.
* Monkey C unit tests (`test/LuxeTests.mc`) written for the simulator, **not yet executed**.

## 3. Decisions taken during implementation

| Topic | Decision | Reason |
|---|---|---|
| Display | Colours restricted to the 64-colour MIP palette (channel levels 00/55/AA/FF). | The fēnix 7X Pro is a 64-colour transflective MIP display; other colours are dithered. |
| Backgrounds | Vector geometry (JSON resources) drawn with preset colour roles, instead of photos. | Photos dither badly on 64 colours, cost memory, and cannot follow the six presets. |
| Arabic text | Each Ayah is pre-shaped with HarfBuzz (Amiri Bold) and shipped as one glyph of a custom font. | Device text rendering cannot be relied on for connected Arabic shaping; a font glyph can be drawn in any preset colour. |
| Ayah length | 2:286, 3:8, 48:4, 11:88 and 20:114 show their opening phrase (marked “excerpt” in settings); Al-Ikhlas shows verses 1–2 and 3–4 alternately every minute. | The verse band is about 130 × 44 px; full verses would be illegible. |
| Location | Manual latitude/longitude (default Houmt Souk, Djerba), 0/0 treated as “not set”. | Preserves the earlier decision; no SDK documentation could be checked here to justify a location API for watch faces. |
| Time zone | Watch time zone by default (follows DST), optional manual UTC offset. | Correct DST handling without a time-zone database. |
| Hijri calendar | Tabular (arithmetical) calendar + −2..+2 day correction. | Deterministic, small, verifiable; moon sighting cannot be computed. |
| Seconds hand | Full redraw into a buffered bitmap; `onPartialUpdate` restores only the hand area in low power; automatic fallback when the power budget is exceeded; user option to hide it in low power. | Documented watch-face power model (see `source/LuxeHijriPrayerView.mc`). |
| Gauge labels | Icons (steps, heart, floors, Body Battery, stress) and short units (KCAL, %, KM/MI). | Text labels such as “FLOORS”/“ÉTAGES” do not fit the open bottom of a 24 px ring (found by `tools/check_layout.py`). |
| Sunrise/sunset | Placed in the band under the pivot, between the gauges. | The bottom band is too narrow at the edge of the circle (≈108 px). |
