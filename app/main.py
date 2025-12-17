import argparse
from pathlib import Path

from app.fs import (
    ensure_dirs,
    move_original,
    no_bg_output_path,
    list_valid_images
)
from app.processor import (
    remove_bg_ai,
    remove_bg_color,
    parse_color,
    detect_background_color,
    looks_like_solid_background
)


def main():
    parser = argparse.ArgumentParser(
        description="Remove image backgrounds using AI or color strategies"
    )

    parser.add_argument(
        "--type",
        choices=["auto", "ai", "color"],
        default="auto",
        help="Background removal strategy (default: auto)",
    )

    parser.add_argument(
        "--color",
        default="auto",
        help="Background color for COLOR strategy (white, black, #ffffff, auto)",
    )

    parser.add_argument(
        "--tolerance",
        type=int,
        default=15,
        help="Color tolerance when using COLOR strategy",
    )

    args = parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    ensure_dirs(base)

    images = list_valid_images(images_dir)

    if not images:
        print("⚠️ No valid images found in app/images/")
        return

    print(f"🖼 Found {len(images)} image(s)")
    print(f"⚙ Strategy: {args.type.upper()}")

    for image in images:
        print(f"\n➡ Processing {image.name}")

        try:
            original = move_original(image, base)
            output = no_bg_output_path(base, original.name)

            if args.type == "ai":
                remove_bg_ai(original, output)

            elif args.type == "color":
                color = (
                    detect_background_color(original)
                    if args.color == "auto"
                    else parse_color(args.color)
                )
                remove_bg_color(original, output, color, args.tolerance)

            else:  # AUTO
                print("🧠 AUTO mode enabled")

                if looks_like_solid_background(original):
                    print("🧠 Solid background detected → COLOR strategy")
                    color = detect_background_color(original)
                    remove_bg_color(original, output, color, args.tolerance)
                else:
                    print("🧠 Complex background detected → AI strategy")
                    remove_bg_ai(original, output)

            print(f"✅ Saved: {output}")

        except Exception as e:
            print(f"❌ Error processing {image.name}")
            print(f"   ↳ {e}")

    print("\n🎉 All images processed successfully")
