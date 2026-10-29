#!/usr/bin/env python3
"""Static checks that do not need the Connect IQ SDK.

They catch the classes of errors the Monkey C compiler would report for resources and
settings, plus project-specific invariants:
  * XML well-formedness of the manifest and every resource file
  * every Rez.<Type>.<Id> used in source/ exists in resources/ (and resource files exist)
  * every @Strings / @Properties / @Drawables reference resolves
  * every property read in source/ is declared, and every declared property is used
  * French strings define exactly the same ids as English
  * settings list sizes match the code tables (presets, gauges, methods, Ayat, ...)
  * all theme colours belong to the 64-colour MIP palette
  * every character drawn on the dial exists in the bitmap font that draws it
  * background geometry uses valid op codes, arities and colour roles
  * Monkey C syntax (via the open-source @markw65/prettier-plugin-monkeyc parser, if
    Node.js and the plugin are installed: `npm install` in tools/)
This is NOT a substitute for compiling with monkeyc: types and API signatures are not checked.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, notes = [], []


def rel(p):
    return os.path.relpath(p, ROOT)


def parse(path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as e:
        errors.append("%s: XML error %s" % (rel(path), e))
        return None


def src_text():
    return {p: open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(ROOT, "source", "*.mc"))
            + glob.glob(os.path.join(ROOT, "test", "*.mc"))}


def main():
    sources = src_text()
    allsrc = "\n".join(sources.values())

    # ---- resources
    res = {"Strings": {}, "Fonts": {}, "JsonData": {}, "Drawables": {}, "Properties": {}}
    for path in glob.glob(os.path.join(ROOT, "resources", "**", "*.xml"), recursive=True):
        root = parse(path)
        if root is None:
            continue
        for el in root.iter():
            tag = el.tag
            rid = el.get("id")
            if tag == "string":
                res["Strings"][rid] = el.text or ""
            elif tag == "font":
                res["Fonts"][rid] = el.get("filename")
            elif tag == "jsonData":
                res["JsonData"][rid] = el.get("filename")
            elif tag == "bitmap":
                res["Drawables"][rid] = el.get("filename")
            elif tag == "property":
                res["Properties"][rid] = (el.get("type"), (el.text or "").strip())
            if tag in ("font", "jsonData", "bitmap"):
                f = os.path.join(os.path.dirname(path), el.get("filename"))
                if not os.path.exists(f):
                    errors.append("%s: missing file %s" % (rel(path), el.get("filename")))
    fre = {}
    root = parse(os.path.join(ROOT, "resources-fre", "strings", "strings.xml"))
    if root is not None:
        fre = {el.get("id"): el.text or "" for el in root.iter("string")}
    missing_fr = set(res["Strings"]) - set(fre)
    extra_fr = set(fre) - set(res["Strings"])
    if missing_fr:
        errors.append("French strings missing: %s" % sorted(missing_fr))
    if extra_fr:
        errors.append("French strings not in English: %s" % sorted(extra_fr))

    # ---- Rez references in source
    for kind, rid in set(re.findall(r"Rez\.(\w+)\.(\w+)", allsrc)):
        if rid not in res.get(kind, {}):
            errors.append("source uses Rez.%s.%s which is not defined" % (kind, rid))
    unused = [s for s in res["Strings"] if s not in allsrc and "@Strings." + s not in
              open(os.path.join(ROOT, "resources", "settings", "settings.xml")).read() + open(os.path.join(ROOT, "manifest.xml")).read()]
    if unused:
        errors.append("unused strings: %s" % unused)

    # ---- manifest
    man = parse(os.path.join(ROOT, "manifest.xml"))
    ns = {"iq": "http://www.garmin.com/xml/connectiq"}
    if man is not None:
        app = man.find("iq:application", ns)
        if app.get("type") != "watchface":
            errors.append("manifest: application type must be watchface")
        if not re.fullmatch(r"[0-9a-f]{32}", app.get("id", "")):
            errors.append("manifest: application id must be 32 hex digits")
        for attr in ("name", "launcherIcon"):
            m = re.fullmatch(r"@(\w+)\.(\w+)", app.get(attr, ""))
            if not m or m.group(2) not in res[m.group(1)]:
                errors.append("manifest: %s reference %s unresolved" % (attr, app.get(attr)))
        if "class %s " % app.get("entry") not in allsrc:
            errors.append("manifest: entry class %s not found" % app.get("entry"))
        products = [p.get("id") for p in app.iter("{%s}product" % ns["iq"])]
        notes.append("products: %s" % products)
        perms = [p.get("id") for p in app.iter("{%s}uses-permission" % ns["iq"])]
        if "SensorHistory" in allsrc and "SensorHistory" not in perms:
            errors.append("manifest: SensorHistory used but permission not declared")

    # ---- settings
    sroot = parse(os.path.join(ROOT, "resources", "settings", "settings.xml"))
    lists = {}
    for st in sroot.iter("setting"):
        key = st.get("propertyKey", "").replace("@Properties.", "")
        if key not in res["Properties"]:
            errors.append("settings: unknown property %s" % key)
        title = st.get("title", "").replace("@Strings.", "")
        if title not in res["Strings"]:
            errors.append("settings: unknown title string %s" % title)
        cfg = st.find("settingConfig")
        if cfg.get("type") == "list":
            vals = []
            for le in cfg.iter("listEntry"):
                vals.append(int(le.get("value")))
                sid = (le.text or "").replace("@Strings.", "")
                if sid not in res["Strings"]:
                    errors.append("settings: unknown list string %s" % sid)
            lists[key] = vals
            if vals != list(range(len(vals))):
                errors.append("settings: %s values must be 0..n-1" % key)
            default = int(res["Properties"][key][1])
            if default not in vals:
                errors.append("settings: default of %s (%d) is not a list value" % (key, default))
    for key in res["Properties"]:
        if '"%s"' % key not in allsrc:
            errors.append("property %s declared but never read" % key)
        if key not in lists and res["Properties"][key][0] == "number":
            errors.append("property %s has no setting" % key)
    for key in re.findall(r'read\w+\("(\w+)"', allsrc):
        if key not in res["Properties"]:
            errors.append("source reads undeclared property %s" % key)

    # list sizes vs code tables
    themes = open(os.path.join(ROOT, "source", "Themes.mc")).read()
    n_presets = len(re.findall(r"//\s+[A-F]\s+\w", themes))
    expect = {
        "StylePreset": n_presets,
        "Background": len([j for j in res["JsonData"] if j.startswith("Bg")]),
        "Gauge1": 8, "Gauge2": 8, "Gauge3": 8, "Gauge4": 8,
        "HijriCorrection": 5,
        "AyahSelection": 8,
        "CalcMethod": len(re.findall(r"^\s+\[\d+\.\dd, \d+\.\dd, \d+\]", open(os.path.join(ROOT, "source", "PrayerTimes.mc")).read(), re.M)),
        "AsrMethod": 2, "HighLatRule": 4, "TimeZoneMode": 2, "SecondsMode": 2,
    }
    for k, n in expect.items():
        if len(lists.get(k, [])) != n:
            errors.append("settings: %s has %d entries, code expects %d" % (k, len(lists.get(k, [])), n))
    if "const COUNT = %d;" % n_presets not in themes:
        errors.append("Themes.COUNT does not match the number of presets")

    # ---- palette
    levels = {0x00, 0x55, 0xAA, 0xFF}
    body = themes[themes.index("const PRESETS"):themes.index("const MULTICOLOR")]
    if len(re.findall(r"true|false", themes[themes.index("const MULTICOLOR"):themes.index("const SOURCE_COLORS")])) != n_presets:
        errors.append("Themes.MULTICOLOR must have one entry per preset")
    src_cols = re.findall(r"0x[0-9A-Fa-f]{6}", themes[themes.index("const SOURCE_COLORS"):])
    if len(src_cols) != 8:
        errors.append("Themes.SOURCE_COLORS must have one colour per gauge source")
    for c in src_cols:
        c = int(c, 16)
        if any(((c >> sh) & 255) not in {0x00, 0x55, 0xAA, 0xFF} for sh in (16, 8, 0)):
            errors.append("source colour %06X is not in the 64-colour MIP palette" % c)
    rows = re.findall(r"\[([^\[\]]+)\]", body)
    for i, r in enumerate(rows):
        cols = [int(x, 16) for x in re.findall(r"0x[0-9A-Fa-f]{6}", r)]
        if len(cols) != 16:
            errors.append("preset %d has %d colours (expected 16)" % (i, len(cols)))
        for c in cols:
            if any(((c >> s) & 255) not in levels for s in (16, 8, 0)):
                errors.append("preset %d colour %06X is not in the 64-colour MIP palette" % (i, c))

    # ---- font sets: one per screen size, same ids everywhere, full glyph coverage
    font_dirs = [os.path.join(ROOT, "resources", "fonts")] + sorted(
        glob.glob(os.path.join(ROOT, "resources-round-*", "fonts")))
    base_ids = None
    for fd in font_dirs:
        root = parse(os.path.join(fd, "fonts.xml"))
        if root is None:
            continue
        ids = {el.get("id"): el.get("filename") for el in root.iter("font")}
        if base_ids is None:
            base_ids = ids
        elif ids != base_ids:
            errors.append("%s: font ids differ from the base set" % rel(fd))
        for fid, fn in ids.items():
            for f in (fn, fn.replace(".fnt", ".png")):
                if not os.path.exists(os.path.join(fd, f)):
                    errors.append("%s: missing %s" % (rel(fd), f))

        def charset(name):
            return {int(m) for m in re.findall(r"char id=(\d+)", open(os.path.join(fd, name + ".fnt")).read())}
        cs = {n: charset(n) for n in ("luxe_num", "luxe_l", "luxe_m", "luxe_s", "luxe_xs", "ayah")}
        xs_keys = [k for k in res["Strings"] if re.match(
            r"(Day|Month|Hijri)\d+$|HijriSuffix$|Prayer\d$|SetLocation$|Label\w+$|AyahRef\d$", k)]
        for table in (res["Strings"], fre):
            for k in xs_keys:
                for ch in table.get(k, ""):
                    if ord(ch) not in cs["luxe_xs"]:
                        errors.append("%s: luxe_xs lacks %r used by string %s" % (rel(fd), ch, k))
        for ch in "0123456789:-hmk. %":
            for f in ("luxe_xs", "luxe_s", "luxe_m"):
                if ord(ch) not in cs[f]:
                    errors.append("%s: %s lacks %r" % (rel(fd), f, ch))
        for f, chars in (("luxe_l", "0123456789"), ("luxe_num", "12369"), ("ayah", "1234567ABC")):
            for ch in chars:
                if ord(ch) not in cs[f]:
                    errors.append("%s: %s lacks %r" % (rel(fd), f, ch))
    notes.append("font sets: %d (%s)" % (len(font_dirs), ", ".join(rel(d) for d in font_dirs)))

    # ---- backgrounds
    arity = {0: None, 1: 5, 2: 7, 3: None, 4: None, 5: 6, 6: 6, 7: 6, 8: 2, 9: 9, 10: 7, 11: 8}
    for path in glob.glob(os.path.join(ROOT, "resources", "jsonData", "*.json")):
        ops = json.load(open(path))
        for op in ops:
            code = op[0]
            if code not in arity:
                errors.append("%s: bad op %s" % (rel(path), op[:3]))
                continue
            if arity[code] is not None and len(op) != arity[code]:
                errors.append("%s: op %d has %d fields" % (rel(path), code, len(op)))
            if not 0 <= op[1] <= 15 or (code == 9 and not 0 <= op[2] <= 15):
                errors.append("%s: bad colour role in %s" % (rel(path), op[:3]))
            if code == 0 and (len(op) % 2 or len(op) - 2 > 128):
                errors.append("%s: bad polygon" % rel(path))
            if code in (3, 4) and (len(op) - 3) % 2:
                errors.append("%s: odd coordinate count" % rel(path))
        notes.append("%s: %d ops, %d bytes" % (rel(path), len(ops), os.path.getsize(path)))

    # ---- Monkey C syntax
    plugin = os.path.join(ROOT, "tools", "node_modules", "@markw65", "prettier-plugin-monkeyc")
    if shutil.which("node") and os.path.isdir(plugin):
        for p in sorted(sources):
            r = subprocess.run(["npx", "--no-install", "prettier", "--plugin", "@markw65/prettier-plugin-monkeyc",
                                "--parser", "monkeyc", p], cwd=os.path.join(ROOT, "tools"),
                               capture_output=True, text=True)
            if r.returncode != 0:
                errors.append("%s: Monkey C syntax error: %s" % (rel(p), r.stderr.strip().splitlines()[0]))
        notes.append("Monkey C syntax: %d files parsed" % len(sources))
    else:
        notes.append("Monkey C syntax check skipped (run `npm install` in tools/)")

    for n in notes:
        print("note:", n)
    for e in errors:
        print("ERROR:", e)
    print("project check:", "PASS" if not errors else "FAIL (%d)" % len(errors))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
