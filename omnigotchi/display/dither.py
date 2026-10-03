"""DedSec 1-Bit Dithering & Techno-Street Art Graphics Engine.

Implements classic Bayer 4x4 ordered dithering matrices, halftone dot stippling,
glitch scanline distortions, spray-stencil banners, and animated Wrench LED mask goggles
for high-contrast 1-bit monochrome E-Paper rendering.
"""

from typing import Optional, Tuple
from PIL import ImageDraw, ImageFont


# Standard 4x4 Bayer Dithering Matrix (normalized 0..15)
BAYER_4X4 = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5],
]


def draw_dither_rect(
    draw: ImageDraw.ImageDraw,
    bbox: Tuple[int, int, int, int],
    density: float = 0.5,
    invert: bool = False,
):
    """Fills a rectangular region with ordered Bayer matrix dithering."""
    x0, y0, x1, y1 = bbox
    threshold = int(density * 16)

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            bayer_val = BAYER_4X4[y % 4][x % 4]
            is_white = bayer_val < threshold
            if invert:
                is_white = not is_white
            if is_white:
                draw.point((x, y), fill=255)
            else:
                draw.point((x, y), fill=0)


def draw_halftone_strip(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    step: int = 3,
):
    """Draws a pop-art / comic book halftone dot pattern in the given box."""
    for y in range(y0, y1 + 1, step):
        for x in range(x0, x1 + 1, step):
            if (x + y) % (step * 2) == 0:
                draw.point((x, y), fill=255)


def draw_stencil_badge(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.ImageFont,
    inverted: bool = True,
    padding: int = 2,
    corner_cut: bool = True,
):
    """Draws a street-graffiti stencil cutout badge with inverted contrast and optional cut corners."""
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    bx0 = x
    by0 = y
    bx1 = x + tw + (padding * 2) + 2
    by1 = y + th + (padding * 2) + 1

    if inverted:
        # Solid white background box
        draw.rectangle([bx0, by0, bx1, by1], fill=255)
        # Cut top-right and bottom-left corners for brutalist stencil look
        if corner_cut:
            draw.point((bx1, by0), fill=0)
            draw.point((bx1 - 1, by0), fill=0)
            draw.point((bx1, by0 + 1), fill=0)
            draw.point((bx0, by1), fill=0)
            draw.point((bx0 + 1, by1), fill=0)
            draw.point((bx0, by1 - 1), fill=0)
        # Text in pitch black
        draw.text((x + padding + 1, y + padding - bbox[1]), text, font=font, fill=0)
    else:
        # Outlined box with dithered shadow
        draw.rectangle([bx0, by0, bx1, by1], outline=255, fill=0)
        draw.text((x + padding + 1, y + padding - bbox[1]), text, font=font, fill=255)


def draw_glitch_bar(
    draw: ImageDraw.ImageDraw,
    y: int,
    width: int,
    glitch_offset: int = 4,
    step: int = 6,
):
    """Draws an intentional cyber glitch artifact line with segmented gaps."""
    draw.line([(0, y), (width, y)], fill=255, width=1)
    for x in range(glitch_offset, width - 10, step * 4):
        # Create negative glitch punchouts
        draw.line([(x, y), (x + step, y)], fill=0, width=1)
        # Draw floating artifact pixels
        draw.point((x + 2, y - 1), fill=255)
        draw.point((x + 4, y + 1), fill=255)


def draw_wrench_mask(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    expression: str = "X_X",
    mood_tag: str = "WEBPUNK",
    font_mini: Optional[ImageFont.ImageFont] = None,
):
    """Renders Watch Dogs 2 Wrench's iconic digital cyber-goggles with customizable LED expressions."""
    # Outer Goggle Frame (Dual octagonal visor lenses)
    # Left Goggle: cx-34 .. cx-4, Right Goggle: cx+4 .. cx+34 (Lens size: 30x28)
    ly0, ly1 = cy - 14, cy + 14

    # Left Lens
    lx0, lx1 = cx - 35, cx - 5
    draw.rectangle([lx0, ly0, lx1, ly1], outline=255, fill=0)
    # Cut 4 corners for octagonal LED lens look
    draw.line([(lx0, ly0 + 3), (lx0 + 3, ly0)], fill=255)
    draw.point((lx0, ly0), fill=0)
    draw.point((lx1, ly0), fill=0)
    draw.point((lx0, ly1), fill=0)
    draw.point((lx1, ly1), fill=0)

    # Right Lens
    rx0, rx1 = cx + 5, cx + 35
    draw.rectangle([rx0, ly0, rx1, ly1], outline=255, fill=0)
    draw.point((rx0, ly0), fill=0)
    draw.point((rx1, ly0), fill=0)
    draw.point((rx0, ly1), fill=0)
    draw.point((rx1, ly1), fill=0)

    # Bridge connecting goggles with stencil rivets
    draw.line([(lx1, cy), (rx0, cy)], fill=255, width=2)
    draw.line([(lx1, cy - 4), (rx0, cy - 4)], fill=255, width=1)
    draw.line([(lx1, cy + 4), (rx0, cy + 4)], fill=255, width=1)

    # Dithered Halftone shading in the upper rim of lenses
    draw_dither_rect(draw, (lx0 + 2, ly0 + 2, lx1 - 2, ly0 + 5), density=0.25)
    draw_dither_rect(draw, (rx0 + 2, ly0 + 2, rx1 - 2, ly0 + 5), density=0.25)

    # Clean expression parsing
    raw = expression.replace(" ", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "")
    if "_" in raw:
        parts = raw.split("_")
        left_eye = parts[0] if parts[0] else "X"
        right_eye = parts[1] if len(parts) > 1 and parts[1] else left_eye
    elif len(raw) == 2:
        left_eye, right_eye = raw[0], raw[1]
    elif len(raw) >= 3:
        left_eye = raw[0]
        right_eye = raw[-1]
    else:
        left_eye, right_eye = "X", "X"

    def _draw_eye_glyph(gx0: int, gx1: int, eye_char: str):
        ecx = (gx0 + gx1) // 2
        ecy = (ly0 + ly1) // 2

        if eye_char in ("X", "x"):
            draw.line([(ecx - 6, ecy - 6), (ecx + 6, ecy + 6)], fill=255, width=2)
            draw.line([(ecx - 6, ecy + 6), (ecx + 6, ecy - 6)], fill=255, width=2)
        elif eye_char in (">", "<"):
            d = 1 if eye_char == ">" else -1
            draw.line([(ecx - 6 * d, ecy - 6), (ecx + 5 * d, ecy)], fill=255, width=2)
            draw.line([(ecx + 5 * d, ecy), (ecx - 6 * d, ecy + 6)], fill=255, width=2)
        elif eye_char in ("^", "A"):
            draw.line([(ecx - 6, ecy + 4), (ecx, ecy - 5)], fill=255, width=2)
            draw.line([(ecx, ecy - 5), (ecx + 6, ecy + 4)], fill=255, width=2)
        elif eye_char == "*":
            draw.line([(ecx - 6, ecy), (ecx + 6, ecy)], fill=255, width=2)
            draw.line([(ecx, ecy - 6), (ecx, ecy + 6)], fill=255, width=2)
            draw.line([(ecx - 4, ecy - 4), (ecx + 4, ecy + 4)], fill=255, width=1)
            draw.line([(ecx - 4, ecy + 4), (ecx + 4, ecy - 4)], fill=255, width=1)
        elif eye_char == "!":
            draw.line([(ecx, ecy - 6), (ecx, ecy + 2)], fill=255, width=2)
            draw.point((ecx, ecy + 5), fill=255)
            draw.point((ecx, ecy + 6), fill=255)
        elif eye_char == "$":
            draw.line([(ecx - 4, ecy - 5), (ecx + 4, ecy - 5)], fill=255, width=1)
            draw.line([(ecx - 4, ecy - 5), (ecx - 4, ecy)], fill=255, width=1)
            draw.line([(ecx - 4, ecy), (ecx + 4, ecy)], fill=255, width=1)
            draw.line([(ecx + 4, ecy), (ecx + 4, ecy + 5)], fill=255, width=1)
            draw.line([(ecx - 4, ecy + 5), (ecx + 4, ecy + 5)], fill=255, width=1)
            draw.line([(ecx, ecy - 7), (ecx, ecy + 7)], fill=255, width=1)
        elif eye_char in ("O", "o", "0"):
            draw.ellipse([ecx - 6, ecy - 6, ecx + 6, ecy + 6], outline=255, fill=0, width=2)
            draw.point((ecx, ecy), fill=255)
        elif eye_char == "#":
            draw.line([(ecx - 3, ecy - 6), (ecx - 3, ecy + 6)], fill=255, width=1)
            draw.line([(ecx + 3, ecy - 6), (ecx + 3, ecy + 6)], fill=255, width=1)
            draw.line([(ecx - 6, ecy - 3), (ecx + 6, ecy - 3)], fill=255, width=1)
            draw.line([(ecx - 6, ecy + 3), (ecx + 6, ecy + 3)], fill=255, width=1)
        elif eye_char == "-":
            draw.line([(ecx - 6, ecy), (ecx + 6, ecy)], fill=255, width=2)
        elif eye_char == "?":
            draw.arc([ecx - 4, ecy - 6, ecx + 4, ecy], start=180, end=0, fill=255, width=2)
            draw.line([(ecx + 2, ecy - 1), (ecx, ecy + 2)], fill=255, width=2)
            draw.point((ecx, ecy + 5), fill=255)
        else:
            draw.line([(ecx - 6, ecy - 6), (ecx + 6, ecy + 6)], fill=255, width=2)
            draw.line([(ecx - 6, ecy + 6), (ecx + 6, ecy - 6)], fill=255, width=2)

    _draw_eye_glyph(lx0, lx1, left_eye)
    _draw_eye_glyph(rx0, rx1, right_eye)

    # Spike / Stud Rivets below goggles
    for ox in (-25, -15, -5, 5, 15, 25):
        draw.point((cx + ox, ly1 + 3), fill=255)
        draw.point((cx + ox, ly1 + 4), fill=255)
