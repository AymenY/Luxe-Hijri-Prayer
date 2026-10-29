#!/usr/bin/env python3
"""Validate the prayer-time, sunrise/sunset and Hijri algorithms against independent references.

References (installed from PyPI, see tools/requirements.txt):
  * adhanpy     - port of the Batoul Apps "Adhan" library (Meeus-based solar model)
  * astral      - NOAA-based sunrise/sunset
  * convertdate - arithmetical (tabular) Islamic calendar
  * hijridate   - Umm al-Qura calendar (official Saudi calendar), used to measure differences

The algorithms checked are tools/luxe_ref/calc.py, the line-by-line mirror of the Monkey C code.
Exit status is non-zero if any tolerance is exceeded. A report is written to
docs/validation-report.md.
"""
import datetime as dt
import os
import sys
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(__file__))
from luxe_ref import calc  # noqa: E402

# convertdate imports pymeeus for unrelated calendars; it is not needed for the Islamic module.
for _m in ["pymeeus", "pymeeus.Angle", "pymeeus.Epoch", "pymeeus.Sun", "pymeeus.Earth", "pymeeus.Coordinates"]:
    sys.modules.setdefault(_m, mock.MagicMock())

from adhanpy.PrayerTimes import PrayerTimes  # noqa: E402
from adhanpy.calculation.CalculationParameters import CalculationParameters  # noqa: E402
from adhanpy.calculation.HighLatitudeRule import HighLatitudeRule  # noqa: E402
from adhanpy.calculation.Madhab import Madhab  # noqa: E402
from astral import Observer  # noqa: E402
from astral.sun import sunrise as astral_sunrise, sunset as astral_sunset  # noqa: E402
from convertdate import islamic  # noqa: E402
from hijridate import Gregorian  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCATIONS = [
    # name, lat, lon, tz, method index, asr factor
    ("Djerba (Houmt Souk), TN", 33.8754, 10.8575, "Africa/Tunis", 0, 1),
    ("Tunis, TN", 36.8065, 10.1815, "Africa/Tunis", 0, 1),
    ("Makkah, SA", 21.4225, 39.8262, "Asia/Riyadh", 4, 1),
    ("Paris, FR", 48.8566, 2.3522, "Europe/Paris", 11, 1),
    ("New York, US", 40.7128, -74.0060, "America/New_York", 2, 1),
    ("Karachi, PK (Hanafi)", 24.8607, 67.0011, "Asia/Karachi", 5, 2),
    ("Cairo, EG", 30.0444, 31.2357, "Africa/Cairo", 3, 1),
    ("Singapore", 1.3521, 103.8198, "Asia/Singapore", 9, 1),
    ("London, GB", 51.5074, -0.1278, "Europe/London", 1, 1),
    ("Oslo, NO (high latitude)", 59.9139, 10.7522, "Europe/Oslo", 1, 1),
]
NAMES = ["Fajr", "Sunrise", "Dhuhr", "Asr", "Sunset", "Maghrib", "Isha"]
TOL_MIN = 2  # minutes; both models round to the minute and differ slightly in solar model
TOL_HIGH_LAT = 3  # minutes, latitude > 55 degrees (refraction/solar-model sensitivity grows)
TOL_GRAZING = 10  # minutes, Fajr/Isha within 1 h of solar midnight: the sun barely reaches the angle,
                  # so a 0.01 deg difference in declination moves the time by several minutes
TOL_ADJUSTED = 20  # minutes, Fajr/Isha replaced by a high-latitude rule (rules are defined differently)


def tz_hours(tz, day):
    return ZoneInfo(tz).utcoffset(dt.datetime(day.year, day.month, day.day, 12)) .total_seconds() / 3600.0


def epoch_day(day):
    return (day - dt.date(1970, 1, 1)).days


def adhan_times(lat, lon, day, method, asr_factor):
    fa, ia, imin = calc.METHODS[method]
    p = CalculationParameters(fajr_angle=fa, isha_angle=ia, isha_interval=imin)
    p.madhab = Madhab.HANAFI if asr_factor == 2 else Madhab.SHAFI
    p.high_latitude_rule = HighLatitudeRule.MIDDLE_OF_THE_NIGHT
    pt = PrayerTimes((lat, lon), dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc),
                     calculation_parameters=p)
    return [pt.fajr, pt.sunrise, pt.dhuhr, pt.asr, None, pt.maghrib, pt.isha]


def validate_prayers(report):
    worst = 0
    report.append("## Prayer times vs adhanpy (independent implementation)\n")
    report.append("Every 5th day of 2026 plus DST-change days; tolerance %d min.\n" % TOL_MIN)
    report.append("Days on which Fajr/Isha were replaced by the high-latitude rule are excluded from the max "
                  "column (rules differ between libraries) and checked with a %d min tolerance instead.\n" % TOL_ADJUSTED)
    report.append("| Location | Method | Days | Max abs diff (min) Fajr/Sunrise/Dhuhr/Asr/Maghrib/Isha | High-lat adjusted days |")
    report.append("|---|---|---|---|---|")
    days = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(0, 365, 5)]
    days += [dt.date(2026, 3, 29), dt.date(2026, 3, 30), dt.date(2026, 10, 25), dt.date(2026, 3, 8),
             dt.date(2026, 11, 1), dt.date(2024, 2, 29), dt.date(2027, 6, 21), dt.date(2026, 12, 21)]
    failures = []
    for name, lat, lon, tz, method, asr in LOCATIONS:
        mx = [0] * 7
        adjusted_days = 0
        for day in days:
            tzh = tz_hours(tz, day)
            ours = calc.compute_day(epoch_day(day), lat, lon, tzh, method, asr, calc.HL_MIDDLE)
            raw = calc.compute_day(epoch_day(day), lat, lon, tzh, method, asr, calc.HL_NONE)
            adjusted = [ours[i] != raw[i] for i in range(7)]
            adjusted_days += 1 if any(adjusted) else 0
            ref = adhan_times(lat, lon, day, method, asr)
            # adhan's Middle-of-the-night rule uses sunset -> *next day's* sunrise as the night,
            # PrayTimes (and this watch face) use today's sunrise + 24h. Detect when adhan clamped.
            nxt = adhan_times(lat, lon, day + dt.timedelta(days=1), method, asr)
            prv = adhan_times(lat, lon, day - dt.timedelta(days=1), method, asr)
            if ref[6] is not None and abs((ref[6] - ref[5]) - (nxt[1] - ref[5]) / 2).total_seconds() < 61:
                adjusted[6] = True
            if ref[0] is not None and abs((ref[1] - ref[0]) - (ref[1] - prv[5]) / 2).total_seconds() < 61:
                adjusted[0] = True
            for i in (0, 1, 2, 3, 5, 6):
                mo = calc.moment(epoch_day(day), ours[i], tzh)
                if ref[i] is None or mo is None:
                    if (ref[i] is None) != (mo is None):
                        failures.append("%s %s %s: one side undefined" % (name, day, NAMES[i]))
                    continue
                diff = abs(mo - ref[i].timestamp()) / 60.0
                tol = TOL_ADJUSTED if adjusted[i] else (TOL_HIGH_LAT if lat > 55 else TOL_MIN)
                if i in (0, 6) and abs(((ours[i] - ours[2]) % 24.0) - 12.0) < 1.0:
                    tol = max(tol, TOL_GRAZING)
                if not adjusted[i]:
                    mx[i] = max(mx[i], diff)
                if diff > tol:
                    failures.append("%s %s %s: %.1f min" % (name, day, NAMES[i], diff))
        worst = max(worst, max(mx))
        report.append("| %s | %d | %d | %s | %d |" % (name, method, len(days),
                      " / ".join("%.0f" % mx[i] for i in (0, 1, 2, 3, 5, 6)), adjusted_days))
    report.append("")
    return failures


def validate_sun(report):
    report.append("## Sunrise / sunset vs astral (NOAA algorithm)\n")
    report.append("| Location | Max abs diff sunrise (min) | Max abs diff sunset (min) |")
    report.append("|---|---|---|")
    failures = []
    for name, lat, lon, tz, method, asr in LOCATIONS:
        if lat > 55:
            continue
        mr = ms = 0
        for i in range(0, 365, 3):
            day = dt.date(2026, 1, 1) + dt.timedelta(days=i)
            tzh = tz_hours(tz, day)
            t = calc.compute_day(epoch_day(day), lat, lon, tzh, method, asr, calc.HL_MIDDLE)
            obs = Observer(latitude=lat, longitude=lon)
            r = astral_sunrise(obs, day, tzinfo=ZoneInfo(tz)).timestamp()
            s = astral_sunset(obs, day, tzinfo=ZoneInfo(tz)).timestamp()
            dr = abs(calc.moment(epoch_day(day), t[1], tzh) - r) / 60
            ds = abs(calc.moment(epoch_day(day), t[4], tzh) - s) / 60
            mr, ms = max(mr, dr), max(ms, ds)
            if dr > TOL_MIN or ds > TOL_MIN:
                failures.append("%s %s sunrise/sunset diff %.1f/%.1f" % (name, day, dr, ds))
        report.append("| %s | %.1f | %.1f |" % (name, mr, ms))
    report.append("")
    return failures


def validate_djerba_table(report):
    report.append("## Djerba sample timetable (computed, Tunisia method 18°/18°, Asr standard)\n")
    report.append("| Date | Fajr | Sunrise | Dhuhr | Asr | Maghrib | Isha | adhanpy Fajr/Dhuhr/Asr/Maghrib/Isha |")
    report.append("|---|---|---|---|---|---|---|---|")
    tz = ZoneInfo("Africa/Tunis")
    for day in [dt.date(2026, 1, 15), dt.date(2026, 3, 20), dt.date(2026, 6, 21), dt.date(2026, 9, 22),
                dt.date(2026, 10, 29), dt.date(2026, 12, 21)]:
        tzh = tz_hours("Africa/Tunis", day)
        t = calc.compute_day(epoch_day(day), 33.8754, 10.8575, tzh, 0, 1, calc.HL_MIDDLE)
        fm = []
        for i in (0, 1, 2, 3, 5, 6):
            m = calc.to_minutes(t[i])
            fm.append("%02d:%02d" % (m // 60, m % 60))
        ref = adhan_times(33.8754, 10.8575, day, 0, 1)
        rf = " ".join(ref[i].astimezone(tz).strftime("%H:%M") for i in (0, 2, 3, 5, 6))
        report.append("| %s | %s | %s |" % (day, " | ".join(fm), rf))
    report.append("")


def validate_high_latitude(report):
    report.append("## High-latitude behaviour (Oslo, MWL, 21 June 2026)\n")
    day = dt.date(2026, 6, 21)
    tzh = tz_hours("Europe/Oslo", day)
    report.append("| Rule | Fajr | Isha |")
    report.append("|---|---|---|")
    for rule, label in [(calc.HL_NONE, "None"), (calc.HL_MIDDLE, "Middle of the night"),
                        (calc.HL_SEVENTH, "One-seventh"), (calc.HL_ANGLE, "Angle-based")]:
        t = calc.compute_day(epoch_day(day), 59.9139, 10.7522, tzh, 1, 1, rule)

        def f(h):
            if h is None:
                return "undefined (shown as --:--)"
            m = calc.to_minutes(h) % 1440
            return "%02d:%02d" % (m // 60, m % 60)
        report.append("| %s | %s | %s |" % (label, f(t[0]), f(t[6])))
    report.append("")


def validate_next_prayer(report):
    failures = []
    report.append("## Next-prayer / countdown transitions (Djerba, UTC+1)\n")
    lat, lon, tzh = 33.8754, 10.8575, 1.0
    day = dt.date(2026, 10, 29)
    t = calc.compute_day(epoch_day(day), lat, lon, tzh, 0, 1, calc.HL_MIDDLE)
    isha = calc.moment(epoch_day(day), t[6], tzh)
    t2 = calc.compute_day(epoch_day(day) + 1, lat, lon, tzh, 0, 1, calc.HL_MIDDLE)
    fajr2 = calc.moment(epoch_day(day) + 1, t2[0], tzh)
    cases = [
        ("1 s before Isha", isha - 1, (calc.ISHA, isha)),
        ("exactly at Isha", isha, (calc.FAJR, fajr2)),
        ("23:59:59 local", int(dt.datetime(2026, 10, 29, 23, 59, 59, tzinfo=dt.timezone(dt.timedelta(hours=1))).timestamp()), (calc.FAJR, fajr2)),
        ("00:00:00 local", int(dt.datetime(2026, 10, 30, 0, 0, 0, tzinfo=dt.timezone(dt.timedelta(hours=1))).timestamp()), (calc.FAJR, fajr2)),
    ]
    report.append("| Case | Next | Countdown |")
    report.append("|---|---|---|")
    for label, now, exp in cases:
        got = calc.next_prayer(now, tzh, lat, lon, 0, 1, calc.HL_MIDDLE)
        ok = got == exp
        if not ok:
            failures.append("next prayer %s: got %s expected %s" % (label, got, exp))
        report.append("| %s | %s | %s |" % (label, NAMES[got[0]], calc.countdown_text(got[1] - now)))
    for secs, exp in [(1, "1m"), (59, "1m"), (60, "1m"), (61, "2m"), (3599, "1h00"), (3600, "1h00"), (3601, "1h01"), (5000, "1h24")]:
        if calc.countdown_text(secs) != exp:
            failures.append("countdown %d -> %s, expected %s" % (secs, calc.countdown_text(secs), exp))
    report.append("")
    return failures


def validate_hijri(report):
    failures = []
    start, end = dt.date(1950, 1, 1), dt.date(2077, 12, 31)
    n = 0
    uq_diff = {}
    d = start
    while d <= end:
        ed = epoch_day(d)
        ours = calc.hijri_for_epoch_day(ed, 0)
        ref = islamic.from_gregorian(d.year, d.month, d.day)
        if tuple(ours) != tuple(ref):
            failures.append("hijri %s: %s vs convertdate %s" % (d, ours, ref))
        if dt.date(1937, 3, 14) <= d <= dt.date(2077, 11, 16):
            h = Gregorian(d.year, d.month, d.day).to_hijri()
            uq = calc.hijri_to_jdn(h.year, h.month, h.day)  # tabular JDN of the UQ label
            delta = uq - (ed + calc.UNIX_EPOCH_JDN)
            uq_diff[delta] = uq_diff.get(delta, 0) + 1
        n += 1
        d += dt.timedelta(days=1)
    report.append("## Hijri calendar\n")
    report.append("* Tabular algorithm vs convertdate.islamic: %d consecutive days (1950-2077) compared, %d mismatches."
                  % (n, len(failures)))
    total = sum(uq_diff.values())
    parts = ", ".join("%+d day: %.1f%%" % (k, 100.0 * v / total) for k, v in sorted(uq_diff.items()))
    report.append("* Difference to the Umm al-Qura calendar (hijridate) over the same range: " + parts + ".")
    report.append("  This is why the watch face offers a -2..+2 day 'Hijri Date Correction'.\n")

    # correction across month / year boundaries
    report.append("| Gregorian | Correction | Hijri (tabular) |")
    report.append("|---|---|---|")
    jdn_new_year = calc.hijri_to_jdn(1448, 1, 1)
    ed0 = jdn_new_year - calc.UNIX_EPOCH_JDN
    for k in range(-2, 3):
        for corr in (-2, 0, 2):
            ed = ed0 + k
            y, m, dd = calc.civil_from_days(ed)
            h = calc.hijri_for_epoch_day(ed, corr)
            report.append("| %04d-%02d-%02d | %+d | %d-%02d-%02d |" % (y, m, dd, corr, *h))
    # invariants: correction == shifting the day
    for ed in range(ed0 - 400, ed0 + 400):
        for corr in range(-2, 3):
            if calc.hijri_for_epoch_day(ed, corr) != calc.hijri_for_epoch_day(ed + corr, 0):
                failures.append("correction invariant failed at %d" % ed)
        y, m, dd = calc.hijri_for_epoch_day(ed, 0)
        if not (1 <= m <= 12 and 1 <= dd <= 30):
            failures.append("out-of-range hijri %s" % ((y, m, dd),))
    # civil date + weekday vs Python
    for ed in range(-1000, 40000, 7):
        d = dt.date(1970, 1, 1) + dt.timedelta(days=ed)
        if calc.civil_from_days(ed) != (d.year, d.month, d.day):
            failures.append("civil_from_days %d" % ed)
        if calc.day_of_week(ed) != (d.isoweekday() % 7):
            failures.append("day_of_week %d" % ed)
    report.append("")
    return failures


def main():
    report = ["# Calculation validation report\n",
              "Generated by `tools/validate_calculations.py`. The algorithms under test are in "
              "`tools/luxe_ref/calc.py`, a line-by-line mirror of `source/PrayerTimes.mc`, "
              "`source/HijriCalendar.mc` and `source/CivilDate.mc`.\n"]
    failures = []
    failures += validate_prayers(report)
    failures += validate_sun(report)
    validate_djerba_table(report)
    validate_high_latitude(report)
    failures += validate_next_prayer(report)
    failures += validate_hijri(report)
    report.append("## Result\n")
    report.append("**%s** (%d failures)" % ("PASS" if not failures else "FAIL", len(failures)))
    for f in failures[:50]:
        report.append("* " + f)
    out = os.path.join(ROOT, "docs", "validation-report.md")
    with open(out, "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report[-(min(len(failures), 50) + 2):]))
    print("report:", out)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
