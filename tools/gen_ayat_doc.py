#!/usr/bin/env python3
"""Writes docs/AYAT.md from tools/ayat.json and tools/assets-report.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "tools", "ayat.json")))
rep = json.load(open(os.path.join(ROOT, "tools", "assets-report.json")))["fonts"]
out = ["# Ayah library", "",
       "Only **complete verses** are used (owner's requirement), chosen among short, well-known verses so that each "
       "fits on one line at a legible size (at least 13 px on a 280 px screen).", "",
       "* Arabic source: %s." % d["source_arabic"],
       "* French translation (documentation only, too small to show on the watch): %s." % d["source_french"],
       "* Every verse is shaped with HarfBuzz (Amiri Bold, SIL OFL) by `tools/build_assets.py` and stored as one glyph "
       "of the fonts Ayah0..Ayah4 (8 verses per font, only the font of the current verse is loaded). The reference "
       "under the verse (surah name and verse number) is in Arabic.",
       "* Settings: *Ayah* = hourly rotation over the verses ticked in the settings (default: all), a fixed verse, "
       "or hidden. The rotation changes verse at every full hour.", "",
       "| # | Reference | Arabic | Reference shown | Font px at 218 / 280 / 454 | French (Hamidullah) |",
       "|---|---|---|---|---|---|"]
for a in d["ayat"]:
    px = " / ".join(str(rep[s]["ayah"][a["ref"]]["px"]) for s in ("218", "280", "454"))
    out.append("| %d | %s | %s | %s | %s | %s |" % (a["index"] + 1, a["ref"], a["lines"][0], a["ref_ar"], px,
                                                   a["fr"].strip()))
out += ["", "Removed from the first version because they are too long to be shown complete: Taha 20:114, "
        "Al-Baqarah 2:286, Al-Imran 3:8, Al-Fath 48:4, Hud 11:88 (the specification listed them; the owner asked "
        "for complete verses only). The Basmala that one source prepends to the first verse of each surah is not "
        "part of those verses and is not shown.", ""]
open(os.path.join(ROOT, "docs", "AYAT.md"), "w").write("\n".join(out))
print("docs/AYAT.md: %d verses" % len(d["ayat"]))
