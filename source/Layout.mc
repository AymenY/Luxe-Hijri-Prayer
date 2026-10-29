import Toybox.Lang;

// Geometry of the 280 x 280 round dial. Every value is in device pixels.
// tools/face.py parses this file so the reference previews use exactly the same layout.
module Layout {
    const W = 280;
    const CX = 140;
    const CY = 140;
    const SAFE_R = 128;          // all text and gauges must stay inside this radius

    // Chapter ring and indices
    const TRACK_R_OUT = 137;     // minute track outer radius
    const TRACK_R_IN = 133;      // minute track inner radius
    const IDX_R_OUT = 134;       // hour index outer radius
    const IDX_R_IN = 123;        // short (non-cardinal) hour index inner radius
    const IDX_CARD_R_IN = 116;   // 3/9 o'clock index inner radius
    const IDX_W = 3;             // half width of an hour index at the outer end
    const IDX_12_GAP = 5;        // half distance between the two 12 o'clock batons
    const STAR6_R = 7;           // 8-point star marker at 6 o'clock
    const STAR6_Y = 264;

    // Ayah (pre-shaped glyph from the Ayah font), centred on AYAH_Y
    const AYAH_Y = 49;
    const AYAH_MAX_W = 160;
    const AYAH_MAX_H = 44;

    // Dates (text vertical centres)
    const GREG_Y = 80;
    const HIJRI_Y = 95;

    // Gauges (centres and ring)
    const GAUGE_DX = 68;         // horizontal distance from CX
    const GAUGE_TOP_Y = 133;
    const GAUGE_BOT_Y = 186;
    const GAUGE_R = 24;          // ring radius (pen centre)
    const GAUGE_PEN = 4;
    const GAUGE_VALUE_DY = -3;   // value text centre relative to gauge centre
    const GAUGE_DISC_R = 27;     // dark disc behind each gauge
    const GAUGE_ICON_DY = 19;    // icon / unit centre (in the open bottom of the ring)

    // Prayer panel
    const SCHED_Y = 220;
    const SCHED_W = 166;         // total width used by the five schedule cells
    const NEXT_Y = 237;

    // Sunrise / sunset, in the band below the pivot between the four gauges
    const SUN_Y = 160;
    const SUN_GAP = 4;           // gap between the sunrise and sunset groups
    const SUN_ICON_W = 11;

    // Hands (lengths from the centre; tails point the other way)
    const HOUR_LEN = 66;
    const HOUR_W = 7;
    const HOUR_TAIL = 12;
    const MIN_LEN = 104;
    const MIN_W = 6;
    const MIN_TAIL = 14;
    const SEC_LEN = 122;
    const SEC_TAIL = 26;
    const SEC_PEN = 2;
    const SEC_WEIGHT_R = 4;      // counterweight radius on the tail
    const CAP_R = 6;
    const CAP_INNER_R = 2;
}
