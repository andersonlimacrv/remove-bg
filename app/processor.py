from pathlib import Path
from collections import Counter
from PIL import Image
from rembg import remove


def remove_bg_ai(input_path: Path, output_path: Path):
    print("🤖 Using AI background removal (rembg)")
    data = input_path.read_bytes()
    result = remove(data)
    output_path.write_bytes(result)


def parse_color(color: str) -> tuple[int, int, int]:
    color = color.lower()

    if color == "white":
        return (255, 255, 255)
    if color == "black":
        return (0, 0, 0)
    if color.startswith("#"):
        color = color.lstrip("#")
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

    raise ValueError(f"Unsupported color format: {color}")


def detect_background_color(image_path: Path, samples: int = 80) -> tuple[int, int, int]:
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    border_pixels = []

    for x in range(0, w, max(1, w // samples)):
        border_pixels.append(img.getpixel((x, 0)))
        border_pixels.append(img.getpixel((x, h - 1)))

    for y in range(0, h, max(1, h // samples)):
        border_pixels.append(img.getpixel((0, y)))
        border_pixels.append(img.getpixel((w - 1, y)))

    color = Counter(border_pixels).most_common(1)[0][0]
    print(f"🎯 Detected background color: {color}")
    return color


def remove_bg_color(
    input_path: Path,
    output_path: Path,
    target_color: tuple[int, int, int],
    tolerance: int = 15,
):
    print(f"🎨 Removing color background {target_color} (tolerance={tolerance})")

    img = Image.open(input_path).convert("RGBA")
    pixels = img.getdata()

    new_pixels = []
    for r, g, b, a in pixels:
        if (
            abs(r - target_color[0]) <= tolerance
            and abs(g - target_color[1]) <= tolerance
            and abs(b - target_color[2]) <= tolerance
        ):
            new_pixels.append((r, g, b, 0))
        else:
            new_pixels.append((r, g, b, a))

    img.putdata(new_pixels)
    img.save(output_path)


def looks_like_solid_background(image_path: Path, sample: int = 200) -> bool:
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())[:sample]

    bright = sum(
        1 for r, g, b in pixels if r > 240 and g > 240 and b > 240
    )

    ratio = bright / sample
    print(f"🔍 Bright background ratio: {ratio:.2f}")

    return ratio > 0.65
