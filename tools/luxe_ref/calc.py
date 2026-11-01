"""Python mirror of source/PrayerTimes.mc, source/HijriCalendar.mc and source/CivilDate.mc.

This module is a line-by-line reference of the Monkey C algorithms so that they can be
validated on a desktop against independent libraries (see tools/validate_calculations.py)
and used by the preview renderer. Keep it in sync with the Monkey C sources.
"""
import math

# ---------------------------------------------------------------- civil dates
def civil_from_days(days):
    """Epoch day (days since 1970-01-01) -> (year, month, day). Mirrors CivilDate.fromDays."""
    z = days + 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    if m <= 2:
        y += 1
    return y, m, d


def day_of_week(days):
    """0 = Sunday ... 6 = Saturday (1970-01-01 was a Thursday)."""
    return (days + 4) % 7


def local_epoch_day(utc_seconds, offset_seconds):
    return (utc_seconds + offset_seconds) // 86400


# ---------------------------------------------------------------- hijri (tabular)
HIJRI_EPOCH_JDN = 1948440  # 1 Muharram 1 AH = Friday 16 July 622 (Julian), civil epoch
UNIX_EPOCH_JDN = 2440588


def _ceil_div(a, b):
    # b > 0. Written so that it maps 1:1 onto Monkey C truncating division.
    if a >= 0:
        return (a + b - 1) // b
    return -((-a) // b)


def hijri_to_jdn(y, m, d):
    return d + (59 * (m - 1) + 1) // 2 + (y - 1) * 354 + (3 + 11 * y) // 30 + HIJRI_EPOCH_JDN - 1


def hijri_from_jdn(jdn):
    y = (30 * (jdn - HIJRI_EPOCH_JDN) + 10646) // 10631
    m = _ceil_div(2 * (jdn - 29 - hijri_to_jdn(y, 1, 1)), 59) + 1
    if m > 12:
        m = 12
    if m < 1:
        m = 1
    d = jdn - hijri_to_jdn(y, m, 1) + 1
    return y, m, d


def hijri_for_epoch_day(days, correction):
    return hijri_from_jdn(days + UNIX_EPOCH_JDN + correction)


# ---------------------------------------------------------------- prayer times
# [fajr angle, isha angle (0 => use minutes), isha minutes after maghrib]
METHODS = [
    (18.0, 18.0, 0),    # 0 Tunisia (Ministry of Religious Affairs)
    (18.0, 17.0, 0),    # 1 Muslim World League
    (15.0, 15.0, 0),    # 2 ISNA (North America)
    (19.5, 17.5, 0),    # 3 Egyptian General Authority of Survey
    (18.5, 0.0, 90),    # 4 Umm al-Qura, Makkah
    (18.0, 18.0, 0),    # 5 Univ. of Islamic Sciences, Karachi
    (19.5, 0.0, 90),    # 6 Gulf region
    (18.0, 17.5, 0),    # 7 Kuwait
    (18.0, 0.0, 90),    # 8 Qatar
    (20.0, 18.0, 0),    # 9 MUIS Singapore
    (18.0, 17.0, 0),    # 10 Diyanet Turkey (angles only)
    (12.0, 12.0, 0),    # 11 UOIF France
    (18.0, 17.0, 0),    # 12 Algeria
    (19.0, 17.0, 0),    # 13 Morocco
]

HL_NONE, HL_MIDDLE, HL_SEVENTH, HL_ANGLE = 0, 1, 2, 3
RISE_SET_ANGLE = 0.833

FAJR, SUNRISE, DHUHR, ASR, SUNSET, MAGHRIB, ISHA = range(7)
PRAYERS = (FAJR, DHUHR, ASR, MAGHRIB, ISHA)

D2R = math.pi / 180.0


def _fix(a, b):
    a = a - b * math.floor(a / b)
    return a + b if a < 0 else a


class _Sun:
    def __init__(self, epoch_day, lon):
        # days from J2000.0 at local 0h (jd = 2440587.5 + epochDay - lon/360)
        self.d0 = epoch_day - 10957.5 - lon / 360.0

    def position(self, t):
        d = self.d0 + t
        g = _fix(357.529 + 0.98560028 * d, 360.0)
        q = _fix(280.459 + 0.98564736 * d, 360.0)
        l = _fix(q + 1.915 * math.sin(g * D2R) + 0.020 * math.sin(2 * g * D2R), 360.0)
        e = 23.439 - 0.00000036 * d
        ra = math.atan2(math.cos(e * D2R) * math.sin(l * D2R), math.cos(l * D2R)) / D2R / 15.0
        eqt = q / 15.0 - _fix(ra, 24.0)
        decl = math.asin(math.sin(e * D2R) * math.sin(l * D2R)) / D2R
        return decl, eqt


def compute_day(epoch_day, lat, lon, tz_hours, method, asr_factor, high_lat):
    """Returns 7 local times in hours after local midnight of epoch_day (None if undefined)."""
    fajr_angle, isha_angle, isha_min = METHODS[method]
    sun = _Sun(epoch_day, lon)

    def mid_day(t):
        return _fix(12.0 - sun.position(t)[1], 24.0)

    def angle_time(angle, t, ccw):
        decl = sun.position(t)[0]
        noon = mid_day(t)
        arg = (-math.sin(angle * D2R) - math.sin(decl * D2R) * math.sin(lat * D2R)) / (
            math.cos(decl * D2R) * math.cos(lat * D2R))
        if arg > 1.0 or arg < -1.0:
            return None
        tt = math.acos(arg) / D2R / 15.0
        return noon - tt if ccw else noon + tt

    def asr_time(t):
        decl = sun.position(t)[0]
        angle = -math.atan(1.0 / (asr_factor + math.tan(abs(lat - decl) * D2R))) / D2R
        return angle_time(angle, t, False)

    times = [
        angle_time(fajr_angle, 5.0 / 24, True),
        angle_time(RISE_SET_ANGLE, 6.0 / 24, True),
        mid_day(12.0 / 24),
        asr_time(13.0 / 24),
        angle_time(RISE_SET_ANGLE, 18.0 / 24, False),
        angle_time(RISE_SET_ANGLE, 18.0 / 24, False),
        angle_time(isha_angle, 18.0 / 24, False) if isha_min == 0 else None,
    ]
    shift = tz_hours - lon / 15.0
    times = [None if x is None else x + shift for x in times]

    sunrise, sunset = times[SUNRISE], times[SUNSET]
    if high_lat != HL_NONE and sunrise is not None and sunset is not None:
        night = _fix(sunrise - sunset, 24.0)

        def portion(angle):
            if high_lat == HL_ANGLE:
                return angle / 60.0 * night
            if high_lat == HL_SEVENTH:
                return night / 7.0
            return night / 2.0

        p = portion(fajr_angle)
        if times[FAJR] is None or _fix(sunrise - times[FAJR], 24.0) > p:
            times[FAJR] = sunrise - p
        if isha_min == 0:
            p = portion(isha_angle)
            if times[ISHA] is None or _fix(times[ISHA] - sunset, 24.0) > p:
                times[ISHA] = sunset + p

    if isha_min != 0 and times[MAGHRIB] is not None:
        times[ISHA] = times[MAGHRIB] + isha_min / 60.0
    return times


def to_minutes(hours):
    """Rounded minutes after local midnight (may be negative or >= 1440)."""
    return None if hours is None else int(math.floor(hours * 60.0 + 0.5))


def moment(epoch_day, hours, tz_hours):
    """UTC epoch seconds of a local time, rounded to the minute."""
    m = to_minutes(hours)
    return None if m is None else epoch_day * 86400 + m * 60 - int(round(tz_hours * 3600))


def next_prayer(now_utc, tz_hours, lat, lon, method, asr_factor, high_lat):
    """Returns (prayer index, utc moment) of the next prayer strictly after now."""
    off = int(round(tz_hours * 3600))
    day = local_epoch_day(now_utc, off)
    for dd in (0, 1, 2):
        times = compute_day(day + dd, lat, lon, tz_hours, method, asr_factor, high_lat)
        for p in PRAYERS:
            mo = moment(day + dd, times[p], tz_hours)
            if mo is not None and mo > now_utc:
                return p, mo
    return None, None


def countdown_text(seconds):
    mins = (seconds + 59) // 60
    if mins < 60:
        return "%dm" % mins
    return "%dh%02d" % (mins // 60, mins % 60)
