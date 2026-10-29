import Toybox.Application;
import Toybox.Lang;
import Toybox.Math;

// User settings, read from Application.Properties (defined in
// resources/properties/properties.xml, edited through resources/settings/settings.xml in
// the Connect IQ / Garmin Connect app). Every value is validated; an invalid value falls
// back to its default so the watch face always renders.
class LuxeSettings {

    var preset as Number = 0;
    var background as Number = 0;
    var secondsAlways as Boolean = true;
    var gauges as Array<Number> = [0, 1, 2, 3];
    var hijriCorrection as Number = 0;
    var ayah as Number = 0;              // 0..6, AYAH_NONE = hidden
    var method as Number = 0;
    var asrFactor as Number = 1;         // 1 = standard, 2 = Hanafi
    var highLat as Number = 1;
    var latitude as Double = 33.8754d;
    var longitude as Double = 10.8575d;
    var locationSet as Boolean = true;
    var tzManual as Boolean = false;
    var utcOffsetSeconds as Number = 3600;

    const AYAH_NONE = 7;

    function initialize() {
    }

    function load() as Void {
        preset = readList("StylePreset", Themes.COUNT - 1, 0);
        background = readList("Background", 3, 0);
        secondsAlways = readList("SecondsMode", 1, 0) == 0;
        gauges = [readList("Gauge1", 7, 0), readList("Gauge2", 7, 1),
                  readList("Gauge3", 7, 2), readList("Gauge4", 7, 3)];
        hijriCorrection = readList("HijriCorrection", 4, 2) - 2;
        ayah = readList("AyahSelection", AYAH_NONE, 0);
        method = readList("CalcMethod", PrayerTimes.METHODS.size() - 1, 0);
        asrFactor = readList("AsrMethod", 1, 0) + 1;
        highLat = readList("HighLatRule", 3, 1);

        latitude = readDegrees("Latitude", 90.0d, 33.8754d);
        longitude = readDegrees("Longitude", 180.0d, 10.8575d);
        // 0/0 (the Gulf of Guinea) is what an empty numeric field turns into: treat it as
        // "not configured" and ask the user to set a location instead of showing wrong times.
        locationSet = !(latitude == 0.0d && longitude == 0.0d);

        tzManual = readList("TimeZoneMode", 1, 0) == 1;
        var off = readDegrees("UtcOffset", 14.0d, 1.0d);
        if (off < -12.0d) {
            off = -12.0d;
        }
        // whole minutes (offsets such as +5:30 and +5:45 exist)
        utcOffsetSeconds = Math.round(off * 60.0d).toNumber() * 60;
    }

    // Raw property value as a Double, or null.
    hidden function readNumeric(key as String) as Double? {
        var v = null;
        try {
            v = Application.Properties.getValue(key);
        } catch (e) {
            v = null;
        }
        if (v instanceof Number || v instanceof Float || v instanceof Double || v instanceof Long) {
            return v.toDouble();
        }
        if (v instanceof String) {
            var f = v.toFloat();
            if (f != null) {
                return f.toDouble();
            }
        }
        return null;
    }

    // List index in 0..max, or the default.
    hidden function readList(key as String, max as Number, def as Number) as Number {
        var v = readNumeric(key);
        if (v == null) {
            return def;
        }
        var n = v.toNumber();
        if (n < 0 || n > max) {
            return def;
        }
        return n;
    }

    // Value in -limit..limit (NaN and out-of-range values use the default).
    hidden function readDegrees(key as String, limit as Double, def as Double) as Double {
        var v = readNumeric(key);
        if (v == null || v != v || v > limit || v < -limit) {
            return def;
        }
        return v;
    }
}
