"""List layouts that use the shared focus selectors, with their text colours.

    python -I tools/inventory.py <decoded-res-dir>
"""

import collections
import re
import sys
from pathlib import Path

SELECTORS = ["selector_item", "selector_item_round", "selector_chip", "selector_chip_round", "selector_button",
             "selector_live", "selector_keyboard", "selector_vod", "selector_vod_oval", "selector_subtitle",
             "selector_video", "selector_playback_dialog_switch"]

res = Path(sys.argv[1])
styles = (res / "values/styles.xml").read_text(encoding="utf-8")
uses = collections.defaultdict(list)
for f in sorted(res.glob("layout*/*.xml")):
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r"<([\w.]+)\s([^<>]*?)/?>", text, re.S):
        attrs = m.group(2)
        style = re.search(r'style="@style/([^"]+)"', attrs)
        for sel in SELECTORS:
            direct = re.search(r'@drawable/' + sel + '"', attrs)
            via_style = style and re.search(r'name="' + re.escape(style.group(1)) + r'"[^>]*>(?:(?!</style>).)*@drawable/' + sel + '<', styles, re.S)
            if direct or via_style:
                tc = re.search(r'textColor="([^"]+)"', attrs)
                uses[sel].append((f.parent.name + "/" + f.name, m.group(1).split(".")[-1], tc.group(1) if tc else "-"))
for sel in SELECTORS:
    if not uses[sel]:
        continue
    print(f"## {sel} ({len(uses[sel])})")
    for (tag, tc), n in collections.Counter((t, c) for _, t, c in uses[sel]).most_common():
        print(f"   {n:3}  {tag:30} text={tc}")
    print("   files:", " ".join(sorted({u[0].split('/')[1][:-4] for u in uses[sel]})))
