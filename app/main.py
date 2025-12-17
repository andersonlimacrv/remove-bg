import argparse
from pathlib import Path

from app.fs import ensure_dirs, move_original, no_bg_output_path
from app.processor import (
    remove_bg_ai,
    remove_bg_color,
    looks_like_solid_background,
)


def main():
    parser = argparse.ArgumentParser(
        description="Remove image backgrounds using multiple strategies"
    )

    parser.add_argument(
        "--type",
        choices=["ai", "color"],
        required=False,
        help="Force background removal strategy (ai or color). "
             "If omitted, AUTO mode is used."
    )

    args = parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    ensure_dirs(base)

    images = [p for p in images_dir.iterdir() if p.is_file()]

    if not images:
        print("⚠️ No images found in images/ folder")
        return

    strategy = args.type or "auto"

    print(f"🖼️ Found {len(images)} image(s)")
    print(f"⚙️ Strategy: {strategy.upper()}")

    for image in images:
        try:
            print(f"\n➡️ Processing {image.name}")

            original = move_original(image, base)
            output = no_bg_output_path(base, original.name)

            if args.type == "color":
                print("🎨 Forced COLOR strategy")
                remove_bg_color(original, output)

            elif args.type == "ai":
                print("🤖 Forced AI strategy")
                remove_bg_ai(original, output)

            else:
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
