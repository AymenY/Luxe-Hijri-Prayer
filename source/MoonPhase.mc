import Toybox.Lang;
import Toybox.Math;

// Phase of the Moon from the main periodic terms of the phase angle (Meeus, Astronomical
// Algorithms, ch. 48): illuminated fraction within about 1 %, validated against an independent
// library by tools/validate_calculations.py.
module MoonPhase {

    const SYNODIC = 29.530588853;

    // [illuminated fraction 0..1, waxing, age in days since the mean new moon]
    function at(utcSeconds as Number) as Array {
        var jd = utcSeconds.toDouble() / 86400.0d + 2440587.5d;
        var t = (jd - 2451545.0d) / 36525.0d;
        var d = norm(297.8501921d + 445267.1114034d * t);
        var m = norm(357.5291092d + 35999.0502909d * t);
        var mp = norm(134.9633964d + 477198.8675055d * t);
        var r = Math.PI / 180.0d;
        var i = 180.0d - d - 6.289d * Math.sin(mp * r) + 2.100d * Math.sin(m * r)
                - 1.274d * Math.sin((2.0d * d - mp) * r) - 0.658d * Math.sin(2.0d * d * r)
                - 0.214d * Math.sin(2.0d * mp * r) - 0.110d * Math.sin(d * r);
        var k = (1.0d + Math.cos(i * r)) / 2.0d;
        return [k, d < 180.0d, d / 360.0d * SYNODIC];
    }

    function norm(x as Double) as Double {
        var y = x - 360.0d * Math.floor(x / 360.0d);
        return y;
    }
}
