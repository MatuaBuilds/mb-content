"""Render V1 Terracotta carousels (F01 Truth List) from a batch JSON.

Usage: python3 farm/tools/render_v1.py farm/batches/<batch>.json
Writes <repo>/<slug>/slide01.jpg ... Wrap *text* for italic.
"""
import json, os, random, re, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
FONTS = "/usr/share/fonts/truetype/liberation/"
BOLD = ImageFont.truetype(FONTS + "LiberationSerif-Bold.ttf", 64)
ITAL = ImageFont.truetype(FONTS + "LiberationSerif-BoldItalic.ttf", 64)
LABEL = ImageFont.truetype(FONTS + "LiberationSerif-Bold.ttf", 22)
PILL = ImageFont.truetype(FONTS + "LiberationSerif-Bold.ttf", 28)
TEXT = (244, 206, 184)
LABEL_C = (236, 196, 172)
CENTRE, EDGE = (158, 93, 55), (137, 81, 48)
MAX_W, LINE_H, BLOCK_CY = 900, 84, 1030


def background():
    im = Image.new("RGB", (W, H))
    px = im.load()
    cx, cy, r = W / 2, H * 0.45, (W**2 + H**2) ** 0.5 / 2
    rnd = random.Random(7)
    for y in range(H):
        for x in range(W):
            t = min(1, ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r) ** 1.4
            n = rnd.randint(-2, 2)
            px[x, y] = tuple(int(c + (e - c) * t) + n for c, e in zip(CENTRE, EDGE))
    return im


def tokens(text):
    out = []
    for i, part in enumerate(re.split(r"\*", text)):
        for w in part.split():
            out.append((w, i % 2 == 1))
    return out


def wrap(text, draw):
    lines, cur = [], []
    for tok in tokens(text):
        trial = cur + [tok]
        if cur and line_width(trial, draw) > MAX_W:
            lines.append(cur)
            cur = [tok]
        else:
            cur = trial
    lines.append(cur)
    return lines


def line_width(line, draw):
    space = draw.textlength(" ", font=BOLD)
    return sum(draw.textlength(w, font=ITAL if it else BOLD) for w, it in line) + space * (len(line) - 1)


def slide(bg, text, n, total):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    lines = wrap(text, d)
    top = BLOCK_CY - (len(lines) * LINE_H) / 2
    space = d.textlength(" ", font=BOLD)
    for i, line in enumerate(lines):
        x = (W - line_width(line, d)) / 2
        y = top + i * LINE_H
        for w, it in line:
            f = ITAL if it else BOLD
            d.text((x, y), w, font=f, fill=TEXT)
            x += d.textlength(w, font=f) + space
    label, y = "MATUA BILL", top + len(lines) * LINE_H + 28
    lw = sum(d.textlength(c, font=LABEL) + 3 for c in label) - 3
    x = (W - lw) / 2
    for c in label:
        d.text((x, y), c, font=LABEL, fill=LABEL_C)
        x += d.textlength(c, font=LABEL) + 3
    tag = f"{n}/{total}"
    tw = d.textlength(tag, font=PILL)
    pw = tw + 40
    d.rounded_rectangle((1030 - pw, 48, 1030, 92), radius=22, fill=(62, 38, 20))
    d.text((1030 - pw / 2, 70), tag, font=PILL, fill=(240, 214, 196), anchor="mm")
    return im


def main(path):
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(path))))
    bg = background()
    for c in json.load(open(path)):
        out = os.path.join(repo, c["slug"])
        os.makedirs(out, exist_ok=True)
        for i, t in enumerate(c["slides"], 1):
            slide(bg, t, i, len(c["slides"])).save(os.path.join(out, f"slide{i:02d}.jpg"), quality=90)
        print(c["slug"])


if __name__ == "__main__":
    main(sys.argv[1])
