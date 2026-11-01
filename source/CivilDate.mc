import Toybox.Lang;

// Gregorian calendar helpers working on "epoch days" (days since 1970-01-01 in a
// given local time zone). Pure integer arithmetic, mirrored in tools/luxe_ref/calc.py.
module CivilDate {

    const UNIX_EPOCH_JDN = 2440588;

    // Local epoch day for a UTC timestamp and a UTC offset in seconds.
    function localEpochDay(utcSeconds as Number, offsetSeconds as Number) as Number {
        var t = utcSeconds.toLong() + offsetSeconds;
        var d = t / 86400;
        if (t < 0 && d * 86400 != t) {
            d -= 1;
        }
        return d.toNumber();
    }

    // Epoch day -> [year, month (1-12), day (1-31)] (Howard Hinnant's civil_from_days).
    function fromDays(days as Number) as Array<Number> {
        var z = days + 719468;
        var era = z / 146097;
        var doe = z - era * 146097;
        var yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
        var y = yoe + era * 400;
        var doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
        var mp = (5 * doy + 2) / 153;
        var d = doy - (153 * mp + 2) / 5 + 1;
        var m = (mp < 10) ? mp + 3 : mp - 9;
        if (m <= 2) {
            y += 1;
        }
        return [y, m, d];
    }

    // 0 = Sunday ... 6 = Saturday.
    function dayOfWeek(days as Number) as Number {
        return (days + 4) % 7;
    }
}
