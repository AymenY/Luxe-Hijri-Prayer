import Toybox.Lang;

// Geometry of the 280 x 280 round dial. Every value is in device pixels.
// tools/face.py parses this file so the reference previews use exactly the same layout.
module Layout {
    const W = 280;
    const CX = 140;
    const CY = 140;
    const SAFE_R = 128;          // all text and gauges must stay inside this radius

    // Chapter ring
    const TICK_R_IN = 131;       // minute ticks
    const TICK_R_OUT = 137;
    const IDX_R_IN = 121;        // gold hour indices (not at 12/3/6/9)
    const IDX_R_OUT = 135;
    const IDX_W_IN = 2;          // half widths of an index at its inner / outer end
    const IDX_W_OUT = 4;
    const NUM_R = 118;           // centre radius of the 12 / 3 / 6 / 9 numerals

    // Date block (between the two upper gauges) and Hijri line
    const CRESCENT_Y = 45;
    const DAY_NAME_Y = 57;
    const DAY_NUM_Y = 75;
    const MONTH_Y = 93;
    const HIJRI_Y = 113;

    // Gauges: upper pair (steps / heart rate) and side pair (calories / battery)
    const GAUGE_UP_DX = 56;
    const GAUGE_UP_Y = 72;
    const GAUGE_SIDE_DX = 76;
    const GAUGE_SIDE_Y = 148;
    const GAUGE_R = 27;          // ring radius (pen centre)
    const GAUGE_PEN = 4;
    const GAUGE_DISC_R = 29;     // dark disc behind each gauge
    const GAUGE_ICON_DY = -16;   // icon centre relative to the gauge centre
    const GAUGE_VALUE_DY = -2;
    const GAUGE_LABEL_DY = 11;
    const GAUGE_BATT_ICON_DY = -17;  // battery: larger value, so icon and label move outwards
    const GAUGE_BATT_LABEL_DY = 14;

    // Sunrise (left) and sunset (right): icon above the time
    const SUN_DX = 93;
    const SUN_ICON_Y = 97;
    const SUN_TIME_Y = 109;

    // Moorish window (night scene behind the date block and the hands): straight sides between
    // the side gauges, shoulders under the upper gauges, neck between them, lobed pointed top
    const WINDOW_X0 = 97;
    const WINDOW_X1 = 183;
    const WINDOW_SHOULDER_Y = 116;
    const WINDOW_NECK_X0 = 114;
    const WINDOW_NECK_X1 = 166;
    const WINDOW_NECK_Y = 98;
    const WINDOW_TOP = 34;
    const WINDOW_BOTTOM = 214;

    // Prayer cartouches: next prayer + countdown (left), following prayer + time (right)
    const PANEL_DX = 49;         // panel centre distance from CX
    const PANEL_W = 66;
    const PANEL_Y0 = 178;
    const PANEL_H = 28;

    // Ayah: no cartouche; the verse and its Arabic reference sit on the dial, inside a circle
    // clear of the hour indices and above the 6 numeral
    const AYAH_Y = 219;
    const AYAH_MAX_W = 136;
    const AYAH_MAX_H = 26;
    const AYAH_REF_Y = 241;
    const AYAH_AREA_R = 117;
    const AYAH_AREA_BOTTOM = 248;

    // Hands (lengths from the centre; tails point the other way)
    const HOUR_LEN = 54;
    const HOUR_W = 4;
    const HOUR_TAIL = 10;
    const MIN_LEN = 96;
    const MIN_W = 3;
    const MIN_TAIL = 12;
    const SEC_LEN = 120;
    const SEC_TAIL = 24;
    const SEC_PEN = 2;
    const SEC_WEIGHT_R = 4;      // hollow counterweight on the tail
    const CAP_R = 7;
    const CAP_INNER_R = 4;
    const HUB_DIAMOND_Y = 152;   // small gold diamond under the pivot
}
