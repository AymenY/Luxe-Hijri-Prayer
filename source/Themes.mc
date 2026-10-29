import Toybox.Lang;

// Style presets. The fenix 7X Pro has a 64-colour MIP display, so every colour uses only
// the channel levels 0x00, 0x55, 0xAA and 0xFF (anything else would be dithered).
// tools/face.py parses this file for the reference previews.
module Themes {
    // Colour roles (index into a preset)
    const BG = 0;        // dial background
    const PLATE = 1;     // gauge discs / panels
    const ORN = 2;       // background ornament (subtle)
    const ORN2 = 3;      // secondary ornament
    const GOLD = 4;      // indices, hands, frames
    const GOLD_DK = 5;   // hand facets, minute track, frame shadow
    const ACCENT = 6;    // gauge progress, day name, next-prayer countdown
    const ACCENT2 = 7;   // Hijri date, highlighted schedule entry, labels
    const TEXT = 8;      // main information text
    const DIM = 9;       // secondary text (labels, past prayers)
    const TRACK = 10;    // gauge track
    const SECONDS = 11;  // seconds hand
    const SIL = 12;      // mosque silhouette
    const STAR = 13;     // stars, crescent highlights
    const WARN = 14;     // low battery

    const COUNT = 6;

    // Order must match the "StylePreset" list in resources/settings/settings.xml.
    const PRESETS = [
        // A  Luxury Blue
        [0x000055, 0x000000, 0x0000AA, 0x0055AA, 0xFFAA00, 0xAA5500, 0x00AAFF, 0x00FFFF,
         0xFFFFFF, 0xAAAAAA, 0x0000AA, 0x00FFFF, 0x000000, 0xFFFFAA, 0xFF5500],
        // B  Royal Gold
        [0x000000, 0x000000, 0x555500, 0xAA5500, 0xFFAA00, 0xAA5500, 0xFFAA00, 0xFFFFAA,
         0xFFFFAA, 0xAAAA55, 0x555500, 0xFFFF55, 0x555500, 0xFFFFAA, 0xFF5500],
        // C  Emerald Night
        [0x000000, 0x000000, 0x005500, 0x005555, 0xFFAA00, 0xAA5500, 0x00AA55, 0x55FFAA,
         0xFFFFFF, 0xAAAAAA, 0x005500, 0x55FF55, 0x005500, 0xFFFFAA, 0xFF5500],
        // D  Burgundy Royale
        [0x550000, 0x000000, 0x000000, 0xAA0055, 0xFFAA55, 0xAA5555, 0xFF0055, 0xFFAAAA,
         0xFFFFAA, 0xAAAAAA, 0x550000, 0xFFAAAA, 0x000000, 0xFFAAAA, 0xFF5500],
        // E  Ice Silver
        [0x000055, 0x000000, 0x0055AA, 0x00AAAA, 0xFFFFFF, 0xAAAAAA, 0x55AAFF, 0xAAFFFF,
         0xFFFFFF, 0xAAAAAA, 0x0055AA, 0xAAFFFF, 0x000000, 0xFFFFFF, 0xFF5500],
        // F  Stealth
        [0x000000, 0x000000, 0x555555, 0x555555, 0xAAAAAA, 0x555555, 0xFFFFFF, 0xFFFFFF,
         0xFFFFFF, 0xAAAAAA, 0x555555, 0xFFFFFF, 0x555555, 0xAAAAAA, 0xFF5500]
    ];
}
