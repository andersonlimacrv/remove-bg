import os
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


def analyze_image(image_path: Path) -> dict:
    original_size = os.path.getsize(image_path)
    try:
        img = Image.open(image_path)
        mode = img.mode
        transparency = mode in ("RGBA", "LA") or (img.info.get("transparency", None) is not None)
        
        w, h = img.size
        pixels = w * h
        bpp = (original_size * 8) / pixels if pixels > 0 else 0
        
        if bpp > 5.0:
            complexity = "High"
        elif bpp > 2.0:
            complexity = "Medium"
        else:
            complexity = "Low"
            
        suggested_format = "webp"
        suggested_quality = 80
        if transparency:
            if complexity == "Low":
                suggested_format = "png"
                suggested_quality = "lossless"
                reason = "Transparency with low complexity (likely logo/icon)"
            else:
                reason = "Transparency with high/medium complexity"
        else:
            if complexity == "Low":
                suggested_format = "webp"
                suggested_quality = "lossless"
                reason = "No transparency, low complexity (flat colors/smooth gradients)"
            else:
                reason = "No transparency, medium/high complexity (photo/AI)"

        expected_reduction = "~60-80%" if suggested_format == "webp" else "~10-30%"
        trade_offs = []
        if suggested_quality != "lossless":
            trade_offs.append("Slight loss in sharp edges possible")
        trade_offs.append("Much smaller size")
        
        return {
            "name": image_path.name,
            "transparency": transparency,
            "complexity": complexity,
            "suggested_format": suggested_format,
            "suggested_quality": suggested_quality,
            "reason": reason,
            "expected_reduction": expected_reduction,
            "trade_offs": trade_offs,
            "size_kb": original_size / 1024
        }
    except Exception as e:
         return {"error": str(e)}


def compress_image(input_path: Path, output_path: Path, format: str = None, quality: int = 80, lossless: bool = False, keep_format: bool = False) -> dict:
    original_size = os.path.getsize(input_path)
    
    if original_size < 50 * 1024:
        return {"skipped": True, "reason": "Skipping small file (already optimized)"}
        
    img = Image.open(input_path)
    orig_format = img.format.lower() if img.format else input_path.suffix.lstrip(".").lower()
    if orig_format == "jpeg":
        orig_format = "jpg"
    
    # Priority rules
    if keep_format:
        target_format = orig_format
    elif format:
        target_format = format.lower()
        if target_format == "jpeg":
            target_format = "jpg"
    else:
        # Auto mode
        analysis = analyze_image(input_path)
        target_format = analysis.get("suggested_format", "webp")
        if target_format == "webp" and analysis.get("suggested_quality") == "lossless":
            lossless = True
            
    # RGBA to RGB conversion if needed
    if target_format in ("jpg", "jpeg") and img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        # use alpha channel as mask if present
        if len(img.split()) == 4:
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        img = background
        
    save_kwargs = {}
    if target_format in ("jpg", "jpeg"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif target_format == "webp":
        save_kwargs["quality"] = quality
        save_kwargs["lossless"] = lossless
        if lossless:
            save_kwargs["method"] = 6
    elif target_format == "png":
        save_kwargs["optimize"] = True
        
    img.save(output_path, format=target_format if target_format != "jpg" else "jpeg", **save_kwargs)
    new_size = os.path.getsize(output_path)
    
    return {
        "skipped": False,
        "original_size": original_size,
        "new_size": new_size,
        "reduction_pct": ((original_size - new_size) / original_size) * 100 if original_size > 0 else 0,
        "target_format": target_format,
        "lossless": lossless,
        "quality": quality,
        "orig_format": orig_format
    }
