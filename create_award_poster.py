"""Generate a celebratory 2026 MDRT award poster.

This script creates a watermark-free "喜报" style poster using the local
portrait in ``images/personal.jpg`` and exports it to
``images/xibao_2026_mdrt.png``.
"""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Final

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT: Final[Path] = Path(__file__).resolve().parent
DEFAULT_SOURCE_IMAGE: Final[Path] = ROOT / "images" / "personal.jpg"
DEFAULT_OUTPUT_IMAGE: Final[Path] = ROOT / "images" / "xibao_2026_mdrt.png"

CANVAS_WIDTH: Final[int] = 1242
CANVAS_HEIGHT: Final[int] = 2208

CHINESE_FONT: Final[Path] = Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")
ENGLISH_FONT: Final[Path] = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def load_font(font_path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font with graceful fallback.

    Args:
        font_path: Target font path on disk.
        size: Font size in pixels.

    Returns:
        A PIL font object.
    """
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def draw_vertical_gradient(width: int, height: int) -> Image.Image:
    """Create a red vertical gradient background.

    Args:
        width: Output image width.
        height: Output image height.

    Returns:
        RGB gradient image.
    """
    top_color = (173, 18, 22)
    mid_color = (136, 10, 14)
    bottom_color = (98, 6, 10)

    gradient = Image.new("RGB", (1, height))
    pixel = gradient.load()
    for y in range(height):
        ratio = y / (height - 1)
        if ratio < 0.45:
            r = ratio / 0.45
            color = tuple(
                int(top_color[i] * (1.0 - r) + mid_color[i] * r) for i in range(3)
            )
        else:
            r = (ratio - 0.45) / 0.55
            color = tuple(
                int(mid_color[i] * (1.0 - r) + bottom_color[i] * r) for i in range(3)
            )
        pixel[0, y] = color
    return gradient.resize((width, height))


def add_light_rays(canvas: Image.Image) -> None:
    """Draw subtle golden rays for celebratory atmosphere.

    Args:
        canvas: RGBA canvas to draw on.
    """
    ray_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(ray_layer)
    origin_x = CANVAS_WIDTH // 2
    origin_y = int(CANVAS_HEIGHT * 0.10)

    for angle_deg in range(-65, 66, 3):
        angle = math.radians(angle_deg)
        length = CANVAS_HEIGHT * 1.4
        end_x = int(origin_x + math.sin(angle) * length)
        end_y = int(origin_y + math.cos(angle) * length)
        alpha = 34 if angle_deg % 2 == 0 else 20
        draw.line(
            [(origin_x, origin_y), (end_x, end_y)],
            fill=(255, 214, 120, alpha),
            width=2,
        )

    ray_layer = ray_layer.filter(ImageFilter.GaussianBlur(1.8))
    canvas.alpha_composite(ray_layer)


def add_confetti(canvas: Image.Image, seed: int = 2026) -> None:
    """Scatter decorative confetti dots in the upper area.

    Args:
        canvas: Target RGBA canvas.
        seed: Random seed for deterministic output.
    """
    random.seed(seed)
    confetti = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(confetti)
    colors = [
        (255, 224, 130, 190),
        (255, 205, 85, 180),
        (255, 241, 195, 150),
        (255, 245, 225, 130),
    ]

    for _ in range(140):
        x = random.randint(40, CANVAS_WIDTH - 40)
        y = random.randint(80, int(CANVAS_HEIGHT * 0.56))
        radius = random.randint(2, 7)
        color = random.choice(colors)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    confetti = confetti.filter(ImageFilter.GaussianBlur(0.4))
    canvas.alpha_composite(confetti)


def rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    """Build an L-mode rounded mask.

    Args:
        size: Mask size.
        radius: Corner radius.

    Returns:
        L mask image.
    """
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size[0], size[1]), radius=radius, fill=255)
    return mask


def build_photo_card(source_image: Path) -> Image.Image:
    """Create framed portrait card from source image.

    Returns:
        RGBA card image with golden border and rounded portrait.
    """
    if not source_image.exists():
        raise FileNotFoundError(f"Source image not found: {source_image}")

    card_w, card_h = 760, 1120
    frame = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)

    # Outer gold frame.
    draw.rounded_rectangle(
        (0, 0, card_w - 1, card_h - 1),
        radius=56,
        fill=(183, 133, 56, 255),
    )
    draw.rounded_rectangle(
        (10, 10, card_w - 11, card_h - 11),
        radius=50,
        fill=(232, 212, 165, 255),
    )
    draw.rounded_rectangle(
        (24, 24, card_w - 25, card_h - 25),
        radius=42,
        fill=(255, 255, 255, 255),
    )

    src = Image.open(source_image).convert("RGB")
    portrait = ImageOps.fit(src, (card_w - 56, card_h - 56), centering=(0.5, 0.25))
    portrait = portrait.convert("RGBA")
    mask = rounded_mask(portrait.size, radius=34)
    frame.paste(portrait, (28, 28), mask)

    return frame


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    stroke_fill: tuple[int, int, int, int] | None = None,
    stroke_width: int = 0,
) -> None:
    """Draw text horizontally centered at a target x-coordinate."""
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    draw.text(
        (center_x - text_w / 2, y),
        text,
        font=font,
        fill=fill,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )


def create_poster(source_image: Path, output_image: Path, display_name: str) -> None:
    """Generate and save the final award poster.

    Args:
        source_image: Input portrait file path.
        output_image: Output poster file path.
        display_name: Name shown on the name ribbon.
    """
    bg = draw_vertical_gradient(CANVAS_WIDTH, CANVAS_HEIGHT).convert("RGBA")

    # Top glow.
    glow = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse(
        (-180, -300, CANVAS_WIDTH + 180, 740),
        fill=(255, 215, 128, 76),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(36))
    bg.alpha_composite(glow)

    add_light_rays(bg)
    add_confetti(bg)

    draw = ImageDraw.Draw(bg)
    title_font = load_font(CHINESE_FONT, 168)
    subtitle_font = load_font(CHINESE_FONT, 58)
    headline_font = load_font(CHINESE_FONT, 76)
    body_font = load_font(CHINESE_FONT, 54)
    english_name_font = load_font(ENGLISH_FONT, 84)
    en_small_font = load_font(ENGLISH_FONT, 38)

    draw_centered_text(
        draw=draw,
        text="喜 报",
        center_x=CANVAS_WIDTH // 2,
        y=130,
        font=title_font,
        fill=(255, 236, 170, 255),
        stroke_fill=(121, 18, 18, 255),
        stroke_width=5,
    )
    draw_centered_text(
        draw=draw,
        text="热烈祝贺 荣耀绽放",
        center_x=CANVAS_WIDTH // 2,
        y=328,
        font=subtitle_font,
        fill=(255, 225, 150, 255),
    )
    draw_centered_text(
        draw=draw,
        text="2026 MDRT 荣誉达成",
        center_x=CANVAS_WIDTH // 2,
        y=412,
        font=headline_font,
        fill=(255, 248, 225, 255),
        stroke_fill=(126, 27, 16, 255),
        stroke_width=2,
    )

    photo_card = build_photo_card(source_image=source_image)

    # Drop shadow under photo card.
    shadow = Image.new("RGBA", photo_card.size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        (12, 18, photo_card.size[0] - 2, photo_card.size[1] - 2),
        radius=58,
        fill=(22, 6, 6, 130),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))

    card_x = (CANVAS_WIDTH - photo_card.size[0]) // 2
    card_y = 530
    bg.alpha_composite(shadow, (card_x, card_y + 10))
    bg.alpha_composite(photo_card, (card_x, card_y))

    # Name ribbon.
    ribbon_w, ribbon_h = 610, 116
    ribbon = Image.new("RGBA", (ribbon_w, ribbon_h), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(ribbon)
    rdraw.rounded_rectangle(
        (0, 0, ribbon_w - 1, ribbon_h - 1),
        radius=28,
        fill=(152, 26, 24, 255),
        outline=(245, 204, 114, 255),
        width=5,
    )
    name_bbox = rdraw.textbbox((0, 0), display_name, font=english_name_font)
    name_w = name_bbox[2] - name_bbox[0]
    rdraw.text(
        ((ribbon_w - name_w) / 2, 13),
        display_name,
        font=english_name_font,
        fill=(255, 240, 195, 255),
    )
    ribbon_x = (CANVAS_WIDTH - ribbon_w) // 2
    ribbon_y = card_y + photo_card.size[1] - 28
    bg.alpha_composite(ribbon, (ribbon_x, ribbon_y))

    draw_centered_text(
        draw=draw,
        text="荣 获 2 0 2 6  M D R T",
        center_x=CANVAS_WIDTH // 2,
        y=ribbon_y + 170,
        font=load_font(CHINESE_FONT, 88),
        fill=(255, 221, 130, 255),
    )
    draw_centered_text(
        draw=draw,
        text="MILLION DOLLAR ROUND TABLE",
        center_x=CANVAS_WIDTH // 2,
        y=ribbon_y + 282,
        font=en_small_font,
        fill=(255, 221, 152, 240),
    )
    draw_centered_text(
        draw=draw,
        text="专 业 · 坚 持 · 卓 越",
        center_x=CANVAS_WIDTH // 2,
        y=ribbon_y + 352,
        font=load_font(CHINESE_FONT, 50),
        fill=(255, 240, 200, 240),
    )

    output_image.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(output_image, format="PNG", optimize=True)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for poster generation.

    Returns:
        Parsed command namespace.
    """
    parser = argparse.ArgumentParser(description="Generate a 2026 MDRT xibao poster.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_SOURCE_IMAGE,
        help="Input portrait image path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_IMAGE,
        help="Output poster image path.",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="XIA LING",
        help="Display name to print on poster.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    create_poster(
        source_image=args.input,
        output_image=args.output,
        display_name=args.name.strip() or "XIA LING",
    )
    print(f"Poster generated: {args.output}")
