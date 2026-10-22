"""Reskin an official FongMi release APK with the resources in skin/res.

    python -I tools/build.py --version 5.8.0 --abi armeabi_v7a          # skinned build
    python -I tools/build.py --version 5.8.0 --abi armeabi_v7a --plain  # round-trip only

Only resources change: classes*.dex, lib/ and assets/ are copied from the official
APK untouched (apktool -s), so FongMi's behaviour stays exactly the upstream one.
"""

import argparse
import copy
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIN = ROOT / "skin" / "res"
APKTOOL = ROOT / "tools" / "apktool_3.0.3.jar"
BUILD_TOOLS = Path.home() / "AppData/Local/Android/Sdk/build-tools/37.0.0"
RELEASE_URL = "https://github.com/FongMi/Release/releases/download/{version}/leanback-{abi}.apk"
ANDROID_NS = "http://schemas.android.com/apk/res/android"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ids import check_layouts  # noqa: E402
import gen_rows  # noqa: E402
import gen_type  # noqa: E402


def run(*cmd):
    print("+", " ".join("pass:***" if str(c).startswith("pass:") else str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def fetch(version, abi):
    apk = ROOT / "apk" / f"leanback-{abi}-{version}.apk"
    if not apk.exists():
        apk.parent.mkdir(exist_ok=True)
        url = RELEASE_URL.format(version=version, abi=abi)
        print("download", url, flush=True)
        urllib.request.urlretrieve(url, apk)
    return apk


def decode(apk, base):
    if (base / "apktool.yml").exists() and (base / ".source").read_text() == apk.name:
        return
    shutil.rmtree(base, ignore_errors=True)
    run("java", "-jar", APKTOOL, "d", "-s", "-f", "-o", base, apk)
    (base / ".source").write_text(apk.name)


def key_of(el):
    return el.tag, el.get("type", ""), el.get("name")


def merge_values(skin_dir, target_dir):
    """Replace same-named resources in place; add new ones to skin_*.xml."""
    index = {}
    trees = {}
    for path in sorted(target_dir.glob("*.xml")):
        if path.name == "public.xml":
            continue
        tree = ET.parse(path)
        trees[path] = tree
        for el in tree.getroot():
            index[key_of(el)] = (path, el)
    changed = set()
    for skin_file in sorted(skin_dir.glob("*.xml")):
        added = ET.Element("resources")
        for el in ET.parse(skin_file).getroot():
            if not isinstance(el.tag, str):
                continue
            hit = index.get(key_of(el))
            if hit:
                path, old = hit
                old.clear()
                old.tag, old.text, old.tail = el.tag, el.text, old.tail
                old.attrib.update(el.attrib)
                for child in el:
                    old.append(copy.deepcopy(child))
                changed.add(path)
            else:
                added.append(copy.deepcopy(el))
        if len(added):
            out = target_dir / f"skin_{skin_file.name}"
            ET.ElementTree(added).write(out, encoding="utf-8", xml_declaration=True)
            print(f"  values: +{len(added)} new from {skin_file.name}")
    for path in changed:
        trees[path].write(path, encoding="utf-8", xml_declaration=True)
        print(f"  values: replaced entries in {path.name}")


def overlay(work):
    ET.register_namespace("android", ANDROID_NS)
    res = work / "res"
    for src_dir in sorted(p for p in SKIN.iterdir() if p.is_dir()):
        dst_dir = res / src_dir.name
        if src_dir.name.startswith("values"):
            dst_dir.mkdir(exist_ok=True)
            merge_values(src_dir, dst_dir)
            continue
        dst_dir.mkdir(exist_ok=True)
        for f in sorted(src_dir.iterdir()):
            # A drawable may exist under another extension (png vs xml vs webp); drop it so names stay unique.
            for stale in dst_dir.glob(f.stem + ".*"):
                stale.unlink()
            shutil.copy2(f, dst_dir / f.name)
        print(f"  {src_dir.name}: {sum(1 for _ in src_dir.iterdir())} file(s)")


def brand(work):
    """Own identity (skin/brand.json): package, provider authorities and the signature permission
    move to the new package so both apps can be installed; the launcher activity gets the FFalcon
    cyberui full-card meta-data. Class names in the manifest are fully qualified, so they stay put."""
    import json
    cfg = json.loads((ROOT / "skin" / "brand.json").read_text(encoding="utf-8"))
    old, new = cfg["upstream_package"], cfg["package"]
    m = work / "AndroidManifest.xml"
    text = m.read_text(encoding="utf-8")
    text = text.replace(f'package="{old}"', f'package="{new}"', 1)
    text = re.sub(rf'android:authorities="{re.escape(old)}\.', f'android:authorities="{new}.', text)
    text = text.replace(f"{old}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION", f"{new}.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION")
    home = f'android:name="{old}.ui.activity.HomeActivity"'
    i = text.index(home)
    j = text.index(">", i) + 1
    if 'beidouui_icon' not in text:
        card = cfg["ffalcon_card"]
        text = text[:j] + f'\n            <meta-data android:name="beidouui_icon" android:value="{card}"/>' + text[j:]
    m.write_text(text, encoding="utf-8")
    assets = ROOT / "skin" / "assets"
    if assets.exists():
        for f in assets.iterdir():
            shutil.copy2(f, work / "assets" / f.name)
    print(f"  brand: {cfg['label']} ({new})")


def sign(unsigned, out):
    props = dict(line.split("=", 1) for line in (ROOT / "keys/skin.properties").read_text().split() if "=" in line)
    aligned = unsigned.with_suffix(".aligned.apk")
    run(BUILD_TOOLS / "zipalign.exe", "-P", "16", "-f", "4", unsigned, aligned)
    run(BUILD_TOOLS / "apksigner.bat", "sign", "--ks", ROOT / props["storeFile"], "--ks-key-alias", props["keyAlias"],
        "--ks-pass", "pass:" + props["storePassword"], "--out", out, aligned)
    run(BUILD_TOOLS / "apksigner.bat", "verify", out)
    aligned.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True)
    ap.add_argument("--abi", default="armeabi_v7a", choices=["armeabi_v7a", "arm64_v8a"])
    ap.add_argument("--plain", action="store_true", help="rebuild without the skin (round-trip test)")
    args = ap.parse_args()

    apk = fetch(args.version, args.abi)
    tag = f"{args.version}-{args.abi}"
    base = ROOT / "work" / tag / "base"
    work = ROOT / "work" / tag / "build"
    decode(apk, base)

    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(base, work)
    if not args.plain:
        # layouts/styles derived from upstream are regenerated from the version being skinned
        print(f"  generated: {gen_rows.generate(base / 'res', quiet=True)} layouts, "
              f"{gen_type.generate(base / 'res', quiet=True)} text appearances", flush=True)
        problems = check_layouts(SKIN, base / "res")
        if problems:
            print("\n".join(problems))
            sys.exit("check_ids: skin layouts no longer match upstream; sync them first")
        overlay(work)
        brand(work)

    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    unsigned = out_dir / f"unsigned-{tag}.apk"
    run("java", "-jar", APKTOOL, "b", "-f", "-o", unsigned, work)
    name = f"{'fongmi-plain' if args.plain else 'guangying'}-{tag}.apk"
    sign(unsigned, out_dir / name)
    unsigned.unlink()
    print("OK", out_dir / name)


if __name__ == "__main__":
    main()
