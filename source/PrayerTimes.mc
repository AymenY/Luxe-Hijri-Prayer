import Toybox.Lang;
import Toybox.Math;

// Islamic prayer times and sunrise/sunset, computed locally from user-configured
// coordinates. Algorithm: PrayTimes.org v2.3 (Hamid Zarrabi-Zadeh), single iteration,
// refraction/semi-diameter 0.833 deg, no elevation correction. Validated against the
// independent "adhan" implementation and NOAA sunrise/sunset in
// tools/validate_calculations.py (mirror: tools/luxe_ref/calc.py).
module PrayerTimes {

    const FAJR = 0;
    const SUNRISE = 1;
    const DHUHR = 2;
    const ASR = 3;
    const SUNSET = 4;
    const MAGHRIB = 5;
    const ISHA = 6;

    // Indices of the five prayers inside a computed day.
    const PRAYERS = [0, 2, 3, 5, 6];

    const HL_NONE = 0;
    const HL_MIDDLE = 1;
    const HL_SEVENTH = 2;
    const HL_ANGLE = 3;

    const RISE_SET_ANGLE = 0.833d;
    const D2R = 0.017453292519943295d;

    // [fajr angle, isha angle (0 = use minutes), isha minutes after maghrib]
    // Order must match the "CalcMethod" list in resources/settings/settings.xml.
    const METHODS = [
        [18.0d, 18.0d, 0],  // 0 Tunisia (Ministry of Religious Affairs)
        [18.0d, 17.0d, 0],  // 1 Muslim World League
        [15.0d, 15.0d, 0],  // 2 ISNA (North America)
        [19.5d, 17.5d, 0],  // 3 Egyptian General Authority of Survey
        [18.5d, 0.0d, 90],  // 4 Umm al-Qura, Makkah
        [18.0d, 18.0d, 0],  // 5 University of Islamic Sciences, Karachi
        [19.5d, 0.0d, 90],  // 6 Gulf region
        [18.0d, 17.5d, 0],  // 7 Kuwait
        [18.0d, 0.0d, 90],  // 8 Qatar
        [20.0d, 18.0d, 0],  // 9 MUIS Singapore
        [18.0d, 17.0d, 0],  // 10 Diyanet Turkey (angles only)
        [12.0d, 12.0d, 0],  // 11 UOIF France
        [18.0d, 17.0d, 0],  // 12 Algeria
        [19.0d, 17.0d, 0]   // 13 Morocco
    ];

    function fix(a as Decimal, b as Decimal) as Decimal {
        var r = a - b * Math.floor(a / b);
        if (r < 0) {
            r += b;
        }
        return r;
    }

    function dsin(x as Decimal) as Decimal {
        return Math.sin(x * D2R);
    }

    function dcos(x as Decimal) as Decimal {
        return Math.cos(x * D2R);
    }

    // d = days since J2000.0. Returns [declination (deg), equation of time (h)].
    function sunPosition(d as Decimal) as Array<Decimal> {
        var g = fix(357.529d + 0.98560028d * d, 360.0d);
        var q = fix(280.459d + 0.98564736d * d, 360.0d);
        var l = fix(q + 1.915d * dsin(g) + 0.020d * dsin(2.0d * g), 360.0d);
        var e = 23.439d - 0.00000036d * d;
        var ra = Math.atan2(dcos(e) * dsin(l), dcos(l)) / D2R / 15.0d;
        var eqt = q / 15.0d - fix(ra, 24.0d);
        var decl = Math.asin(dsin(e) * dsin(l)) / D2R;
        return [decl, eqt];
    }

    function midDay(d0 as Decimal, t as Decimal) as Decimal {
        var p = sunPosition(d0 + t);
        return fix(12.0d - p[1], 24.0d);
    }

    // Time at which the sun is `angle` degrees below the horizon; null if never reached.
    function angleTime(d0 as Decimal, lat as Decimal, angle as Decimal, t as Decimal, ccw as Boolean) as Decimal? {
        var decl = sunPosition(d0 + t)[0];
        var noon = midDay(d0, t);
        var arg = (-dsin(angle) - dsin(decl) * dsin(lat)) / (dcos(decl) * dcos(lat));
        if (arg > 1.0d || arg < -1.0d) {
            return null;
        }
        var tt = Math.acos(arg) / D2R / 15.0d;
        return ccw ? noon - tt : noon + tt;
    }

    function asrTime(d0 as Decimal, lat as Decimal, factor as Number, t as Decimal) as Decimal? {
        var decl = sunPosition(d0 + t)[0];
        var diff = lat - decl;
        if (diff < 0) {
            diff = -diff;
        }
        var angle = -Math.atan(1.0d / (factor + Math.tan(diff * D2R))) / D2R;
        return angleTime(d0, lat, angle, t, false);
    }

    // Returns 7 local times in hours after local midnight of `epochDay` (entries may be
    // null when undefined, e.g. Fajr/Isha at high latitude with no adjustment rule).
    // Values can be < 0 or >= 24 when the event falls on the previous/next calendar day.
    function computeDay(epochDay as Number, lat as Decimal, lon as Decimal, tzHours as Decimal,
                        method as Number, asrFactor as Number, highLat as Number) as Array {
        var params = METHODS[method] as Array;
        var fajrAngle = params[0] as Decimal;
        var ishaAngle = params[1] as Decimal;
        var ishaMin = params[2] as Number;
        var d0 = epochDay - 10957.5d - lon / 360.0d;

        var times = new [7];
        times[FAJR] = angleTime(d0, lat, fajrAngle, 5.0d / 24.0d, true);
        times[SUNRISE] = angleTime(d0, lat, RISE_SET_ANGLE, 6.0d / 24.0d, true);
        times[DHUHR] = midDay(d0, 12.0d / 24.0d);
        times[ASR] = asrTime(d0, lat, asrFactor, 13.0d / 24.0d);
        times[SUNSET] = angleTime(d0, lat, RISE_SET_ANGLE, 18.0d / 24.0d, false);
        times[MAGHRIB] = times[SUNSET];
        times[ISHA] = (ishaMin == 0) ? angleTime(d0, lat, ishaAngle, 18.0d / 24.0d, false) : null;

        var shift = tzHours - lon / 15.0d;
        for (var i = 0; i < 7; i++) {
            if (times[i] != null) {
                times[i] = (times[i] as Decimal) + shift;
            }
        }

        var sunrise = times[SUNRISE];
        var sunset = times[SUNSET];
        if (highLat != HL_NONE && sunrise != null && sunset != null) {
            var night = fix((sunrise as Decimal) - (sunset as Decimal), 24.0d);
            var p = nightPortion(highLat, fajrAngle, night);
            if (times[FAJR] == null || fix((sunrise as Decimal) - (times[FAJR] as Decimal), 24.0d) > p) {
                times[FAJR] = (sunrise as Decimal) - p;
            }
            if (ishaMin == 0) {
                p = nightPortion(highLat, ishaAngle, night);
                if (times[ISHA] == null || fix((times[ISHA] as Decimal) - (sunset as Decimal), 24.0d) > p) {
                    times[ISHA] = (sunset as Decimal) + p;
                }
            }
        }

        if (ishaMin != 0 && times[MAGHRIB] != null) {
            times[ISHA] = (times[MAGHRIB] as Decimal) + ishaMin / 60.0d;
        }
        return times;
    }

    function nightPortion(highLat as Number, angle as Decimal, night as Decimal) as Decimal {
        if (highLat == HL_ANGLE) {
            return angle / 60.0d * night;
        }
        if (highLat == HL_SEVENTH) {
            return night / 7.0d;
        }
        return night / 2.0d;
    }

    // Rounded minutes after local midnight, or null.
    function toMinutes(hours) as Number? {
        if (hours == null) {
            return null;
        }
        return Math.floor((hours as Decimal) * 60.0d + 0.5d).toNumber();
    }

    // UTC epoch seconds of a local time (rounded to the minute), or null.
    function moment(epochDay as Number, hours, offsetSeconds as Number) as Long? {
        var m = toMinutes(hours);
        if (m == null) {
            return null;
        }
        return epochDay.toLong() * 86400l + m * 60 - offsetSeconds;
    }
}

// Caches the computed days so that the trigonometry runs only when the local date, the
// UTC offset or a calculation setting changes (not on every one-second redraw).
class PrayerSchedule {

    var lat as Decimal = 0.0d;
    var lon as Decimal = 0.0d;
    var method as Number = 0;
    var asrFactor as Number = 1;
    var highLat as Number = 1;

    hidden var mKey as String = "";
    hidden var mDay as Number = 0;
    hidden var mOffset as Number = 0;
    hidden var mDays as Array = [];

    function initialize() {
    }

    function configure(latitude as Decimal, longitude as Decimal, calcMethod as Number,
                       asr as Number, highLatRule as Number) as Void {
        lat = latitude;
        lon = longitude;
        method = calcMethod;
        asrFactor = asr;
        highLat = highLatRule;
        mKey = "";
    }

    // Recomputes today, tomorrow and the day after (for polar edge cases) when needed.
    function update(nowUtc as Number, offsetSeconds as Number) as Void {
        var day = CivilDate.localEpochDay(nowUtc, offsetSeconds);
        var key = day.toString() + "/" + offsetSeconds.toString();
        if (key.equals(mKey)) {
            return;
        }
        mKey = key;
        mDay = day;
        mOffset = offsetSeconds;
        var tz = offsetSeconds / 3600.0d;
        mDays = [
            PrayerTimes.computeDay(day, lat, lon, tz, method, asrFactor, highLat),
            PrayerTimes.computeDay(day + 1, lat, lon, tz, method, asrFactor, highLat),
            PrayerTimes.computeDay(day + 2, lat, lon, tz, method, asrFactor, highLat)
        ];
    }

    // Local time in minutes after midnight of day `dayIndex` (0 = today, 1 = tomorrow) for
    // event `index` (PrayerTimes.FAJR..ISHA), or null when undefined.
    function minutes(dayIndex as Number, index as Number) as Number? {
        if (mDays.size() <= dayIndex) {
            return null;
        }
        return PrayerTimes.toMinutes((mDays[dayIndex] as Array)[index]);
    }

    // UTC moment of event `index` on day `dayIndex` (0 = today), or null when undefined.
    function momentOf(dayIndex as Number, index as Number) as Long? {
        if (mDays.size() <= dayIndex) {
            return null;
        }
        return PrayerTimes.moment(mDay + dayIndex, (mDays[dayIndex] as Array)[index], mOffset);
    }

    // [prayer index, UTC moment as Long, day index] of the next prayer strictly after
    // `nowUtc`, or null when no prayer can be computed in the next three days.
    function next(nowUtc as Number) as Array? {
        var list = upcoming(nowUtc, 1);
        return (list.size() > 0) ? list[0] as Array : null;
    }

    // Up to `count` upcoming prayers, each [prayer index, UTC moment as Long, day index].
    function upcoming(nowUtc as Number, count as Number) as Array {
        var out = [];
        for (var dd = 0; dd < mDays.size(); dd++) {
            var times = mDays[dd] as Array;
            for (var k = 0; k < 5; k++) {
                var p = PrayerTimes.PRAYERS[k] as Number;
                var mo = PrayerTimes.moment(mDay + dd, times[p], mOffset);
                if (mo != null && mo > nowUtc) {
                    out.add([p, mo, dd]);
                    if (out.size() >= count) {
                        return out;
                    }
                }
            }
        }
        return out;
    }
}
