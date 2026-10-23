"""Move D-pad focus to the control that shows <text>, pressing <key> until it does.

The focusable view is usually a container; the text sits on a child. So a node matches when it
or any descendant carries the text.

    python -I tools/focus.py <text> <keycode> [max_presses]
exit 0 when focused, 1 when not found (prints what has focus instead).
"""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

E = ["adb", "-s", os.environ.get("EMU", "emulator-5554")]


def dump():
    subprocess.run(E + ["shell", "uiautomator", "dump", "/sdcard/ui.xml"], capture_output=True)
    xml = subprocess.run(E + ["shell", "cat", "/sdcard/ui.xml"], capture_output=True).stdout
    try:
        return ET.fromstring(xml)
    except ET.ParseError:
        return None


def texts(node):
    return [t for t in (n.get("text", "") for n in node.iter()) if t]


def focused(root):
    for n in root.iter():
        if n.get("focused") == "true":
            return n
    return None


def main():
    text, key = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 14
    last = None
    for _ in range(limit):
        root = dump()
        if root is not None:
            f = focused(root)
            if f is not None:
                last = texts(f)
                if any(text in t for t in last):
                    return 0
        subprocess.run(E + ["shell", "input", "keyevent", key], capture_output=True)
    print(f"focus: miss {text!r}; focus is on {last}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
