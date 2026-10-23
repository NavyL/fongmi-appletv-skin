"""Draw the 光影 brand art: launcher icon layers, TV banner, FFalcon home card, in-app logo.

光影 = light and shadow: a white play glyph lit from the top left, a soft glow around it and a
shadow falling to the bottom right, on the skin's navy. Text uses Noto Sans SC (OFL), fetched
into work/fonts by hand (see README).

    python -I tools/gen_brand.py                       # draws the icon itself
    python -I tools/gen_brand.py --source icon.png     # derives everything from a square icon picture instead
    python -I tools/gen_brand.py --preview [--out X]   # also writes shots/brand-preview.png (or X)
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "skin" / "res"
ASSETS = ROOT / "skin" / "assets"
FONT = ROOT / "work" / "fonts" / "NotoSansSC.ttf"
NAME = "光影"
S = 1024  # master size; the adaptive icon canvas is 108 dp, so 1 dp = S / 108 px
SOURCE = None  # a square picture to derive the brand from (--source); None draws the glyph in code


def lerp(a, b, t):
    return a + (b - a) * t


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32)


def background(w, h):
    """Navy with light falling in from the top left."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    u, v = xx / w, yy / h
    t = np.clip((u * 0.45 + v * 0.55), 0, 1)[..., None]
    img = lerp(rgb("#16245E"), rgb("#060A1C"), t)
    d = ((u + 0.05) / 0.75) ** 2 + ((v + 0.10) / 0.70) ** 2
    img = lerp(img, rgb("#3B5BD9"), (0.55 * np.exp(-d))[..., None])
    img += np.random.default_rng(3).uniform(-1.2, 1.2, img.shape)  # dither, no banding
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def triangle(size, cx, cy, r, corner):
    """Rounded play triangle (pointing right) as an L mask."""
    # an equilateral triangle shrunk by the corner radius, grown back by a disc (Minkowski sum)
    big = 4
    m = Image.new("L", (size * big, size * big), 0)
    c = corner * big
    r2 = r * big - 2 * c
    cx, cy = cx * big, cy * big
    pts = [(cx - r2 * 0.5, cy - r2 * 0.866), (cx - r2 * 0.5, cy + r2 * 0.866), (cx + r2, cy)]
    d = ImageDraw.Draw(m)
    d.polygon(pts, fill=255)
    for i in range(3):
        d.line([pts[i], pts[(i + 1) % 3]], fill=255, width=int(2 * c))
    for x, y in pts:
        d.ellipse((x - c, y - c, x + c, y + c), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def source_image(size):
    return SOURCE.convert("RGBA").resize((size, size), Image.LANCZOS)


def source_glyph(size, threshold=170):
    """The bright glyph cut out of the source picture: alpha from luminance, so it floats on any background."""
    img = source_image(size)
    lum = img.convert("L")
    alpha = lum.point(lambda v: 255 if v >= threshold else max(0, int((v - threshold * 0.6) / (threshold * 0.4) * 255)))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, mask=alpha)
    return out, alpha


def foreground(size):
    """Glyph layer on transparent: glow, shadow, lit glyph. Fits the adaptive safe zone (66/108)."""
    if SOURCE is not None:
        # the picture already carries its own glow and shadow; the adaptive background gets the whole
        # picture and this layer stays empty, so launchers do not draw the glyph twice
        return Image.new("RGBA", (size, size), (0, 0, 0, 0)), source_glyph(size)[1]
    cx, cy, r = size * 0.53, size * 0.5, size * 0.205
    glyph = triangle(size, cx, cy, r, size * 0.018)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (size, size), (2, 4, 14, 0))
    shadow.putalpha(glyph.point(lambda a: a * 0.7))
    shadow = shadow.transform((size, size), Image.AFFINE, (1, 0, -size * 0.035, 0, 1, -size * 0.045))
    out.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(size * 0.03)))
    glow = Image.new("RGBA", (size, size), (150, 185, 255, 0))
    glow.putalpha(glyph.point(lambda a: a * 0.55))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(size * 0.06)))
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    t = np.clip(((xx - (cx - r)) + (yy - (cy - r))) / (3.2 * r), 0, 1)[..., None]
    lit = lerp(rgb("#FFFFFF"), rgb("#C9D6FF"), t)
    face = Image.fromarray(np.clip(lit, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    face.putalpha(glyph)
    out.alpha_composite(face)
    return out, glyph


def squircle_mask(size, radius_frac=0.225):
    big = 4
    m = Image.new("L", (size * big, size * big), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size * big - 1, size * big - 1), radius=int(size * big * radius_frac), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def full_icon(size):
    icon = source_image(size) if SOURCE is not None else background(size, size)
    fg, _ = foreground(size)
    icon.alpha_composite(fg)
    # a fine light rim, brighter at the top left, so the tile reads on navy surroundings
    rim = Image.new("L", (size, size), 0)
    w = max(1, size // 160)
    ImageDraw.Draw(rim).rounded_rectangle((w, w, size - 1 - w, size - 1 - w), radius=int(size * 0.215), outline=255, width=w)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    fade = np.clip(1.1 - (xx + yy) / (2 * size), 0.25, 1.0)
    rim = Image.fromarray((np.asarray(rim, np.float32) * fade * 0.35).astype(np.uint8), "L")
    light = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    light.putalpha(rim)
    icon.alpha_composite(light)
    icon.putalpha(squircle_mask(size))
    return icon


def drop_shadow(img, s, x, y):
    """Soft shadow under a squircle tile, on a padded layer so the blur is never cut square."""
    pad = int(s * 0.3)
    sh = Image.new("RGBA", (s + 2 * pad, s + 2 * pad), (0, 0, 0, 0))
    mask = Image.new("L", sh.size, 0)
    mask.paste(squircle_mask(s).point(lambda a: a * 0.5), (pad, pad))
    sh.putalpha(mask)
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(s * 0.07)), (x - pad, y - pad + int(s * 0.05)))


def text_layer(w, h, text, px, weight, fill=(255, 255, 255, 255)):
    font = ImageFont.truetype(str(FONT), px)
    font.set_variation_by_axes([weight])
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((0, 0), text, font=font, fill=fill)
    return layer.crop(layer.getbbox())


def banner(w, h):
    """TV banner (320x180 dp): icon at the left, name at the right."""
    img = background(w, h)
    s = int(h * 0.56)
    icon = full_icon(s)
    x, y = int(w * 0.11), (h - s) // 2
    drop_shadow(img, s, x, y)
    img.alpha_composite(icon, (x, y))
    t = text_layer(w, h, NAME, int(h * 0.30), 600)
    img.alpha_composite(t, (x + s + int(w * 0.07), (h - t.height) // 2))
    return img


def card(w, h):
    """FFalcon cyberui full card (700x450 asset): icon above the name, centred."""
    img = background(w, h)
    s = int(h * 0.42)
    icon = full_icon(s)
    t = text_layer(w, h, NAME, int(h * 0.15), 600)
    gap = int(h * 0.06)
    top = (h - (s + gap + t.height)) // 2
    drop_shadow(img, s, (w - s) // 2, top)
    img.alpha_composite(icon, ((w - s) // 2, top))
    img.alpha_composite(t, ((w - t.width) // 2, top + s + gap))
    return img.convert("RGB")


def write(img, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    print("wrote", path.relative_to(ROOT) if path.is_absolute() else path)


def xml(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('<?xml version="1.0" encoding="utf-8"?>\n<!-- GENERATED by tools/gen_brand.py -->\n' + body + "\n", encoding="utf-8")
    print("wrote", path.relative_to(ROOT) if path.is_absolute() else path)


def main():
    global SOURCE
    args = sys.argv[1:]
    if "--source" in args:
        SOURCE = Image.open(args[args.index("--source") + 1]).convert("RGBA")
        if SOURCE.width != SOURCE.height:
            raise SystemExit("--source must be a square picture")
    NS = 'xmlns:android="http://schemas.android.com/apk/res/android"'
    # adaptive launcher icon: 108 dp layers at xxxhdpi (432 px)
    write(source_image(432) if SOURCE is not None else background(432, 432), RES / "drawable-nodpi" / "gy_icon_bg.png")
    fg, glyph = foreground(432)
    write(fg, RES / "drawable-nodpi" / "gy_icon_fg.png")
    mono = Image.new("RGBA", (432, 432), (255, 255, 255, 0))
    mono.putalpha(glyph)
    write(mono, RES / "drawable-nodpi" / "gy_icon_mono.png")
    for name in ("ic_launcher", "ic_launcher_round"):
        xml(RES / "mipmap-anydpi-v26" / f"{name}.xml",
            f'<adaptive-icon {NS}>\n    <background android:drawable="@drawable/gy_icon_bg" />\n'
            f'    <foreground android:drawable="@drawable/gy_icon_fg" />\n    <monochrome android:drawable="@drawable/gy_icon_mono" />\n</adaptive-icon>')
    # legacy launcher bitmaps (pre-API 26 launchers, some vendor launchers)
    for dpi, px in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        ic = full_icon(px * 4).resize((px, px), Image.LANCZOS)
        write(ic, RES / f"mipmap-{dpi}" / "ic_launcher.png")
        write(ic, RES / f"mipmap-{dpi}" / "ic_launcher_round.png")
    # splash (Android 12+ uses the animated one, older the plain foreground) and the in-app fallback logo
    splash = "gy_icon_fg"
    if SOURCE is not None:  # the glyph alone, floating on the navy splash background
        write(source_glyph(432)[0], RES / "drawable-nodpi" / "gy_splash_glyph.png")
        splash = "gy_splash_glyph"
    for path in (RES / "drawable" / "ic_launcher_foreground.xml", RES / "drawable-v31" / "ic_splash_logo_animated.xml"):
        xml(path, f'<bitmap {NS} android:src="@drawable/{splash}" android:gravity="fill" />')
    write(full_icon(512), RES / "drawable-nodpi" / "ic_logo.png")
    # TV banner 320x180 dp, drawn at 4x
    write(banner(1280, 720), RES / "drawable-nodpi" / "gy_banner.png")
    xml(RES / "mipmap-anydpi-v26" / "ic_banner.xml", f'<bitmap {NS} android:src="@drawable/gy_banner" android:gravity="fill" />')
    # FFalcon cyberui home card (activity meta-data beidouui_icon -> assets/card_guangying.png)
    write(card(700, 450), ASSETS / "card_guangying.png")
    if "--preview" in sys.argv:
        prev = Image.new("RGB", (1460, 520), (12, 14, 22))
        prev.paste(full_icon(400), (30, 60), full_icon(400))
        prev.paste(banner(640, 360).convert("RGB"), (460, 20))
        c = card(700, 450).resize((350, 225))
        prev.paste(c, (1100, 20))
        rows = Image.new("RGB", (1460, 760), (12, 14, 22))
        rows.paste(prev, (0, 0))
        launcher = background(1460, 240).convert("RGB")
        for i, s in enumerate((96, 144, 192)):
            ic = full_icon(s)
            launcher.paste(ic, (60 + i * 260, (240 - s) // 2), ic)
        rows.paste(launcher, (0, 520))
        out = Path(sys.argv[sys.argv.index("--out") + 1]).resolve() if "--out" in sys.argv else ROOT / "shots" / "brand-preview.png"
        write(rows, out)


if __name__ == "__main__":
    main()
