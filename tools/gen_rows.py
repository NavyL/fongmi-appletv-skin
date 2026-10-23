"""Generate tvOS-style layouts from upstream's, for screens built from many similar rows.

Upstream rows/pills are focusable views (selector_item / selector_chip_round / selector_button)
holding white labels and white icons. A white focus plate needs that content to turn dark, so each
such view gets a tvOS selector and its texts/icons follow its state (duplicateParentState + colour
selectors). Ids, classes and structure are untouched, so check_ids passes by construction.

build.py runs this on every build, so the layouts always follow the upstream version being skinned.
Standalone: python -I tools/gen_rows.py --base work/<version>-<abi>/base/res
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unclip  # noqa: E402

A = "{http://schemas.android.com/apk/res/android}"
APP = "{http://schemas.android.com/apk/res-auto}"
OUT = Path(__file__).resolve().parent.parent / "skin" / "res" / "layout"

# upstream selector -> tvOS selector
SELECTORS = {
    "@drawable/selector_item": "@drawable/selector_tvos_tile",
    "@drawable/selector_chip_round": "@drawable/selector_tvos_pill",
    "@drawable/selector_button": "@drawable/selector_tvos_pill",
    "@drawable/selector_chip": "@drawable/selector_tvos_pill",
}
# per-layout replacements where the generic choice would look wrong (two-line rows want a tile)
SELECTOR_OVERRIDES = {"view_decoder_mode_row": "@drawable/selector_tvos_tile"}
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
    # player: parse-line chips, decoder mode rows
    "adapter_parse", "view_decoder_mode_row",
]
# screens taken from upstream unchanged except for the content fade when they open
ENTER_ONLY = ["activity_vod"]
SCREEN_ENTER = "@anim/tvos_screen_enter"
SETTINGS = False
ROW_GAP = "20.0dp"
UPSTREAM = None
CHECK_TINT = "#FF8E8E93"  # visible on both the white plate and navy; a checkbox keeps its own checked state


def is_text(el):
    return el.tag.endswith("TextView") or el.tag.endswith("CustomUpDownView")


def is_image(el):
    return el.tag.endswith("ImageView") or el.tag.endswith("DialogActionView")


def is_check(el):
    return el.tag.endswith("CheckBox")


def animator_for(view, tile):
    """Settings pages grow the focused row a little (tvOS 1.02, icon buttons 1.05). Rows in dialogs and
    sheets stay put like tvOS menus: their lists clip, and a grown row would lose its rounded ends."""
    if not SETTINGS:
        return "@animator/tvos_press_flat"
    if is_image(view):
        return "@animator/tvos_press"
    return "@animator/tvos_press_tile"


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
        colour = t.get(A + "textColor")
        if colour in ("@color/white", "@color/text", None) or (colour or "").startswith("?"):
            primary = "@color/tvos_on_pill" if colour == "@color/text" else "@color/tvos_on_button"
            t.set(A + "textColor", primary if i == 0 else "@color/tvos_on_button_secondary")
    for e in (e for e in view.iter() if e is not view):
        if is_image(e):
            e.set(A + "duplicateParentState", "true")
            e.set(APP + "tint", "@color/tvos_on_button")
        elif is_check(e):
            e.set(APP + "buttonTint", CHECK_TINT)


def generate(base, quiet=False):
    """base: decoded upstream res dir."""
    global UPSTREAM
    base = Path(base)
    UPSTREAM = base / "layout"
    ET.register_namespace("android", A[1:-1])
    ET.register_namespace("app", APP[1:-1])
    global SETTINGS
    for name in ENTER_ONLY:
        tree = parse_upstream(name)
        tree.getroot().set(A + "layoutAnimation", SCREEN_ENTER)
        write(name, tree)
    for name in FILES:
        SETTINGS = name.startswith("activity_setting")
        tree = parse_upstream(name)
        if SETTINGS:  # title-safe area (HIG: 80/60 pt at 1080p = 40/30 dp on FongMi's 960 canvas)
            for e in tree.iter():
                if e.get(A + "padding") == "24.0dp":
                    del e.attrib[A + "padding"]
                    for k, v in (("paddingStart", "40.0dp"), ("paddingEnd", "40.0dp"), ("paddingTop", "30.0dp"), ("paddingBottom", "30.0dp")):
                        e.set(A + k, v)
        if SETTINGS:  # a little more air between rows (upstream 16dp)
            for e in tree.iter():
                if e.get(A + "layout_marginTop") == "16.0dp":
                    e.set(A + "layout_marginTop", ROW_GAP)
        if SETTINGS:  # page title: the one plain 20sp label above the rows
            for e in tree.iter():
                if is_text(e) and e.get(A + "id") is None and e.get(A + "background") is None and e.get(A + "textSize") == "20.0sp":
                    e.set(A + "textSize", "22.0sp")
                    e.set(A + "fontFamily", "@font/tvos_display")
                    e.set(A + "textFontWeight", "600")
                    e.set(A + "layout_marginBottom", "18.0dp")
        if name.startswith("activity_") and name != "activity_crash":
            tree.getroot().set(A + "layoutAnimation", SCREEN_ENTER)
        views = [e for e in tree.iter() if e.get(A + "background") in SELECTORS]
        for view in views:
            restyle(view, SELECTOR_OVERRIDES.get(name, SELECTORS[view.get(A + "background")]))
        write(name, tree)
        if not quiet:
            print(f"{name}: {len(views)}")
    return len(FILES) + len(ENTER_ONLY)


def parse_upstream(name):
    path = UPSTREAM / f"{name}.xml"
    if not path.exists():
        raise SystemExit(f"gen_rows: upstream has no layout/{name}.xml any more; drop it from FILES/ENTER_ONLY")
    return ET.parse(path)


def write(name, tree):
    unclip.apply(tree.getroot(), ET.parse(UPSTREAM / f"{name}.xml").getroot())
    body = ET.tostring(tree.getroot(), encoding="unicode")
    (OUT / f"{name}.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f"<!-- GENERATED by tools/gen_rows.py from upstream {name}.xml. Do not edit by hand. -->\n"
        + body + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="decoded upstream res dir")
    generate(ap.parse_args().base)


if __name__ == "__main__":
    main()
