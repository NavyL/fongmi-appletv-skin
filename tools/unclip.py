"""Let focused rows/chips grow without their rounded ends being cut off.

A focused control scales up (stateListAnimator); with hardware rendering a ViewGroup that clips
children cuts each child to the child's own bounds, so a row's container must not clip the row
while it overflows. The exception is a ViewGroup that directly holds a scrolling list: it has to
keep clipping, or rows scrolled past the list's edge would draw over whatever sits next to it.

    python -I tools/unclip.py skin/res/layout/<hand-written>.xml ...   # rewrites in place
gen_rows.py applies the same rule to the layouts it generates.
"""

import re
import sys
import xml.etree.ElementTree as ET

A = "{http://schemas.android.com/apk/res/android}"
SCROLLERS = ("RecyclerView", "GridView", "ScrollView", "ViewPager", "ListView", "LiveListView", "WebView")


def is_scroller(el):
    return el.tag.split(".")[-1].endswith(SCROLLERS)


def apply(root, upstream_root=None):
    for e in root.iter():
        if not len(e):
            continue
        e.set(A + "clipToPadding", "false")
        if any(is_scroller(c) for c in e):
            original = upstream_root.get(A + "clipChildren") if (e is root and upstream_root is not None) else None
            if original is not None:
                e.set(A + "clipChildren", original)
            else:
                e.attrib.pop(A + "clipChildren", None)
        else:
            e.set(A + "clipChildren", "false")


def rewrite(path, upstream_dir):
    text = open(path, encoding="utf-8").read()
    header = re.match(r'(<\?xml[^>]*\?>\s*(?:<!--.*?-->\s*)?)', text, re.S).group(1)
    ET.register_namespace("android", A[1:-1])
    ET.register_namespace("app", "http://schemas.android.com/apk/res-auto")
    ET.register_namespace("tools", "http://schemas.android.com/tools")
    tree = ET.parse(path)
    upstream = None
    if upstream_dir:
        try:
            upstream = ET.parse(f"{upstream_dir}/{path.replace(chr(92), '/').split('/')[-1]}").getroot()
        except (FileNotFoundError, ET.ParseError):
            upstream = None
    apply(tree.getroot(), upstream)
    open(path, "w", encoding="utf-8").write(header.rstrip() + "\n" + ET.tostring(tree.getroot(), encoding="unicode") + "\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    upstream_dir = None
    if args and args[0].startswith("--upstream="):
        upstream_dir = args.pop(0).split("=", 1)[1]
    for p in args:
        rewrite(p, upstream_dir)
        print("unclipped", p)
