import Toybox.Lang;

// Tabular (arithmetical) Islamic calendar, civil epoch: 1 Muharram 1 AH = JDN 1948440
// (Friday 16 July 622, Julian). Leap years 2, 5, 7, 10, 13, 16, 18, 21, 24, 26, 29 of the
// 30-year cycle. The result can differ by one or two days from moon sighting or from the
// Umm al-Qura calendar; the user-facing "Hijri Date Correction" setting compensates.
// Mirrored in tools/luxe_ref/calc.py and validated in tools/validate_calculations.py.
module HijriCalendar {

    const EPOCH_JDN = 1948440;

    function toJdn(y as Number, m as Number, d as Number) as Number {
        return d + (59 * (m - 1) + 1) / 2 + (y - 1) * 354 + (3 + 11 * y) / 30 + EPOCH_JDN - 1;
    }

    // ceil(a / b) for b > 0 using truncating integer division.
    function ceilDiv(a as Number, b as Number) as Number {
        if (a >= 0) {
            return (a + b - 1) / b;
        }
        return -((-a) / b);
    }

    // Julian Day Number -> [year, month (1-12), day (1-30)].
    function fromJdn(jdn as Number) as Array<Number> {
        var y = (30 * (jdn - EPOCH_JDN) + 10646) / 10631;
        var m = ceilDiv(2 * (jdn - 29 - toJdn(y, 1, 1)), 59) + 1;
        if (m > 12) {
            m = 12;
        }
        if (m < 1) {
            m = 1;
        }
        var d = jdn - toJdn(y, m, 1) + 1;
        return [y, m, d];
    }

    // Hijri date for a local epoch day with a correction of -2..+2 days. Shifting the day
    // number (rather than the day field) keeps month and year transitions consistent.
    function forEpochDay(epochDay as Number, correction as Number) as Array<Number> {
        return fromJdn(epochDay + CivilDate.UNIX_EPOCH_JDN + correction);
    }
}
