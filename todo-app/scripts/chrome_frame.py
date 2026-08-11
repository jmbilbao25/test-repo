"""Wraps a page screenshot in a browser window frame.

The screenshot itself is untouched. This only draws the window bar and the
address bar around it, so a reader can see what the app looked like and where it
was being served from.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SANS = "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf"

BAR_H = 56          # logical pixels
PAD = 14            # gap between the window and the image edge
RADIUS = 9
BACKDROP = (201, 207, 219)
BAR_BG = (228, 231, 238)
BAR_LINE = (205, 210, 221)
PILL_BG = (255, 255, 255)
PILL_LINE = (211, 216, 226)
URL_INK = (74, 81, 99)
DOTS = [(255, 95, 87), (254, 188, 46), (40, 200, 64)]


def _rounded_mask(size, radius) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return mask


def add_chrome(shot_path: str, out_path: str, url: str, scale: int = 2) -> None:
    """shot_path is a screenshot of the page; out_path gets the framed version."""
    body = Image.open(shot_path).convert("RGB")
    w = body.width
    bar_h = BAR_H * scale
    pad = PAD * scale
    radius = RADIUS * scale

    # The window: address bar on top, the real screenshot underneath.
    win = Image.new("RGB", (w, bar_h + body.height), BAR_BG)
    draw = ImageDraw.Draw(win)
    draw.line([(0, bar_h - scale), (w, bar_h - scale)], fill=BAR_LINE,
              width=scale)

    cx = 24 * scale
    r = 5.5 * scale
    for colour in DOTS:
        draw.ellipse([cx - r, bar_h / 2 - r, cx + r, bar_h / 2 + r], fill=colour)
        cx += 21 * scale

    pill = [cx + 4 * scale, bar_h / 2 - 13 * scale,
            w - 24 * scale, bar_h / 2 + 13 * scale]
    draw.rounded_rectangle(pill, radius=13 * scale, fill=PILL_BG,
                           outline=PILL_LINE, width=scale)
    font = ImageFont.truetype(SANS, 12 * scale)
    draw.text((pill[0] + 12 * scale, bar_h / 2), url, font=font, fill=URL_INK,
              anchor="lm")

    win.paste(body, (0, bar_h))
    win.putalpha(_rounded_mask(win.size, radius))

    # Drop it on a backdrop with a soft shadow.
    canvas = Image.new("RGB", (w + pad * 2, win.height + pad * 2), BACKDROP)
    shadow = Image.new("L", canvas.size, 0)
    ImageDraw.Draw(shadow).rounded_rectangle(
        [pad, pad + 3 * scale, pad + w, pad + win.height + 3 * scale],
        radius=radius, fill=90)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6 * scale))
    canvas.paste(Image.new("RGB", canvas.size, (20, 24, 35)), (0, 0), shadow)
    canvas.paste(win, (pad, pad), win)
    canvas.save(out_path)
