"""Generate tvOS-style layouts from upstream's, for screens built from many similar rows.

Upstream rows/pills are focusable views (selector_item / selector_chip_round / selector_button)
holding white labels and white icons. A white focus plate needs that content to turn dark, so each
such view gets a tvOS selector and its texts/icons follow its state (duplicateParentState + colour
selectors). Ids, classes and structure are untouched, so check_ids passes by construction.

Re-run after each upstream version bump (build.py does not run it):
    python -I tools/gen_rows.py --base work/<version>-<abi>/base/res
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

A = "{http://schemas.android.com/apk/res/android}"
APP = "{http://schemas.android.com/apk/res-auto}"
OUT = Path(__file__).resolve().parent.parent / "skin" / "res" / "layout"

# upstream selector -> tvOS selector
SELECTORS = {
    "@drawable/selector_item": "@drawable/selector_tvos_tile",
    "@drawable/selector_chip_round": "@drawable/selector_tvos_pill",
    "@drawable/selector_button": "@drawable/selector_tvos_pill",
}
# Layouts generated here. Layouts with hand-written overrides in skin/res/layout are not listed.
FILES = [
    # settings pages (rows of label + value, icon buttons)
    "activity_setting", "activity_setting_player", "activity_setting_decode",
    "activity_setting_preload", "activity_setting_danmaku", "item_module",
    # dialogs and their lists
    "adapter_chapter", "adapter_config", "adapter_danmaku", "adapter_doh", "adapter_edition",
    "adapter_live", "adapter_restore", "adapter_site", "adapter_subtitle", "adapter_track",
    "dialog_config", "dialog_danmaku", "dialog_danmaku_search", "dialog_module", "dialog_mpv_conf",
    "dialog_pass", "dialog_player_engine", "dialog_single_input", "dialog_site",
    "dialog_subtitle_search", "dialog_track", "dialog_update", "activity_module", "activity_crash",
]
SETTINGS = False
CHECK_TINT = "#FF8E8E93"  # visible on both the white plate and navy; a checkbox keeps its own checked state


def is_text(el):
    return el.tag.endswith("TextView") or el.tag.endswith("CustomUpDownView")


def is_image(el):
    return el.tag.endswith("ImageView") or el.tag.endswith("DialogActionView")


def is_check(el):
    return el.tag.endswith("CheckBox")


def animator_for(view, tile):
    """Grow with focus only where there is room: a full-width row in a dialog list would be clipped."""
    full = view.get(A + "layout_width") in ("match_parent", "0.0dp")
    if is_image(view):
        return "@animator/tvos_press"
    if full and not SETTINGS:
        return "@animator/tvos_press_flat"
    return "@animator/tvos_press_tile" if (tile or full) else "@animator/tvos_press"


def pad(el, h, v):
    if el.get(A + "padding") is None and el.get(A + "paddingStart") is None and el.get(A + "paddingLeft") is None:
        el.set(A + "paddingStart", h)
        el.set(A + "paddingEnd", h)
        el.set(A + "paddingTop", v)
        el.set(A + "paddingBottom", v)


def restyle(view, pill):
    view.set(A + "background", pill)
    tile = pill.endswith("tile")
    view.set(A + "stateListAnimator", animator_for(view, tile))
    if is_image(view):
        view.set(APP + "tint", "@color/tvos_on_button")
        return
    if is_text(view):
        view.set(A + "textColor", "@color/tvos_on_pill")
        pad(view, "14.0dp", "9.0dp" if tile else "7.0dp")
        return
    pad(view, "16.0dp", "11.0dp" if tile else "7.0dp")
    texts = [e for e in view.iter() if e is not view and is_text(e) and e.get(A + "background") is None]
    for i, t in enumerate(texts):
        t.set(A + "duplicateParentState", "true")
        if t.get(A + "textColor") in ("@color/white", "@color/text", None):
            primary = "@color/tvos_on_pill" if t.get(A + "textColor") == "@color/text" else "@color/tvos_on_button"
            t.set(A + "textColor", primary if i == 0 else "@color/tvos_on_button_secondary")
    for e in (e for e in view.iter() if e is not view):
        if is_image(e):
            e.set(A + "duplicateParentState", "true")
            e.set(APP + "tint", "@color/tvos_on_button")
        elif is_check(e):
            e.set(APP + "buttonTint", CHECK_TINT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="decoded upstream res dir")
    base = Path(ap.parse_args().base)
    ET.register_namespace("android", A[1:-1])
    ET.register_namespace("app", APP[1:-1])
    global SETTINGS
    for name in FILES:
        SETTINGS = name.startswith("activity_setting")
        tree = ET.parse(base / "layout" / f"{name}.xml")
        if SETTINGS:  # title-safe area (HIG: 80/60 pt at 1080p = 40/30 dp on FongMi's 960 canvas)
            for e in tree.iter():
                if e.get(A + "padding") == "24.0dp":
                    del e.attrib[A + "padding"]
                    for k, v in (("paddingStart", "40.0dp"), ("paddingEnd", "40.0dp"), ("paddingTop", "30.0dp"), ("paddingBottom", "30.0dp")):
                        e.set(A + k, v)
        views = [e for e in tree.iter() if e.get(A + "background") in SELECTORS]
        for view in views:
            restyle(view, SELECTORS[view.get(A + "background")])
        body = ET.tostring(tree.getroot(), encoding="unicode")
        (OUT / f"{name}.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            f"<!-- GENERATED by tools/gen_rows.py from upstream {name}.xml. Do not edit by hand. -->\n"
            + body + "\n", encoding="utf-8")
        print(f"{name}: {len(views)}")


if __name__ == "__main__":
    main()
