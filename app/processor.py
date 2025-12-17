from pathlib import Path
from PIL import Image
from rembg import remove


def remove_bg_ai(input_path: Path, output_path: Path):
    print("🤖 Using AI background removal (rembg)")
    data = input_path.read_bytes()
    result = remove(data)
    output_path.write_bytes(result)


def remove_bg_color(
    input_path: Path,
    output_path: Path,
    threshold: int = 245
):
    print("🎨 Using color-based background removal")

    img = Image.open(input_path).convert("RGBA")
    pixels = img.getdata()

    new_pixels = []
    for r, g, b, a in pixels:
        if r > threshold and g > threshold and b > threshold:
            new_pixels.append((255, 255, 255, 0))
        else:
            new_pixels.append((r, g, b, a))

    img.putdata(new_pixels)
    img.save(output_path)


def looks_like_solid_background(image_path: Path, sample: int = 200) -> bool:
    img = Image.open(image_path).convert("RGB")
    pixels = list(img.getdata())

    white_pixels = 0
    for r, g, b in pixels[:sample]:
        if r > 245 and g > 245 and b > 245:
            white_pixels += 1

    ratio = white_pixels / sample
    print(f"🔍 White background ratio: {ratio:.2f}")

    return ratio > 0.7
