"""
Build a 1200x630 Open Graph share image for LF Property Media.

Uses the twilight front-facade photo as the background, darkened with a
gradient, with the LF wordmark + tagline overlaid.

Output: images/og-image.jpg
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "images" / "exterior" / "_DSC0964-twilight.jpg"
OUT = ROOT / "images" / "og-image.jpg"

W, H = 1200, 630

# Brand colors
PAPER = (250, 248, 245)
INK = (26, 26, 26)
SAND = (176, 137, 104)
WHITE = (255, 255, 255)

def find_font(candidates, size):
    """Try a list of font filenames; return the first one that loads."""
    win_fonts = Path("C:/Windows/Fonts")
    for name in candidates:
        p = win_fonts / name
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()

# Open the source photo and cover-crop to 1200x630
src = Image.open(SRC).convert("RGB")
sw, sh = src.size
target_ratio = W / H
src_ratio = sw / sh
if src_ratio > target_ratio:
    # source is wider: crop horizontally
    new_w = int(sh * target_ratio)
    left = (sw - new_w) // 2
    src = src.crop((left, 0, left + new_w, sh))
else:
    # source is taller: crop vertically
    new_h = int(sw / target_ratio)
    top = (sh - new_h) // 2
    src = src.crop((0, top, sw, top + new_h))
bg = src.resize((W, H), Image.LANCZOS)

# Darken with a vertical gradient so text is readable
overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_o = ImageDraw.Draw(overlay)
for y in range(H):
    # Stronger darken at bottom for tagline area, lighter at top
    alpha = int(60 + (y / H) * 140)  # 60 -> 200 across the image
    draw_o.line([(0, y), (W, y)], fill=(0, 0, 0, alpha))
bg = bg.convert("RGBA")
bg.alpha_composite(overlay)
bg = bg.convert("RGB")

draw = ImageDraw.Draw(bg)

# Wordmark "LF." with terracotta period
title_font = find_font(["pala.ttf", "palab.ttf", "georgiab.ttf", "georgia.ttf"], 200)
small_font = find_font(["pala.ttf", "georgia.ttf"], 56)
tag_font = find_font(["arial.ttf"], 30)

# Center "LF" with period after, period in sand
lf_text = "LF"
dot_text = "."
lf_w = draw.textlength(lf_text, font=title_font)
dot_w = draw.textlength(dot_text, font=title_font)
total = lf_w + dot_w
start_x = (W - total) / 2
y_title = H * 0.30
draw.text((start_x, y_title), lf_text, font=title_font, fill=WHITE)
draw.text((start_x + lf_w, y_title), dot_text, font=title_font, fill=SAND)

# Subtitle: "Property Media"
sub = "Property Media"
sub_w = draw.textlength(sub, font=small_font)
draw.text(((W - sub_w) / 2, y_title + 220), sub, font=small_font, fill=WHITE)

# Tagline at bottom
tag = "REAL ESTATE PHOTOGRAPHY  ·  SARASOTA, FLORIDA"
tag_w = draw.textlength(tag, font=tag_font)
draw.text(((W - tag_w) / 2, H - 80), tag, font=tag_font, fill=(220, 210, 200))

# Save as high-quality JPG
bg.save(OUT, "JPEG", quality=88, optimize=True, progressive=True)
print(f"Wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")
