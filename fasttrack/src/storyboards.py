"""Render branded 9:16 FastTrack storyboard cards for human review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH = 1080
HEIGHT = 1920


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size=size)
    return ImageFont.load_default(size=size)


def _gradient(start: tuple[int, int, int], end: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), start)
    pixels = image.load()
    for y in range(HEIGHT):
        ratio = y / (HEIGHT - 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
        for x in range(WIDTH):
            pixels[x, y] = color
    return image


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        box = draw.textbbox((0, 0), candidate, font=font)
        if box[2] - box[0] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    width: int,
    spacing: int,
    max_lines: int | None = None,
) -> int:
    lines = _wrap(draw, text, font, width)
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    x, y = xy
    line_height = draw.textbbox((0, 0), "Ag", font=font)[3] + spacing
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def render_storyboard(record: dict, destination: Path) -> Path:
    brand = json.loads((ROOT / "config" / "brand.json").read_text(encoding="utf-8"))
    palette = brand["palette"]
    primary = _hex(palette["primary"])
    secondary = _hex(palette["secondary"])
    water = _hex(palette["water"])
    background = _hex(palette["dark_background"])
    card = _hex(palette["dark_card"])
    white = (248, 248, 252)
    muted = (175, 177, 196)

    image = _gradient(background, card)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((70, 64, 1010, 144), radius=40, fill=(26, 26, 46))
    draw.text((108, 82), "FASTTRACK", font=_font(30, bold=True), fill=white)
    label = f"{record['asset_id']}  •  {record['series'].upper()}"
    label_box = draw.textbbox((0, 0), label, font=_font(23))
    draw.text((970 - (label_box[2] - label_box[0]), 89), label, font=_font(23), fill=muted)

    ring = (270, 200, 810, 740)
    draw.ellipse(ring, outline=(54, 55, 78), width=34)
    draw.arc(ring, start=-90, end=208, fill=primary, width=34)
    draw.arc((306, 236, 774, 704), start=-90, end=145, fill=secondary, width=10)
    draw.ellipse((500, 450, 580, 530), fill=water)
    center = "16:8" if record["series"] != "beginner" else "12:12"
    center_font = _font(86, bold=True)
    center_box = draw.textbbox((0, 0), center, font=center_font)
    draw.text(
        ((WIDTH - (center_box[2] - center_box[0])) / 2, 350),
        center,
        font=center_font,
        fill=white,
    )
    subtitle = "FASTING RHYTHM" if record["locale"] == "en" else "ORUÇ RİTMİ"
    sub_font = _font(26, bold=True)
    sub_box = draw.textbbox((0, 0), subtitle, font=sub_font)
    draw.text(
        ((WIDTH - (sub_box[2] - sub_box[0])) / 2, 555),
        subtitle,
        font=sub_font,
        fill=muted,
    )

    _draw_wrapped(
        draw,
        record["hook"],
        xy=(84, 795),
        font=_font(66, bold=True),
        fill=white,
        width=912,
        spacing=16,
        max_lines=4,
    )

    draw.rounded_rectangle((70, 1110, 1010, 1570), radius=44, fill=(27, 30, 55))
    draw.rounded_rectangle((102, 1147, 116, 1507), radius=7, fill=water)
    _draw_wrapped(
        draw,
        record["script"],
        xy=(154, 1160),
        font=_font(36),
        fill=(229, 230, 239),
        width=795,
        spacing=18,
        max_lines=8,
    )

    draw.rounded_rectangle((70, 1614, 1010, 1770), radius=48, fill=primary)
    _draw_wrapped(
        draw,
        record["cta"],
        xy=(118, 1650),
        font=_font(37, bold=True),
        fill=white,
        width=844,
        spacing=10,
        max_lines=2,
    )

    _draw_wrapped(
        draw,
        record["safety_note"],
        xy=(84, 1810),
        font=_font(21),
        fill=muted,
        width=912,
        spacing=6,
        max_lines=2,
    )

    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return destination


def render_storyboards(records: list[dict], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return [
        render_storyboard(record, output_dir / f"{record['asset_id']}.png")
        for record in records
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.pack.read_text(encoding="utf-8"))
    paths = render_storyboards(payload["records"], args.output)
    print(f"Rendered {len(paths)} storyboards in {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
