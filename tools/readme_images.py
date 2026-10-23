"""Build the README pictures in docs/ from emulator screenshots, with private regions pixelated.

Screenshots in shots/ are never committed (they show the user's subscription and history); the
docs/ copies blur the source names, subscription URLs and watch history before they go public.

    python -I tools/readme_images.py        # reads shots/readme/*.png, shots/brand-preview.png, shots/wallpapers.png
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SHOTS, DOCS = ROOT / "shots", ROOT / "docs"
OUT_W = 1280


def pixelate(img, box, block=26):
    region = img.crop(box)
    small = region.resize((max(1, region.width // block), max(1, region.height // block)), Image.BILINEAR)
    img.paste(small.resize(region.size, Image.NEAREST), box)


def save(img, name, boxes=(), quality=82):
    img = img.convert("RGB")
    for b in boxes:
        pixelate(img, b)
    img = img.resize((OUT_W, round(img.height * OUT_W / img.width)), Image.LANCZOS)
    DOCS.mkdir(exist_ok=True)
    img.save(DOCS / name, "JPEG", quality=quality, optimize=True)
    print("wrote", name)


def shot(name):
    return Image.open(SHOTS / "readme" / f"{name}.png")


SOURCE_BTN = (140, 50, 560, 135)          # "⌄ <source name>" button on the home screen
HISTORY = (40, 370, 420, 745)             # 最近观看 card + title
DETAIL_SOURCE = (955, 205, 1245, 262)     # "站源: <name>" line on the detail page
SETTING_URLS = [(960, 70, 1620, 150), (960, 200, 1620, 280), (960, 330, 1620, 410)]
SEARCH_HISTORY = (800, 140, 1720, 240)

if __name__ == "__main__":
    pair = Image.new("RGB", (1920 * 2 + 40, 1080), (8, 10, 18))
    OFFICIAL_SOURCE, OFFICIAL_HISTORY = (140, 40, 780, 118), (30, 440, 310, 930)
    for i, (im, boxes) in enumerate(((shot("official-home"), (OFFICIAL_SOURCE, OFFICIAL_HISTORY)), (shot("home"), (SOURCE_BTN, HISTORY)))):
        im = im.convert("RGB")
        for b in boxes:
            pixelate(im, b)
        pair.paste(im, (i * (1920 + 40), 0))
    save(pair, "before-after.jpg", quality=80)
    save(shot("home"), "home.jpg", [SOURCE_BTN, HISTORY])
    save(shot("detail"), "detail.jpg", [DETAIL_SOURCE])
    save(shot("player"), "player.jpg")
    save(shot("live"), "live.jpg")
    save(shot("search"), "search.jpg", [SEARCH_HISTORY])
    save(shot("settings"), "settings.jpg", SETTING_URLS)
    save(Image.open(SHOTS / "brand-preview.png"), "brand.jpg", quality=88)
    save(Image.open(SHOTS / "wallpapers.png"), "wallpapers.jpg", quality=85)
