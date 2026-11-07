import Toybox.Lang;
import Toybox.Test;

// Unit tests, run with the Connect IQ simulator (see README "Unit tests").
// Golden values come from tools/luxe_ref/calc.py, which is validated against independent
// libraries by tools/validate_calculations.py.

(:test)
function testCivilDate(logger as Logger) as Boolean {
    var d = CivilDate.fromDays(20755);
    Test.assertEqual(d[0], 2026);
    Test.assertEqual(d[1], 10);
    Test.assertEqual(d[2], 29);
    Test.assertEqual(CivilDate.dayOfWeek(20755), 4); // Thursday
    d = CivilDate.fromDays(19782);
    Test.assertEqual(d[1], 2);
    Test.assertEqual(d[2], 29);
    Test.assertEqual(CivilDate.dayOfWeek(10957), 6); // 2000-01-01 Saturday
    Test.assertEqual(CivilDate.localEpochDay(20755 * 86400 + 86399, 0), 20755);
    Test.assertEqual(CivilDate.localEpochDay(20755 * 86400 - 3600, 3600), 20755);
    Test.assertEqual(CivilDate.localEpochDay(20755 * 86400 - 1, 3600), 20755);
    return true;
}

// Helpers return an error message (or null) and never call Toybox.Test themselves: only the
// (:test) functions below use the Test module. The runner treats every (:test) function as a
// test case, so helpers must not carry that annotation.
function checkHijri(c as Array<Number>) as String? {
    var h = HijriCalendar.forEpochDay(c[0], c[1]);
    if (h[0] != c[2] || h[1] != c[3] || h[2] != c[4]) {
        return "day " + c[0] + " corr " + c[1] + ": got " + h[0] + "-" + h[1] + "-" + h[2];
    }
    return null;
}

// Compares computed times (minutes, +-1) with the expected ones; null entries must be undefined.
function checkMinutes(times as Array, expected as Array) as String? {
    for (var i = 0; i < 7; i++) {
        var got = PrayerTimes.toMinutes(times[i]);
        var exp = expected[i];
        if (exp == null) {
            if (got != null) {
                return "index " + i + " should be undefined, got " + got;
            }
        } else if (got == null) {
            return "index " + i + " undefined, expected " + exp;
        } else {
            var diff = (got as Number) - (exp as Number);
            if (diff < -1 || diff > 1) {
                return "index " + i + " got " + got + " expected " + exp;
            }
        }
    }
    return null;
}

(:test)
function testHijri(logger as Logger) as Boolean {
    // [epoch day, correction, year, month, day]
    var cases = [
        [20755, 0, 1448, 5, 17], [20755, -2, 1448, 5, 15], [20755, 2, 1448, 5, 19],
        // year boundary 1447 -> 1448
        [20620, 0, 1447, 12, 30], [20621, 0, 1448, 1, 1], [20620, 2, 1448, 1, 2], [20621, -2, 1447, 12, 29],
        [19782, 0, 1445, 8, 19], [10957, 0, 1420, 9, 24]
    ];
    for (var i = 0; i < cases.size(); i++) {
        var err = checkHijri(cases[i] as Array<Number>);
        Test.assertMessage(err == null, err == null ? "" : err as String);
    }
    return true;
}

(:test)
function testPrayerTimesDjerba(logger as Logger) as Boolean {
    // Djerba 2026-10-29, Tunisia method, Asr standard, UTC+1
    var t = PrayerTimes.computeDay(20755, 33.8754d, 10.8575d, 1.0d, 0, 1, PrayerTimes.HL_MIDDLE);
    var err = checkMinutes(t, [309, 393, 720, 904, 1047, 1047, 1131]);
    Test.assertMessage(err == null, err == null ? "" : err as String);
    return true;
}

(:test)
function testPrayerTimesOtherLocations(logger as Logger) as Boolean {
    var err;
    // Makkah 2026-03-01, Umm al-Qura (Isha = Maghrib + 90 min)
    err = checkMinutes(PrayerTimes.computeDay(20513, 21.4225d, 39.8262d, 3.0d, 4, 1, PrayerTimes.HL_MIDDLE),
                       [325, 401, 753, 954, 1105, 1105, 1195]);
    Test.assertMessage(err == null, err == null ? "" : err as String);
    // Karachi 2026-01-10, Karachi method, Hanafi Asr
    err = checkMinutes(PrayerTimes.computeDay(20463, 24.8607d, 67.0011d, 5.0d, 5, 2, PrayerTimes.HL_MIDDLE),
                       [358, 438, 759, 985, 1081, 1081, 1161]);
    Test.assertMessage(err == null, err == null ? "" : err as String);
    return true;
}

(:test)
function testHighLatitude(logger as Logger) as Boolean {
    var err;
    // Oslo 2026-06-21, MWL: Fajr/Isha undefined without a rule, middle-of-night with it
    err = checkMinutes(PrayerTimes.computeDay(20625, 59.9139d, 10.7522d, 2.0d, 1, 1, PrayerTimes.HL_NONE),
                       [null, 234, 799, 1080, 1364, 1364, null]);
    Test.assertMessage(err == null, err == null ? "" : err as String);
    err = checkMinutes(PrayerTimes.computeDay(20625, 59.9139d, 10.7522d, 2.0d, 1, 1, PrayerTimes.HL_MIDDLE),
                       [79, 234, 799, 1080, 1364, 1364, 1519]);
    Test.assertMessage(err == null, err == null ? "" : err as String);
    return true;
}

(:test)
function testNextPrayerRollover(logger as Logger) as Boolean {
    var s = new PrayerSchedule();
    s.configure(33.8754d, 10.8575d, 0, 1, PrayerTimes.HL_MIDDLE);
    var offset = 3600;
    // 2026-10-29 18:51 local is Isha (1131 min). One second before -> Isha.
    var isha = 20755 * 86400 + 1131 * 60 - offset;
    s.update(isha - 1, offset);
    var n = s.next(isha - 1) as Array;
    Test.assertEqual(n[0], PrayerTimes.ISHA);
    // At Isha -> next day's Fajr
    n = s.next(isha) as Array;
    Test.assertEqual(n[0], PrayerTimes.FAJR);
    Test.assertMessage((n[1] as Long) > isha + 9 * 3600, "Fajr should be on the following day");
    // Just after local midnight the cache moves to the new day and still finds that Fajr
    var midnight = 20756 * 86400 - offset;
    s.update(midnight, offset);
    var n2 = s.next(midnight) as Array;
    Test.assertEqual(n2[0], PrayerTimes.FAJR);
    Test.assertEqual(n2[1], n[1]);
    return true;
}

(:test)
function testAyahRotation(logger as Logger) as Boolean {
    var all = [true, true, true, true];
    // hourly rotation over every verse
    Test.assertEqual(AyahPicker.pick(0, 2, all, 0), 0);
    Test.assertEqual(AyahPicker.pick(0, 2, all, 5), 1);
    // only verses 1 and 3 ticked: hours alternate between them
    var some = [false, true, false, true];
    Test.assertEqual(AyahPicker.pick(0, 0, some, 10), 1);
    Test.assertEqual(AyahPicker.pick(0, 0, some, 11), 3);
    // nothing ticked: the fixed verse
    Test.assertEqual(AyahPicker.pick(0, 2, [false, false, false, false], 7), 2);
    // fixed and hidden modes
    Test.assertEqual(AyahPicker.pick(1, 2, all, 7), 2);
    Test.assertEqual(AyahPicker.pick(2, 2, all, 7), -1);
    return true;
}

(:test)
function testPrayerAdjustment(logger as Logger) as Boolean {
    var offset = 3600;
    var now = 20756 * 86400 - offset + 6 * 3600;      // local morning, Djerba
    var s = new PrayerSchedule();
    s.configure(33.8754d, 10.8575d, 0, 1, PrayerTimes.HL_MIDDLE);
    s.update(now, offset);
    var fajr = s.minutes(0, PrayerTimes.FAJR) as Number;
    var isha = s.minutes(0, PrayerTimes.ISHA) as Number;
    var rise = s.minutes(0, PrayerTimes.SUNRISE) as Number;
    s.setAdjust([3, 0, 0, 0, -5]);
    s.update(now, offset);
    Test.assertEqual(s.minutes(0, PrayerTimes.FAJR), fajr + 3);
    Test.assertEqual(s.minutes(0, PrayerTimes.ISHA), isha - 5);
    Test.assertEqual(s.minutes(0, PrayerTimes.SUNRISE), rise);   // sunrise is not a prayer: unchanged
    return true;
}

(:test)
function testJumuah(logger as Logger) as Boolean {
    var offset = 3600;
    var now = 20756 * 86400 - offset + 6 * 3600;      // Friday 2026-10-30, local morning, Djerba
    var s = new PrayerSchedule();
    s.configure(33.8754d, 10.8575d, 0, 1, PrayerTimes.HL_MIDDLE);
    s.update(now, offset);
    var asr = s.minutes(0, PrayerTimes.ASR);
    Test.assert(!s.isJumuah(0));                       // feature off: the computed Dhuhr
    s.setJumuah(750);
    s.update(now, offset);
    Test.assert(s.isJumuah(0));
    Test.assert(!s.isJumuah(1));                       // Saturday
    Test.assertEqual(s.minutes(0, PrayerTimes.DHUHR), 750);
    Test.assertEqual(s.minutes(0, PrayerTimes.ASR), asr);
    var nxt = s.next(now) as Array;                    // next prayer after 06:00: Jumu'ah at 12:30
    Test.assertEqual(nxt[0], PrayerTimes.DHUHR);
    Test.assertEqual(nxt[1], (20756 * 86400 - offset + 750 * 60).toLong());
    return true;
}
