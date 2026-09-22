from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = Path(
    r"C:/Users/19512/Documents/Tencent Files/1951227340/nt_qq/nt_data/Pic/2026-06/Ori/b94232f81495ffef7bca83481904b9da.png"
)
OUTPUT_DIR = PROJECT_ROOT / "game" / "gui" / "story_ui"


def crop(source, box, filename):
    image = source.crop(box).convert("RGBA")
    image.save(OUTPUT_DIR / filename)
    return image


def hover_variant(image, filename):
    bright = ImageEnhance.Brightness(image).enhance(1.10)
    contrast = ImageEnhance.Contrast(bright).enhance(1.04)
    contrast.save(OUTPUT_DIR / filename)


def clean_notebook(image):
    cleaned = image.copy()
    draw = ImageDraw.Draw(cleaned, "RGBA")

    # Remove the sample quote and default quick-menu marks from the mockup while
    # keeping the paper area close to the original crop.
    draw.rectangle((320, 74, 620, 144), fill=(237, 229, 213, 236))
    draw.rectangle((290, 268, 1110, 330), fill=(237, 229, 213, 232))
    draw.rectangle((1040, 210, 1115, 266), fill=(237, 229, 213, 210))
    draw.rectangle((90, 230, 282, 312), fill=(199, 179, 139, 226))

    cleaned.save(OUTPUT_DIR / "ui_notebook_base.png")


def clean_portrait(image):
    cleaned = image.copy()
    draw = ImageDraw.Draw(cleaned, "RGBA")
    draw.rectangle((56, 228, 250, 326), fill=(199, 179, 139, 226))
    cleaned.save(OUTPUT_DIR / "ui_portrait_card.png")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_IMAGE).convert("RGB")

    notebook = source.crop((270, 470, 1638, 852)).convert("RGBA")
    clean_notebook(notebook)

    phone = crop(source, (34, 402, 315, 852), "ui_phone_idle.png")
    hover_variant(phone, "ui_phone_hover.png")

    portrait = source.crop((302, 458, 570, 804)).convert("RGBA")
    clean_portrait(portrait)

    pen = crop(source, (1630, 548, 1844, 852), "ui_pen_idle.png")
    hover_variant(pen, "ui_pen_hover.png")

    crop(source, (0, 0, 675, 205), "ui_top_status.png")

    buttons = {
        "character": (1408, 18, 1548, 162),
        "inventory": (1558, 18, 1696, 162),
        "medicine": (1702, 18, 1842, 162),
    }
    for name, box in buttons.items():
        image = crop(source, box, f"ui_btn_{name}_idle.png")
        hover_variant(image, f"ui_btn_{name}_hover.png")


if __name__ == "__main__":
    main()
