"""Turn four pictures into the built-in wallpapers (skin/res/drawable-nodpi/wallpaper_1..4.webp).

FongMi shows wallpaper_N (N = 1..4, the first is the default) behind every screen; the skin adds a
readability scrim on top (drawable/tvos_wall_scrim), so pictures should already be on the dark
side. Each picture is cover-cropped to 16:9, scaled to 1920x1080 and lightly dithered so smooth
gradients do not band on 8-bit panels.

    python -I tools/import_wallpapers.py work/wallpapers/1-dunes.png work/wallpapers/2-aurora.png ...
(order = slot order; tools/gen_wallpapers.py draws a fallback set in code if no pictures are at hand)
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "skin" / "res" / "drawable-nodpi"
W, H = 1920, 1080


def cover(img):
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def main(paths):
    if len(paths) != 4:
        raise SystemExit("give exactly four pictures, in slot order (the first is the default wallpaper)")
    rng = np.random.default_rng(7)
    OUT.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(paths, 1):
        img = np.asarray(cover(Image.open(p).convert("RGB")), np.float32)
        img += rng.uniform(-1.2, 1.2, img.shape)
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / f"wallpaper_{i}.webp", "WEBP", quality=92, method=6)
        print(f"wallpaper_{i}.webp <- {p}")


if __name__ == "__main__":
    main(sys.argv[1:])
