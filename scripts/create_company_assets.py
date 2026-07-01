"""Generate logo and favicon PNG assets for seed companies."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

STATIC_ROOT = Path(__file__).resolve().parent.parent / "static" / "companies"

COMPANIES = [
    {
        "slug": "ahsoftech",
        "display": "AHSoftech",
        "primary": (30, 64, 175),
        "accent": (59, 130, 246),
        "bg": (239, 246, 255),
    },
    {
        "slug": "beela",
        "display": "Beela",
        "primary": (124, 58, 237),
        "accent": (167, 139, 250),
        "bg": (245, 243, 255),
    },
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def create_logo(slug: str, display: str, primary: tuple, accent: tuple, bg: tuple) -> Path:
    size = (400, 120)
    image = Image.new("RGBA", size, bg + (255,))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((16, 16, 104, 104), radius=20, fill=primary)
    draw.rounded_rectangle((28, 28, 92, 92), radius=14, fill=accent)

    initial = display[0].upper()
    font = _load_font(42)
    bbox = draw.textbbox((0, 0), initial, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((64 - text_w) / 2, (64 - text_h) / 2 - 4),
        initial,
        fill="white",
        font=font,
    )

    name_font = _load_font(36)
    draw.text((120, 38), display, fill=primary, font=name_font)

    out_dir = STATIC_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "logo.png"
    image.save(out_path, "PNG")
    return out_path


def create_favicon(slug: str, display: str, primary: tuple, accent: tuple) -> Path:
    size = (64, 64)
    image = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle((4, 4, 60, 60), radius=12, fill=primary)
    draw.rounded_rectangle((12, 12, 52, 52), radius=8, fill=accent)

    initial = display[0].upper()
    font = _load_font(28)
    bbox = draw.textbbox((0, 0), initial, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((64 - text_w) / 2, (64 - text_h) / 2 - 2),
        initial,
        fill="white",
        font=font,
    )

    out_dir = STATIC_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "favicon.png"
    image.save(out_path, "PNG")
    return out_path


def main() -> None:
    for company in COMPANIES:
        logo = create_logo(
            company["slug"],
            company["display"],
            company["primary"],
            company["accent"],
            company["bg"],
        )
        favicon = create_favicon(
            company["slug"],
            company["display"],
            company["primary"],
            company["accent"],
        )
        print(f"Created {logo}")
        print(f"Created {favicon}")


if __name__ == "__main__":
    main()
