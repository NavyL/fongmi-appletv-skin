"""Check that every skin layout keeps upstream's view ids and view classes.

FongMi's Java finds views through ViewBinding (by id, cast to the declared class),
so a replaced layout must keep each upstream id on a view of the same class.
New ids are allowed; nothing may be removed or retyped.

    python -I tools/check_ids.py <decoded-apk-res-dir>
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_ID = "{http://schemas.android.com/apk/res/android}id"


def ids(path):
    found = {}
    for el in ET.parse(path).iter():
        ref = el.get(ANDROID_ID)
        if ref:
            found[ref.split("/", 1)[1]] = el.tag
    return found


def check_layouts(skin_res, base_res):
    problems = []
    for skin_dir in sorted(Path(skin_res).glob("layout*")):
        for skin_file in sorted(skin_dir.glob("*.xml")):
            upstream = Path(base_res) / skin_dir.name / skin_file.name
            if not upstream.exists():
                problems.append(f"{skin_dir.name}/{skin_file.name}: no such layout upstream")
                continue
            want, have = ids(upstream), ids(skin_file)
            for vid, cls in want.items():
                if vid not in have:
                    problems.append(f"{skin_dir.name}/{skin_file.name}: id '{vid}' ({cls}) missing")
                elif have[vid] != cls:
                    problems.append(f"{skin_dir.name}/{skin_file.name}: id '{vid}' is {have[vid]}, upstream {cls}")
    return problems


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    found = check_layouts(root / "skin" / "res", sys.argv[1])
    print("\n".join(found) or "ok")
    sys.exit(1 if found else 0)
