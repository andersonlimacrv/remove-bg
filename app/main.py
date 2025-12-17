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
    looks_like_solid_background
)


def main():
    parser = argparse.ArgumentParser(
        description="Remove image backgrounds using multiple strategies"
    )

    parser.add_argument(
        "--type",
        choices=["auto", "ai", "color"],
        default="auto",
        help="Background removal strategy (default: auto)"
    )

    args = parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    print("🖼 Starting background removal")
    print(f"⚙ Strategy: {args.type.upper()}")

    ensure_dirs(base)

    images = list_valid_images(images_dir)

    if not images:
        print("⚠ No valid images found in images/ folder")
        return

    print(f"📂 Found {len(images)} valid image(s)")

    for image in images:
        try:
            print(f"\n➡ Processing {image.name}")

            original = move_original(image, base)
            output = no_bg_output_path(base, original.name)

            if args.type == "color":
                remove_bg_color(original, output)

            elif args.type == "ai":
                remove_bg_ai(original, output)

            else:  # AUTO
                print("🧠 AUTO mode enabled")

                if looks_like_solid_background(original):
                    print("🧠 Solid background detected → COLOR strategy")
                    remove_bg_color(original, output)
                else:
                    print("🧠 Complex background detected → AI strategy")
                    remove_bg_ai(original, output)

            print(f"✅ Saved: {output}")

        except Exception as e:
            print(f"❌ Error processing {image.name}")
            print(f"   ↳ {e}")

    print("\n🎉 All images processed successfully")
