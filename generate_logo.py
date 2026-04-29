import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
from rembg import remove

# ================= CONFIGURATION =================
IMAGE_PATH = "app/images/avtr-01.png"
BORDER_COLOR = "#00ACAC"
BORDER_WIDTH = 8       # Base border width in pixels
FONT_SIZE = 50         # Base font size
MARGIN_PERCENT = 0.10  # 15% distance from the closest border to the text box
SPLIT_PERCENT = 0.70   # Position of the before/after split line (0.0 to 1.0)
# =================================================

def create_checkerboard(width, height, size=20):
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    for y in range(0, height, size):
        for x in range(0, width, size):
            if (x // size + y // size) % 2 == 1:
                draw.rectangle([x, y, x + size, y + size], fill=(200, 200, 200))
    return img

def main():
    input_path = Path(IMAGE_PATH)
    if not input_path.exists():
        print(f"File {input_path} not found.")
        sys.exit(1)

    orig = Image.open(input_path).convert("RGBA")
    no_bg_bytes = remove(input_path.read_bytes())
    no_bg = Image.open(io.BytesIO(no_bg_bytes)).convert("RGBA")

    min_dim = min(orig.size)
    left = (orig.width - min_dim) // 2
    top = (orig.height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim

    orig = orig.crop((left, top, right, bottom))
    no_bg = no_bg.crop((left, top, right, bottom))

    scale = 3
    base_size = 800
    target_size = base_size * scale

    orig = orig.resize((target_size, target_size), Image.Resampling.LANCZOS)
    no_bg = no_bg.resize((target_size, target_size), Image.Resampling.LANCZOS)

    checker = create_checkerboard(target_size, target_size, size=30 * scale)
    after_side = Image.alpha_composite(checker.convert("RGBA"), no_bg)

    final = Image.new('RGBA', (target_size, target_size))
    split_x = int(target_size * SPLIT_PERCENT)

    left_half = orig.crop((0, 0, split_x, target_size))
    final.paste(left_half, (0, 0))

    right_half = after_side.crop((split_x, 0, target_size, target_size))
    final.paste(right_half, (split_x, 0))

    draw = ImageDraw.Draw(final)

    # Line
    draw.line([(split_x, 0), (split_x, target_size)], fill="white", width=6 * scale)

    # Handle
    handle_y = target_size // 2
    handle_radius = 25 * scale
    draw.ellipse([
        (split_x - handle_radius, handle_y - handle_radius),
        (split_x + handle_radius, handle_y + handle_radius)
    ], fill="white", outline="#ccc", width=2 * scale)

    # Left arrow
    aw = 12 * scale
    ah = 8 * scale
    draw.polygon([
        (split_x - aw, handle_y),
        (split_x - (aw // 3), handle_y - ah),
        (split_x - (aw // 3), handle_y + ah)
    ], fill="#666")
    # Right arrow
    draw.polygon([
        (split_x + aw, handle_y),
        (split_x + (aw // 3), handle_y - ah),
        (split_x + (aw // 3), handle_y + ah)
    ], fill="#666")

    # Font
    try:
        font_path = "/usr/share/fonts/TTF/Comfortaa-Bold.ttf"
        font = ImageFont.truetype(font_path, int(FONT_SIZE * scale))
    except Exception as e:
        print(f"Failed to load font, using default! {e}")
        font = ImageFont.load_default()

    def draw_label(text, x_pos, y_center, align="left"):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        
        pad_x, pad_y = 20 * scale, 15 * scale
        
        if align == "left":
            # x_pos is the left edge of the black box
            rect_x1 = x_pos
            rect_x2 = x_pos + tw + (pad_x * 2)
        elif align == "right":
            # x_pos is the right edge of the black box
            rect_x2 = x_pos
            rect_x1 = x_pos - tw - (pad_x * 2)
            
        rect_y1 = y_center - th // 2 - pad_y
        rect_y2 = y_center + th // 2 + pad_y
        
        draw.rounded_rectangle([rect_x1, rect_y1, rect_x2, rect_y2], radius=15 * scale, fill="black")
        
        # Draw text exactly in the center of the drawn rectangle
        text_x = rect_x1 + pad_x
        text_y = y_center - th // 2 - (4 * scale)
        draw.text((text_x, text_y), text, fill="white", font=font)

    # Position at 70% height
    y_center = int(target_size * 0.70)
    
    # Position BEFORE at MARGIN_PERCENT from the left edge
    margin_px = int(target_size * MARGIN_PERCENT)
    draw_label("BEFORE", margin_px, y_center, align="left")
    
    # Position AFTER at MARGIN_PERCENT from the right edge
    draw_label("AFTER", target_size - margin_px, y_center, align="right")

    # Alpha mask for clean rounded corners (applied FIRST to ensure edges are clipped perfectly)
    rad = 40 * scale
    b_width = BORDER_WIDTH * scale

    # Shrink the mask slightly so the image is cut off INSIDE the border area
    mask_shrink = b_width // 2
    alpha = Image.new('L', final.size, 0)
    draw_alpha = ImageDraw.Draw(alpha)
    draw_alpha.rounded_rectangle(
        [(mask_shrink, mask_shrink), (target_size - 1 - mask_shrink, target_size - 1 - mask_shrink)], 
        radius=rad - mask_shrink, 
        fill=255
    )
    final.putalpha(alpha)

    # Draw border on a separate transparent layer to guarantee it perfectly overlaps the edges
    border_layer = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
    draw_border = ImageDraw.Draw(border_layer)
    # By drawing the border at [0, 0], it will grow inwards to b_width.
    # Since the alpha mask stops at mask_shrink (which is b_width // 2), 
    # the image is completely hidden under the solid center of the border line.
    # No anti-aliasing edge will ever leak.
    draw_border.rounded_rectangle(
        [(0, 0), (target_size - 1, target_size - 1)], 
        radius=rad, 
        outline=BORDER_COLOR, 
        width=b_width
    )
    
    # Composite border over the final image
    final = Image.alpha_composite(final, border_layer)

    final = final.resize((base_size, base_size), Image.Resampling.LANCZOS)
    final.save("logo.png")
    print("Logo updated successfully.")

if __name__ == "__main__":
    main()
