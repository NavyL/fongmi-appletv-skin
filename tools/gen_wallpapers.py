"""Draw the four built-in wallpapers (skin/res/drawable-nodpi/wallpaper_1..4.webp).

FongMi shows wallpaper_N behind every screen (CustomWallView); upstream ships green photos.
These follow the tvOS look: dark, quiet, no brand hue, so posters carry the colour.

    python -I tools/gen_wallpapers.py
"""

from pathlib import Path

import numpy as np
from PIL import Image

W, H = 1920, 1080
OUT = Path(__file__).resolve().parent.parent / "skin" / "res" / "drawable-nodpi"
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = xx / W, yy / H


def rgb(hexstr):
    return np.array([int(hexstr[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def glow(cx, cy, rx, ry):
    """Soft radial falloff 1 → 0."""
    d = ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2
    return np.exp(-d)


def mix(base, color, weight):
    return base * (1 - weight[..., None]) + rgb(color) * weight[..., None]


def save(img, name):
    img = img + rng.uniform(-1.2, 1.2, img.shape)  # dither: no banding on 8-bit panels
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / name, "WEBP", quality=92, method=6)
    print("wrote", name)


def canvas(color):
    return np.broadcast_to(rgb(color), (H, W, 3)).copy()


def navy():
    """1: Yingxia's canvas #050917 with a faint blue light from the top left."""
    img = canvas("#050917")
    img = mix(img, "#13254F", 0.55 * glow(0.18, -0.05, 0.75, 0.65))
    img = mix(img, "#0B1430", 0.35 * glow(0.95, 1.1, 0.6, 0.5))
    return img


def dunes():
    """2: Mac-style dunes in indigo dusk."""
    img = canvas("#070B1E")
    img = mix(img, "#2A2F66", 0.6 * glow(0.55, 0.15, 0.9, 0.55))
    img = mix(img, "#4A3A6E", 0.25 * glow(0.75, 0.35, 0.5, 0.3))
    layers = [(0.58, "#1A1D45", 0.035, 1.3, 0.2), (0.68, "#14173A", 0.04, 1.7, 1.1),
              (0.78, "#0E1130", 0.03, 2.2, 2.3), (0.88, "#090B22", 0.025, 2.9, 0.7)]
    for base, color, amp, freq, phase in layers:
        ridge = base + amp * np.sin(u * np.pi * freq + phase) + 0.012 * np.sin(u * np.pi * freq * 3.1 + phase * 2)
        edge = np.clip((v - ridge) / 0.004, 0, 1)
        shade = mix(np.broadcast_to(rgb(color), (H, W, 3)), "#000000", np.clip((v - ridge) * 1.8, 0, 0.5))
        img = img * (1 - edge[..., None]) + shade * edge[..., None]
    return img


def ember():
    """3: warm black with a low ember glow (Yingxia's older look)."""
    img = canvas("#100D0B")
    img = mix(img, "#3A2416", 0.55 * glow(0.8, 1.05, 0.7, 0.55))
    img = mix(img, "#1E1712", 0.5 * glow(0.15, 0.0, 0.6, 0.5))
    return img


def black():
    """4: plain black, the tvOS system background."""
    return canvas("#000000")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for i, draw in enumerate([navy, dunes, ember, black], 1):
        save(draw(), f"wallpaper_{i}.webp")
