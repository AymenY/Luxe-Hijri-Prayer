import Toybox.Lang;

// Style presets. Colours use only the channel levels 0x00, 0x55, 0xAA and 0xFF so that they
// are exact on 64-colour MIP displays (fenix, Forerunner MIP, Enduro); AMOLED displays show
// them unchanged. tools/face.py parses this file for the reference previews.
module Themes {
    // Colour roles (index into a preset)
    const BG = 0;        // dial background / sky
    const PLATE = 1;     // gauge discs, cartouches, bezel band
    const ORN = 2;       // background ornament (subtle)
    const ORN2 = 3;      // secondary ornament
    const GOLD = 4;      // indices, numerals, hands, frames
    const GOLD_DK = 5;   // facets, frame lines, lit windows
    const ACCENT = 6;    // gauge progress (single-colour presets), countdown
    const ACCENT2 = 7;   // Hijri date, labels
    const TEXT = 8;      // main information text, hand lume
    const DIM = 9;       // secondary text
    const TRACK = 10;    // gauge track
    const SECONDS = 11;  // seconds hand
    const SIL = 12;      // silhouettes (mosque, palms)
    const STAR = 13;     // stars, crescent highlights
    const WARN = 14;     // low battery
    const TICK = 15;     // minute track

    const COUNT = 10;

    // Order must match the "StylePreset" list in resources/settings/settings.xml.
    const PRESETS = [
        // A  Luxury Blue
        [0x000055, 0x000000, 0x0000AA, 0x0055AA, 0xFFAA00, 0xAA5500, 0x00AAFF, 0x00FFFF,
         0xFFFFFF, 0xAAAAAA, 0x0000AA, 0x00AAFF, 0x000000, 0xFFFFAA, 0xFF5500, 0xAAFFFF],
        // B  Royal Gold
        [0x000000, 0x000000, 0x555500, 0xAA5500, 0xFFAA00, 0xAA5500, 0xFFAA00, 0xFFFFAA,
         0xFFFFAA, 0xAAAA55, 0x555500, 0xFFFF55, 0x555500, 0xFFFFAA, 0xFF5500, 0xAAAA55],
        // C  Emerald Night
        [0x000000, 0x000000, 0x005500, 0x005555, 0xFFAA00, 0xAA5500, 0x00AA55, 0x55FFAA,
         0xFFFFFF, 0xAAAAAA, 0x005500, 0x55FF55, 0x005500, 0xFFFFAA, 0xFF5500, 0x55AA55],
        // D  Burgundy Royale
        [0x550000, 0x000000, 0x000000, 0xAA0055, 0xFFAA55, 0xAA5555, 0xFF0055, 0xFFAAAA,
         0xFFFFAA, 0xAAAAAA, 0x550000, 0xFFAAAA, 0x000000, 0xFFAAAA, 0xFF5500, 0xAA5555],
        // E  Ice Silver
        [0x000055, 0x000000, 0x0055AA, 0x00AAAA, 0xFFFFFF, 0xAAAAAA, 0x55AAFF, 0xAAFFFF,
         0xFFFFFF, 0xAAAAAA, 0x0055AA, 0xAAFFFF, 0x000000, 0xFFFFFF, 0xFF5500, 0xAAFFFF],
        // F  Stealth
        [0x000000, 0x000000, 0x555555, 0x555555, 0xAAAAAA, 0x555555, 0xFFFFFF, 0xFFFFFF,
         0xFFFFFF, 0xAAAAAA, 0x555555, 0xFFFFFF, 0x555555, 0xAAAAAA, 0xFF5500, 0xAAAAAA],
        // G  Scarlet Noir: black, red and white
        [0x000000, 0x000000, 0x550000, 0xAA0000, 0xFFFFFF, 0xAAAAAA, 0xFF0000, 0xFF5555,
         0xFFFFFF, 0xAAAAAA, 0x550000, 0xFF0000, 0x000000, 0xFFFFFF, 0xFF5500, 0xAAAAAA],
        // H  Ember Gold: high contrast, black, white, red, orange and gold (readable without backlight)
        [0x000000, 0x000000, 0x550000, 0xAA0000, 0xFFAA00, 0xAA5500, 0xFF5500, 0xFFAA00,
         0xFFFFFF, 0xFFAA55, 0x550000, 0xFF0000, 0x000000, 0xFFFFFF, 0xFF0000, 0xFFFFFF],
        // I  Oasis Gold: high contrast, black, white, blue, green and gold (readable without backlight)
        [0x000000, 0x000000, 0x000055, 0x005500, 0xFFAA00, 0xAA5500, 0x00FF55, 0x00AAFF,
         0xFFFFFF, 0x55AAFF, 0x005500, 0x00AAFF, 0x000000, 0xFFFFFF, 0xFF5500, 0xFFFFFF],
        // J  E-Ink: black ink on white paper, red seconds hand (like an electronic-paper screen)
        [0xFFFFFF, 0xFFFFFF, 0xAAAAAA, 0xAAAAAA, 0x000000, 0x555555, 0x000000, 0x000000,
         0x000000, 0x555555, 0xAAAAAA, 0xFF0000, 0x000000, 0x000000, 0xFF0000, 0x000000]
    ];

    // Presets whose gauges use one colour per data type (as in the approved concept)
    // instead of the preset accent.
    const MULTICOLOR = [true, false, false, false, true, false, false, false, false, false];

    // Friday dial (from 00:00 until Asr, setting FridayDesign), whatever the style: Sidi Bou Said
    // blue wrought iron, gold hour ring, white text, jasmine (STAR) and geranium (SIL) on the
    // vector dial, one gauge colour per data type. Hands: FRIDAY_HANDS unless the user chose a colour.
    const FRIDAY = [0x000055, 0x000000, 0x0055AA, 0x00AA00, 0xFFAA00, 0xAA5500, 0x00AAFF, 0x55AAFF,
                    0xFFFFFF, 0xAAAAAA, 0x0055AA, 0x00AAFF, 0xFF0000, 0xFFFFFF, 0xFF5500, 0xFFFFAA];
    const FRIDAY_HANDS = [0xFFFFFF, 0xAAAAAA];
    const FRIDAY_NUMERALS = 1;   // gold numerals of the Royal Gold style

    // Gauge colour per data source (DataFields order), used by MULTICOLOR presets.
    const SOURCE_COLORS = [0x00AAFF, 0xFF0055, 0xFFAA00, 0x00FF55, 0x55FFFF, 0xAAAAFF, 0x00FFAA, 0xFFFF55, 0xFF55FF, 0xAAAAAA];

    // Daylight / darkness ring (full colour; MIP devices map them to their own palette):
    // daylight (sunrise -> sunset), twilight (Fajr -> sunrise, sunset -> Isha), darkness, night text
    const SUN_DAY = 0xFFC83A;
    const SUN_TWILIGHT = 0x8A5BC8;
    const SUN_NIGHT = 0x3355AA;
    const SUN_NIGHT_TEXT = 0x9FB8FF;

    // E-Ink style: daylight ring and Moon dial in greys (day, twilight, night, night text;
    // lit, dark, ring)
    const INK = 9;
    const SUN_INK = [0x555555, 0xAAAAAA, 0x000000, 0x000000];
    const MOON_INK = [0xFFFFFF, 0x000000, 0x000000];

    // Moon dial: lit surface, dark surface (earthshine), lunation ring
    const MOON_LIT = 0xFFF2C0;
    const MOON_DARK = 0x2A3350;
    const MOON_RING = 0xC8D2E6;

    // User colour choices (settings index - 1). Order must match tools/gen_settings.py.
    const COLOUR_CHOICES = [0xFF0000, 0xFF5500, 0xFFAA00, 0x00FF55, 0x00FFFF, 0x00AAFF, 0xFFFFFF];
    const TEXT_CHOICES = [0xFFFFFF, 0xFFFFAA, 0xFFAA00, 0xAAAAAA, 0xAAFFFF];
    // hands: [light, dark]
    const HAND_CHOICES = [[0xFFAA00, 0xAA5500], [0xFFAA55, 0xAA5555], [0xFFFFFF, 0xAAAAAA], [0xAA5500, 0x550000]];
}
