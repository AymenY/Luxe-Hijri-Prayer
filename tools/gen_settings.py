#!/usr/bin/env python3
"""Single source of truth for the user settings.

Writes resources/properties/properties.xml, resources/settings/settings.xml and the settings
strings in English and French (resources/strings/settings_strings.xml and
resources-fre/strings/settings_strings.xml). Run it after changing a setting here.
"""
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COLOURS = [("Preset", "Selon le style"), ("Red", "Rouge"), ("Orange", "Orange"), ("Gold", "Or"),
           ("Green", "Vert"), ("Cyan", "Cyan"), ("Blue", "Bleu"), ("White", "Blanc")]
SOURCES = [("Steps", "Pas"), ("Heart rate", "Fréquence cardiaque"), ("Calories", "Calories"),
           ("Battery percentage", "Batterie (%)"), ("Distance", "Distance"), ("Floors climbed", "Étages montés"),
           ("Body Battery", "Body Battery"), ("Stress", "Stress"), ("Active minutes (week)", "Minutes intensives (semaine)"),
           ("None (empty gauge)", "Aucune (jauge vide)"), ("Daylight / darkness (24 h)", "Lumière / obscurité (24 h)"),
           ("Moon phase", "Phase de la lune")]
METHODS = [("Tunisia (18° / 18°)", "Tunisie (18° / 18°)"), ("Muslim World League (18° / 17°)", "Ligue islamique mondiale (18° / 17°)"),
           ("ISNA North America (15° / 15°)", "ISNA Amérique du Nord (15° / 15°)"), ("Egypt (19.5° / 17.5°)", "Égypte (19,5° / 17,5°)"),
           ("Umm al-Qura, Makkah (18.5° / 90 min)", "Umm al-Qura, La Mecque (18,5° / 90 min)"),
           ("Karachi (18° / 18°)", "Karachi (18° / 18°)"), ("Gulf region (19.5° / 90 min)", "Région du Golfe (19,5° / 90 min)"),
           ("Kuwait (18° / 17.5°)", "Koweït (18° / 17,5°)"), ("Qatar (18° / 90 min)", "Qatar (18° / 90 min)"),
           ("Singapore MUIS (20° / 18°)", "Singapour MUIS (20° / 18°)"), ("Turkey Diyanet (18° / 17°)", "Turquie Diyanet (18° / 17°)"),
           ("France UOIF (12° / 12°)", "France UOIF (12° / 12°)"), ("Algeria (18° / 17°)", "Algérie (18° / 17°)"),
           ("Morocco (19° / 17°)", "Maroc (19° / 17°)")]


def ayat():
    return json.load(open(os.path.join(ROOT, "tools", "ayat.json")))["ayat"]


def settings():
    """(key, type, default, (title en, title fr), options [(en, fr)] or numeric (min, max))."""
    A = "Appearance: "
    AF = "Apparence : "
    D, DF = "Data fields: ", "Données : "
    F, FF = "Faith & calendar: ", "Foi et calendrier : "
    verses = [(a["ref"], a["name_fr"]) for a in ayat()]
    default_fixed = [a["ref"] for a in ayat()].index("Ash-Sharh 94:5")
    out = [
        ("StylePreset", "number", 0, (A + "Style", AF + "style"),
         [("Luxury Blue", "Luxury Blue (bleu)"), ("Royal Gold", "Royal Gold (or)"), ("Emerald Night", "Emerald Night (émeraude)"),
          ("Burgundy Royale", "Burgundy Royale (bordeaux)"), ("Ice Silver", "Ice Silver (argent)"), ("Stealth", "Stealth (graphite)")]),
        ("Background", "number", 0, (A + "Background", AF + "arrière-plan"),
         [("Mosque at night (illustration)", "Mosquée de nuit (illustration)"), ("Islamic geometric pattern", "Motif géométrique islamique"),
          ("Black marble, gold veining", "Marbre noir veiné d'or"), ("Night sky and crescent", "Ciel nocturne et croissant")]),
        ("DialDigits", "number", 0, (A + "Dial numerals", AF + "chiffres du cadran"),
         [("Arabic numerals (12 3 6 9)", "Chiffres arabes (12 3 6 9)"), ("Indian numerals (Eastern Arabic)", "Chiffres indiens (arabe oriental)")]),
        ("FontFamily", "number", 0, (A + "Font", AF + "police"),
         [("Modern", "Moderne"), ("Classic (serif)", "Classique (empattements)"), ("Sport", "Sport")]),
        ("TextColor", "number", 0, (A + "Text colour", AF + "couleur du texte"),
         [("Preset", "Selon le style"), ("White", "Blanc"), ("Cream", "Crème"), ("Gold", "Or"), ("Silver", "Argent"), ("Ice blue", "Bleu glacier")]),
        ("AccentColor", "number", 0, (A + "Accent colour (countdown, gauges)", AF + "couleur d'accent (compte à rebours, jauges)"), COLOURS),
        ("HandStyle", "number", 0, (A + "Hands", AF + "aiguilles"),
         [("Baton with lume", "Bâton luminescent"), ("Dauphine", "Dauphine"), ("Sword", "Glaive")]),
        ("HandColor", "number", 0, (A + "Hands colour", AF + "couleur des aiguilles"),
         [("Preset", "Selon le style"), ("Gold", "Or"), ("Rose gold", "Or rose"), ("Silver", "Argent"), ("Bronze", "Bronze")]),
        ("SecondsMode", "number", 0, (A + "Seconds hand", AF + "trotteuse"),
         [("Always (also in low power on MIP)", "Toujours (aussi en basse consommation sur MIP)"),
          ("Only after wrist raise", "Seulement après levée du poignet"), ("Hidden", "Masquée")]),
        ("SecondsColor", "number", 0, (A + "Seconds hand colour", AF + "couleur de la trotteuse"), COLOURS),
        ("Gauge1", "number", 0, (D + "gauge 1 (upper left)", DF + "jauge 1 (haut gauche)"), SOURCES),
        ("Gauge2", "number", 1, (D + "gauge 2 (upper right)", DF + "jauge 2 (haut droite)"), SOURCES),
        ("Gauge3", "number", 11, (D + "gauge 3 (left)", DF + "jauge 3 (gauche)"), SOURCES),
        ("Gauge4", "number", 10, (D + "gauge 4 (right)", DF + "jauge 4 (droite)"), SOURCES),
        ("GaugeColors", "number", 0, (D + "gauge colours", DF + "couleurs des jauges"),
         [("One colour per data type", "Une couleur par type de donnée"), ("Accent colour", "Couleur d'accent"), ("Text colour", "Couleur du texte")]),
        ("HijriScript", "number", 0, (F + "Hijri date script", FF + "écriture de la date hégirienne"),
         [("Arabic", "Arabe"), ("Latin", "Latine")]),
        ("HijriDigits", "number", 1, (F + "Hijri date digits (Arabic script)", FF + "chiffres de la date hégirienne (écriture arabe)"),
         [("Arabic numerals (1 2 3)", "Chiffres arabes (1 2 3)"), ("Indian numerals (Eastern Arabic)", "Chiffres indiens (arabe oriental)")]),
        ("HijriCorrection", "number", 2, (F + "Hijri date correction", FF + "correction de la date hégirienne"),
         [("-2 days", "-2 jours"), ("-1 day", "-1 jour"), ("0 days", "0 jour"), ("+1 day", "+1 jour"), ("+2 days", "+2 jours")]),
        ("AyahMode", "number", 0, (F + "Ayah", FF + "verset"),
         [("Hourly rotation (verses ticked below)", "Rotation chaque heure (versets cochés ci-dessous)"),
          ("Fixed verse", "Verset fixe"), ("Hidden", "Masqué")]),
        ("AyahFixed", "number", default_fixed, (F + "Fixed verse", FF + "verset fixe"), verses),
    ]
    for i, (en, fr) in enumerate(verses):
        out.append(("AyahInc%02d" % (i + 1), "boolean", True, ("Rotation: " + en, "Rotation : " + fr), None))
    out += [
        ("CalcMethod", "number", 0, (F + "Prayer calculation method", FF + "méthode de calcul des prières"), METHODS),
        ("AsrMethod", "number", 0, (F + "Asr convention", FF + "calcul de l'Asr"),
         [("Standard (Maliki, Shafi'i, Hanbali)", "Standard (malikite, chaféite, hanbalite)"), ("Hanafi", "Hanafite")]),
        ("HighLatRule", "number", 1, (F + "High-latitude rule", FF + "règle des hautes latitudes"),
         [("None", "Aucune"), ("Middle of the night", "Milieu de la nuit"), ("One-seventh of the night", "Septième de la nuit"),
          ("Angle-based", "Selon l'angle")]),
    ]
    adj = [("%+d min" % m if m else "0 min", "%+d min" % m if m else "0 min") for m in range(-30, 31)]
    for key, (en, fr) in (("AdjFajr", ("Fajr", "Fajr")), ("AdjDhuhr", ("Dhuhr", "Dhohr")), ("AdjAsr", ("Asr", "Asr")),
                          ("AdjMaghrib", ("Maghrib", "Maghrib")), ("AdjIsha", ("Isha", "Icha"))):
        out.append((key, "number", 30, (F + "Adjustment " + en + " (minutes)", FF + "ajustement " + fr + " (minutes)"), adj))
    out += [
        ("LocationMode", "number", 0, (F + "Location for prayer times", FF + "position pour les prières"),
         [("Automatic (watch GPS position)", "Automatique (position GPS de la montre)"),
          ("Manual (latitude / longitude below)", "Manuelle (latitude / longitude ci-dessous)")]),
        ("Latitude", "float", 33.8754, (F + "Latitude (decimal degrees, north positive)", FF + "latitude (degrés décimaux, nord positif)"), (-90, 90)),
        ("Longitude", "float", 10.8575, (F + "Longitude (decimal degrees, east positive)", FF + "longitude (degrés décimaux, est positif)"), (-180, 180)),
        ("TimeZoneMode", "number", 0, (F + "Time zone for prayer times", FF + "fuseau horaire des prières"),
         [("Watch time zone (automatic, follows DST)", "Fuseau de la montre (automatique, heure d'été incluse)"),
          ("Manual UTC offset", "Décalage UTC manuel")]),
        ("UtcOffset", "float", 1.0, (F + "Manual UTC offset (hours, e.g. 1 or 5.5)", FF + "décalage UTC manuel (heures, ex. 1 ou 5,5)"), (-12, 14)),
    ]
    return out


# On-watch settings menu (AppBase.getSettingsView): groups of (property key, short title).
# "#verses" opens the verse check boxes, "#gps" stores the watch's last known position.
MENU = [
    ("Appearance", ("Appearance", "Apparence"), [
        ("StylePreset", ("Style", "Style")), ("Background", ("Background", "Arrière-plan")),
        ("DialDigits", ("Dial numerals", "Chiffres du cadran")), ("FontFamily", ("Font", "Police")),
        ("TextColor", ("Text colour", "Couleur du texte")), ("AccentColor", ("Accent colour", "Couleur d'accent")),
        ("HandStyle", ("Hands", "Aiguilles")), ("HandColor", ("Hands colour", "Couleur des aiguilles")),
        ("SecondsMode", ("Seconds hand", "Trotteuse")), ("SecondsColor", ("Seconds colour", "Couleur trotteuse"))]),
    ("Complications", ("Complications", "Complications"), [
        ("Gauge1", ("Upper left", "Haut gauche")), ("Gauge2", ("Upper right", "Haut droite")),
        ("Gauge3", ("Left", "Gauche")), ("Gauge4", ("Right", "Droite")),
        ("GaugeColors", ("Ring colours", "Couleurs des anneaux"))]),
    ("DateVerse", ("Date & verse", "Date et verset"), [
        ("HijriScript", ("Hijri script", "Écriture hégirienne")), ("HijriDigits", ("Hijri digits", "Chiffres hégiriens")),
        ("HijriCorrection", ("Hijri correction", "Correction hégirienne")), ("AyahMode", ("Verse", "Verset")),
        ("AyahFixed", ("Fixed verse", "Verset fixe")), ("#verses", ("Verses in rotation", "Versets en rotation"))]),
    ("Prayers", ("Prayers", "Prières"), [
        ("CalcMethod", ("Method", "Méthode")), ("AsrMethod", ("Asr", "Asr")),
        ("HighLatRule", ("High latitudes", "Hautes latitudes")), ("TimeZoneMode", ("Time zone", "Fuseau horaire")),
        ("AdjFajr", ("Adjust Fajr", "Ajuster Fajr")), ("AdjDhuhr", ("Adjust Dhuhr", "Ajuster Dhohr")),
        ("AdjAsr", ("Adjust Asr", "Ajuster Asr")), ("AdjMaghrib", ("Adjust Maghrib", "Ajuster Maghrib")),
        ("AdjIsha", ("Adjust Isha", "Ajuster Icha"))]),
    ("Location", ("Location", "Position"), [
        ("LocationMode", ("Position", "Position")),
        ("#gps", ("Use current position", "Utiliser la position actuelle"))]),
]
MENU_TEXTS = [("M_Title", ("Luxe Hijri Prayer", "Luxe Hijri Prayer")),
              ("M_GpsNone", ("No position: start a GPS activity first", "Pas de position : lancez d'abord une activité GPS"))]


def menu_source(table):
    """source/MenuTable.mc: the menu structure with resource ids (Monkey C has no dynamic Rez lookup)."""
    opts = {key: o for key, typ, d, t, o in table if isinstance(o, list)}
    out = ["import Toybox.Lang;", "",
           "// Generated by tools/gen_settings.py: on-watch settings menu (see SettingsMenu.mc).",
           "// [group title, [[property key, title, [option titles] or null], ...]]",
           "module MenuTable {", "    function groups() as Array {", "        return ["]
    for gi, (gid, _t, items) in enumerate(MENU):
        out.append("            [Rez.Strings.MG_%s, [" % gid)
        for key, _tt in items:
            sid = "M_" + key.strip("#").capitalize() if key.startswith("#") else "M_" + key
            if key in opts:
                ids = ", ".join("Rez.Strings.S_%s_%d" % (key, i) for i in range(len(opts[key])))
                out.append('                ["%s", Rez.Strings.%s, [%s]],' % (key, sid, ids))
            else:
                out.append('                ["%s", Rez.Strings.%s, null],' % (key, sid))
        out.append("            ]]%s" % ("," if gi < len(MENU) - 1 else ""))
    out += ["        ];", "    }", "", "    // titles of the verses, for the rotation check boxes",
            "    function verses() as Array {",
            "        return [%s];" % ", ".join("Rez.Strings.S_AyahFixed_%d" % i for i in range(len(opts["AyahFixed"]))),
            "    }", "}", ""]
    return "\n".join(out)


def main():
    props, sets, en, fr = [], [], [], []
    for key, typ, default, (ten, tfr), opts in settings():
        val = ("true" if default else "false") if typ == "boolean" else (repr(float(default)) if typ == "float" else str(default))
        props.append('    <property id="%s" type="%s">%s</property>' % (key, typ, val))
        tid = "S_%s" % key
        en.append((tid, ten))
        fr.append((tid, tfr))
        if typ == "boolean":
            sets.append('    <setting propertyKey="@Properties.%s" title="@Strings.%s">\n'
                        '        <settingConfig type="boolean" />\n    </setting>' % (key, tid))
        elif isinstance(opts, list):
            entries = []
            for i, (oen, ofr) in enumerate(opts):
                oid = "S_%s_%d" % (key, i)
                en.append((oid, oen))
                fr.append((oid, ofr))
                entries.append('            <listEntry value="%d">@Strings.%s</listEntry>' % (i, oid))
            sets.append('    <setting propertyKey="@Properties.%s" title="@Strings.%s">\n        <settingConfig type="list">\n%s\n'
                        '        </settingConfig>\n    </setting>' % (key, tid, "\n".join(entries)))
        else:
            sets.append('    <setting propertyKey="@Properties.%s" title="@Strings.%s">\n'
                        '        <settingConfig type="numeric" min="%s" max="%s" />\n    </setting>' % (key, tid, opts[0], opts[1]))
    for gid, (gen, gfr), items in MENU:
        en.append(("MG_" + gid, gen))
        fr.append(("MG_" + gid, gfr))
        for key, (ten, tfr) in items:
            sid = "M_" + key.strip("#").capitalize() if key.startswith("#") else "M_" + key
            en.append((sid, ten))
            fr.append((sid, tfr))
    for sid, (ten, tfr) in MENU_TEXTS:
        en.append((sid, ten))
        fr.append((sid, tfr))
    w = lambda path, text: open(os.path.join(ROOT, path), "w").write(text)
    w("source/MenuTable.mc", menu_source(settings()))
    w("resources/properties/properties.xml",
      "<properties>\n    <!-- Generated by tools/gen_settings.py -->\n" + "\n".join(props) + "\n</properties>\n")
    w("resources/settings/settings.xml", "<settings>\n    <!-- Generated by tools/gen_settings.py -->\n" + "\n".join(sets) + "\n</settings>\n")
    for path, table in (("resources/strings/settings_strings.xml", en), ("resources-fre/strings/settings_strings.xml", fr)):
        w(path, "<strings>\n    <!-- Generated by tools/gen_settings.py -->\n" + "\n".join(
            '    <string id="%s">%s</string>' % (k, escape(v, {"'": "&apos;"})) for k, v in table) + "\n</strings>\n")
    print("%d settings" % len(props))


if __name__ == "__main__":
    main()
