"""Mock-ups of a tvOS sidebar home (Yingxia's structure) using the skin's wallpaper, fonts and posters.

    python -I tools/mock_sidebar.py   -> shots/mock-sidebar-collapsed.png, shots/mock-sidebar-open.png
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
CJK = ROOT / "work" / "fonts" / "NotoSansSC.ttf"
INTER = ROOT / "skin" / "res" / "font" / "tvos_display_300.ttf"
W, H = 1920, 1080
NAVY, CONTROL, RAISED = (5, 9, 23), (23, 32, 56), (33, 45, 74)


def font(px, weight=500):
    f = ImageFont.truetype(str(CJK), px)
    f.set_variation_by_axes([weight])
    return f


def wallpaper():
    bg = Image.open(ROOT / "skin/res/drawable-nodpi/wallpaper_1.webp").convert("RGBA").resize((W, H))
    scrim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(scrim)
    for y in range(H):
        a = int(115 - 65 * y / H)
        d.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    bg.alpha_composite(scrim)
    return bg


def posters():
    src = Image.open(ROOT / "shots/p3/11-vod-tab.png").convert("RGB")
    xs = [48, 418, 790, 1160, 1532]
    return [src.crop((x, 148, x + 340, 600)).resize((294, 441), Image.LANCZOS) for x in xs]


TITLES = ["醉梦", "小城良方", "嫁金钗", "赛博朋克：边缘行者", "兰香如故"]
BADGES = ["评分 8.1", "更新至04集", "更新至12集", "全10集", "更新至20集"]


def pill(d, x, y, text, f, fill, color, pad=22, h=58, icon=None):
    tw = d.textlength(text, font=f) + (34 if icon else 0)
    if len(fill) == 4 and fill[3] < 255:  # translucent: draw on a layer so alpha composites
        layer = Image.new("RGBA", d._image.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle((x, y, x + tw + 2 * pad, y + h), radius=h // 2, fill=fill)
        d._image.alpha_composite(layer)
    else:
        d.rounded_rectangle((x, y, x + tw + 2 * pad, y + h), radius=h // 2, fill=fill)
    tx = x + pad
    if icon:
        icon(d, tx, y + h // 2, color)
        tx += 34
    d.text((tx, y + h / 2), text, font=f, fill=color, anchor="lm")
    return x + tw + 2 * pad


def play_glyph(d, x, cy, color):
    d.polygon([(x + 2, cy - 11), (x + 2, cy + 11), (x + 22, cy)], fill=color)


def chevron_left(d, x, cy, color):
    d.line([(x + 14, cy - 10), (x + 4, cy), (x + 14, cy + 10)], fill=color, width=4, joint="curve")


def chevron_down(d, x, cy, color):
    d.line([(x + 2, cy - 5), (x + 12, cy + 5), (x + 22, cy - 5)], fill=color, width=4, joint="curve")


def home_content(img, left=144, dim=False):
    d = ImageDraw.Draw(img)
    f26, f29, f23 = font(26, 600), font(29, 600), font(23, 600)
    # row 1: collapsed sidebar pill + clock
    pill(d, 80, 50, "立即观看", f26, (255, 255, 255, 46), (255, 255, 255), icon=lambda d, x, cy, c: (chevron_left(d, x - 6, cy, c), play_glyph(d, x + 14, cy, c)))
    d.text((W - 80, 79), "19:01", font=ImageFont.truetype(str(INTER), 44), fill=(255, 255, 255, 220), anchor="rm")
    # row 2: source button + refresh
    pill(d, left, 140, "豆豆 | 片单", f26, CONTROL, (255, 255, 255), icon=chevron_down)
    d.rounded_rectangle((W - left - 58, 140, W - left, 198), radius=14, fill=CONTROL)
    cx, cy = W - left - 29, 169
    d.arc((cx - 13, cy - 13, cx + 13, cy + 13), 300, 240, fill=(255, 255, 255), width=4)
    d.polygon([(cx + 6, cy - 18), (cx + 16, cy - 8), (cx + 4, cy - 4)], fill=(255, 255, 255))
    # row 3: category chips
    x = left
    for i, t in enumerate(["推荐", "电影", "国产剧", "动漫", "短剧", "综艺", "海外剧"]):
        fill, col = ((235, 235, 235), (15, 15, 15)) if i == 0 else (CONTROL, (255, 255, 255))
        x = pill(d, x, 224, ("✓ " if i == 0 else "") + t, f26, fill, col) + 8
    # grid
    y0 = 322
    for i, p in enumerate(posters()):
        x = left + i * (294 + 40)
        focused = i == 1
        if focused:
            plate = Image.new("RGBA", (294 + 28, 441 + 28), (0, 0, 0, 0))
            ImageDraw.Draw(plate).rounded_rectangle((0, 0, 293 + 28, 440 + 28), radius=24, fill=RAISED + (255,), outline=(255, 255, 255), width=3)
            sh = Image.new("RGBA", (294 + 80, 441 + 80), (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle((26, 36, 294 + 54, 441 + 64), radius=24, fill=(0, 0, 0, 110))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (x - 40, y0 - 40))
            img.alpha_composite(plate, (x - 14, y0 - 14))
        tile = p.convert("RGBA")
        m = Image.new("L", tile.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, 293, 440), radius=10, fill=255)
        tile.putalpha(m)
        img.alpha_composite(tile, (x, y0))
        d = ImageDraw.Draw(img)
        bw = d.textlength(BADGES[i], font=f23) + 12
        d.rounded_rectangle((x + 8, y0 + 441 - 8 - 32, x + 8 + bw, y0 + 441 - 8), radius=16, fill=(0, 0, 0, 115))
        d.text((x + 14, y0 + 441 - 8 - 16), BADGES[i], font=f23, fill=(255, 255, 255), anchor="lm")
        d.text((x, y0 + 441 + 10), TITLES[i], font=f29, fill=(255, 255, 255) if focused else (255, 255, 255, 166))
    # second row peeking
    for i, p in enumerate(posters()[::-1]):
        x = left + i * (294 + 40)
        tile = p.convert("RGBA").crop((0, 0, 294, H - (y0 + 441 + 48 + 48)))
        m = Image.new("L", tile.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, 293, 440), radius=10, fill=255)
        tile.putalpha(m)
        img.alpha_composite(tile, (x, y0 + 441 + 48 + 48))
    if dim:
        img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))


def collapsed():
    img = wallpaper()
    home_content(img)
    return img


def opened():
    img = wallpaper()
    home_content(img, dim=True)
    img = img.filter(ImageFilter.GaussianBlur(6))
    panel = Image.new("RGBA", (520, H), (19, 27, 48, 236))
    img.alpha_composite(panel, (0, 0))
    d = ImageDraw.Draw(img)
    icon = Image.open(ROOT / "skin/res/drawable-nodpi/ic_logo.png").convert("RGBA").resize((72, 72), Image.LANCZOS)
    img.alpha_composite(icon, (64, 52))
    d.text((152, 88), "光影", font=font(32, 600), fill=(255, 255, 255), anchor="lm")
    items = ["立即观看", "直播", "搜索", "收藏", "连接", "设置"]
    y = 190
    for i, t in enumerate(items):
        focused = i == 0
        if focused:
            d.rounded_rectangle((48, y, 472, y + 72), radius=36, fill=(255, 255, 255))
        d.text((88, y + 36), t, font=font(29, 600), fill=(0, 0, 0) if focused else (255, 255, 255), anchor="lm")
        y += 72 + 12
    d.text((88, H - 60), "按 ‹ 返回键收起", font=font(21, 500), fill=(255, 255, 255, 120), anchor="lm")
    return img


if __name__ == "__main__":
    collapsed().convert("RGB").save(ROOT / "shots/mock-sidebar-collapsed.png")
    opened().convert("RGB").save(ROOT / "shots/mock-sidebar-open.png")
    print("ok")
