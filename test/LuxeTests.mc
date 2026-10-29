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

(:test)
function assertHijri(epochDay as Number, corr as Number, y as Number, m as Number, d as Number) as Void {
    var h = HijriCalendar.forEpochDay(epochDay, corr);
    Test.assertEqualMessage(h[0], y, "year " + epochDay);
    Test.assertEqualMessage(h[1], m, "month " + epochDay);
    Test.assertEqualMessage(h[2], d, "day " + epochDay);
}

(:test)
function testHijri(logger as Logger) as Boolean {
    assertHijri(20755, 0, 1448, 5, 17);
    assertHijri(20755, -2, 1448, 5, 15);
    assertHijri(20755, 2, 1448, 5, 19);
    // year boundary 1447 -> 1448
    assertHijri(20620, 0, 1447, 12, 30);
    assertHijri(20621, 0, 1448, 1, 1);
    assertHijri(20620, 2, 1448, 1, 2);
    assertHijri(20621, -2, 1447, 12, 29);
    assertHijri(19782, 0, 1445, 8, 19);
    assertHijri(10957, 0, 1420, 9, 24);
    return true;
}

(:test)
function assertMinutes(times as Array, expected as Array) as Void {
    for (var i = 0; i < 7; i++) {
        var got = PrayerTimes.toMinutes(times[i]);
        var exp = expected[i];
        if (exp == null) {
            Test.assertMessage(got == null, "index " + i + " should be undefined");
        } else {
            Test.assertMessage(got != null, "index " + i + " undefined");
            var diff = (got as Number) - (exp as Number);
            Test.assertMessage(diff >= -1 && diff <= 1, "index " + i + " got " + got + " expected " + exp);
        }
    }
}

(:test)
function testPrayerTimesDjerba(logger as Logger) as Boolean {
    // Djerba 2026-10-29, Tunisia method, Asr standard, UTC+1
    var t = PrayerTimes.computeDay(20755, 33.8754d, 10.8575d, 1.0d, 0, 1, PrayerTimes.HL_MIDDLE);
    assertMinutes(t, [309, 393, 720, 904, 1047, 1047, 1131]);
    return true;
}

(:test)
function testPrayerTimesOtherLocations(logger as Logger) as Boolean {
    // Makkah 2026-03-01, Umm al-Qura (Isha = Maghrib + 90 min)
    assertMinutes(PrayerTimes.computeDay(20513, 21.4225d, 39.8262d, 3.0d, 4, 1, PrayerTimes.HL_MIDDLE),
                  [325, 401, 753, 954, 1105, 1105, 1195]);
    // Karachi 2026-01-10, Karachi method, Hanafi Asr
    assertMinutes(PrayerTimes.computeDay(20463, 24.8607d, 67.0011d, 5.0d, 5, 2, PrayerTimes.HL_MIDDLE),
                  [358, 438, 759, 985, 1081, 1081, 1161]);
    return true;
}

(:test)
function testHighLatitude(logger as Logger) as Boolean {
    // Oslo 2026-06-21, MWL: Fajr/Isha undefined without a rule, middle-of-night with it
    assertMinutes(PrayerTimes.computeDay(20625, 59.9139d, 10.7522d, 2.0d, 1, 1, PrayerTimes.HL_NONE),
                  [null, 234, 799, 1080, 1364, 1364, null]);
    assertMinutes(PrayerTimes.computeDay(20625, 59.9139d, 10.7522d, 2.0d, 1, 1, PrayerTimes.HL_MIDDLE),
                  [79, 234, 799, 1080, 1364, 1364, 1519]);
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
