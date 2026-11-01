#!/usr/bin/env python3
"""Rewrite the <iq:products> list of manifest.xml from the device files of the installed
Connect IQ SDK, so that the watch face targets every current round colour watch.

Run it on the machine where the SDK Manager has downloaded the devices:
    python3 tools/update_products.py            # show what would change
    python3 tools/update_products.py --write    # update manifest.xml

A device is selected when its compiler.json says:
  * round display whose resolution has a font set in this project (218 ... 454 px),
  * more than 1 bit per pixel (colour; monochrome Instinct models are excluded),
  * watch faces are supported,
  * Connect IQ 4.0 or newer (the manifest's minApiLevel).
Fields that are missing in a device file are reported; such devices are skipped unless
--include-unknown is given. Check the result in the SDK's device list before publishing.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZES = {218, 240, 260, 280, 360, 390, 416, 454}
MIN_CIQ = (4, 0, 0)


def device_dirs():
    env = os.environ.get("CIQ_DEVICES")
    cands = [env] if env else []
    home = os.path.expanduser("~")
    cands += [os.path.join(home, ".Garmin", "ConnectIQ", "Devices"),
              os.path.join(home, "Library", "Application Support", "Garmin", "ConnectIQ", "Devices"),
              os.path.join(os.environ.get("APPDATA", ""), "Garmin", "ConnectIQ", "Devices")]
    for c in cands:
        if c and os.path.isdir(c):
            return c
    return None


def version(v):
    nums = [int(x) for x in re.findall(r"\d+", str(v))[:3]]
    return tuple(nums + [0] * (3 - len(nums)))


def assess(cfg):
    """Returns (selected?, reasons, unknown fields)."""
    unknown, reasons = [], []
    res = cfg.get("resolution") or {}
    w, h = res.get("width"), res.get("height")
    shape = cfg.get("displayType")
    bpp = cfg.get("bitsPerPixel")
    if w is None or h is None:
        unknown.append("resolution")
    elif not (w == h and w in SIZES):
        reasons.append("%sx%s" % (w, h))
    if shape is None:
        unknown.append("displayType")
    elif str(shape).lower() != "round":
        reasons.append(str(shape))
    if bpp is None:
        unknown.append("bitsPerPixel")
    elif int(bpp) <= 1:
        reasons.append("monochrome")
    types = [str(t.get("type", "")).lower() for t in cfg.get("appTypes", []) if isinstance(t, dict)]
    if not types:
        unknown.append("appTypes")
    elif "watchface" not in types:
        reasons.append("no watch faces")
    versions = [version(p.get("connectIQVersion")) for p in cfg.get("partNumbers", []) if isinstance(p, dict)
                and p.get("connectIQVersion")]
    if not versions:
        unknown.append("connectIQVersion")
    elif max(versions) < MIN_CIQ:
        reasons.append("CIQ %s" % ".".join(map(str, max(versions))))
    return (not reasons and not unknown), reasons, unknown


def main():
    write = "--write" in sys.argv
    include_unknown = "--include-unknown" in sys.argv
    base = device_dirs()
    if base is None:
        sys.exit("Connect IQ device folder not found (set CIQ_DEVICES=/path/to/Devices).")
    selected = []
    for cfg_path in sorted(glob.glob(os.path.join(base, "*", "compiler.json"))):
        dev = os.path.basename(os.path.dirname(cfg_path))
        cfg = json.load(open(cfg_path))
        dev = cfg.get("deviceId", dev)
        ok, reasons, unknown = assess(cfg)
        if ok or (include_unknown and not reasons):
            selected.append(dev)
            print("  + %-24s %s" % (dev, cfg.get("displayName", "")))
        elif unknown:
            print("  ? %-24s missing %s" % (dev, ", ".join(unknown)))
    man_path = os.path.join(ROOT, "manifest.xml")
    man = open(man_path).read()
    block = "\n".join('            <iq:product id="%s" />' % d for d in selected)
    new = re.sub(r"(<iq:products>\n)(.*?)(\n\s*</iq:products>)", lambda m: m.group(1) + block + m.group(3), man,
                 flags=re.S)
    print("%d devices selected" % len(selected))
    if write:
        open(man_path, "w").write(new)
        print("manifest.xml updated")


if __name__ == "__main__":
    main()
