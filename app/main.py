import argparse
from pathlib import Path

from app.fs import (
    ensure_dirs,
    move_original,
    no_bg_output_path,
    compressed_output_path,
    list_valid_images
)
from app.processor import (
    remove_bg_ai,
    remove_bg_color,
    parse_color,
    detect_background_color,
    looks_like_solid_background,
    analyze_image,
    compress_image
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


def main_compress():
    parser = argparse.ArgumentParser(
        description="Compress and convert images"
    )

    parser.add_argument(
        "--quality",
        type=int,
        default=80,
        help="Quality for lossy formats (0-100, default: 80)",
    )

    parser.add_argument(
        "--format",
        help="Force conversion to a specific format (e.g., webp, jpeg, png)",
    )

    parser.add_argument(
        "--keep-format",
        action="store_true",
        help="Force keeping the original format",
    )
    
    parser.add_argument(
        "--lossless",
        action="store_true",
        help="Force lossless compression (for WebP/PNG)",
    )

    args = parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    ensure_dirs(base)

    images = list_valid_images(images_dir)

    if not images:
        print("⚠️ No valid images found in app/images/")
        return

    print(f"🖼 Found {len(images)} image(s) for compression")

    for image in images:
        print(f"\n➡ Processing {image.name}")

        try:
            original = move_original(image, base)
            
            # Temporary output path for compression, we'll rename it based on format
            ext = f".{args.format}" if args.format else original.suffix
            output = compressed_output_path(base, original.name, ext)
            
            res = compress_image(
                original, 
                output, 
                format=args.format, 
                quality=args.quality, 
                lossless=args.lossless, 
                keep_format=args.keep_format
            )
            
            if res.get("skipped"):
                print(f"⏭ {res.get('reason', 'Skipping file')}")
                import shutil
                output = compressed_output_path(base, original.name, original.suffix)
                shutil.copy2(original, output)
                print(f"✅ Saved original: {output}")
                continue
                
            orig_kb = res['original_size'] / 1024
            new_kb = res['new_size'] / 1024
            pct = res['reduction_pct']
            
            # Adjust output path if target format changed from what we guessed
            final_ext = f".{res['target_format']}"
            if output.suffix.lower() != final_ext:
                new_output = output.with_suffix(final_ext)
                output.rename(new_output)
                output = new_output
                
            mode_str = "lossless" if res['lossless'] else f"lossy | quality={res['quality']}"
            
            print(f"📦 {original.name} → {output.name}")
            if orig_kb > 1024:
                print(f"📉 {orig_kb/1024:.1f}MB → {new_kb/1024:.1f}MB (-{pct:.0f}%)")
            else:
                print(f"📉 {orig_kb:.1f}KB → {new_kb:.1f}KB (-{pct:.0f}%)")
            print(f"⚙️ Mode: {mode_str}")
            print(f"✅ Saved: {output}")

        except Exception as e:
            print(f"❌ Error processing {image.name}")
            print(f"   ↳ {e}")

    print("\n🎉 All images processed successfully")


def main_analyze():
    parser = argparse.ArgumentParser(
        description="Analyze images for compression suggestions without modifying them"
    )
    parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    images = list_valid_images(images_dir)

    if not images:
        print("⚠️ No valid images found in app/images/")
        return

    print(f"🖼 Found {len(images)} image(s) for analysis\n")

    for image in images:
        try:
            res = analyze_image(image)
            if "error" in res:
                print(f"🔍 {image.name}\n- Error: {res['error']}\n")
                continue
                
            print(f"🔍 {image.name}")
            
            if res["transparency"]:
                print("- Transparency detected")
            else:
                print("- No transparency")
                
            print(f"- {res['complexity']} complexity")
            
            if res.get("size_kb", 0) < 50:
                print(f"→ Suggest: Skip compression")
                print("→ Expected reduction: None (Size < 50KB)")
                print("Trade-offs:")
                print("- None (original preserved)\n")
                continue
                
            mode_str = "lossless" if res['suggested_quality'] == "lossless" else f"quality={res['suggested_quality']}"
            print(f"→ Suggest: {res['suggested_format'].upper()} ({mode_str})")
            print(f"→ Expected reduction: {res['expected_reduction']}")
            
            print("Trade-offs:")
            for to in res['trade_offs']:
                print(f"- {to}")
            print()
                
        except Exception as e:
            print(f"❌ Error analyzing {image.name}")
            print(f"   ↳ {e}\n")
