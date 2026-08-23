import argparse
from pathlib import Path

from app.fs import (
    ensure_dirs,
    move_original,
    no_bg_output_path,
    compressed_output_path,
    vectorized_output_path,
    list_valid_images
)
from app.processor import (
    remove_bg_ai,
    remove_bg_color,
    parse_color,
    detect_background_color,
    looks_like_solid_background,
    analyze_image,
    compress_image,
    format_avatar
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


def main_format_avatar():
    parser = argparse.ArgumentParser(
        description="Format images to be avatars (< 1MB, standardized)"
    )

    parser.add_argument(
        "--max-size",
        type=int,
        default=1000,
        help="Maximum size in KB (default: 1000 = 1MB)",
    )

    parser.add_argument(
        "--keep-format",
        action="store_true",
        help="Force keeping the original format",
    )

    args = parser.parse_args()

    base = Path(__file__).parent
    images_dir = base / "images"

    ensure_dirs(base)

    images = list_valid_images(images_dir)

    if not images:
        print("⚠️ No valid images found in app/images/")
        return

    print(f"🖼 Found {len(images)} image(s) for avatar formatting")

    for image in images:
        print(f"\n➡ Formatting {image.name} as Avatar")

        try:
            original = move_original(image, base)
            
            ext = original.suffix if args.keep_format else ".webp"
            output = compressed_output_path(base, original.name, ext)
            
            res = format_avatar(original, output, max_size_kb=args.max_size, keep_format=args.keep_format)
            
            # Adjust output path if target format changed
            final_ext = f".{res['target_format']}"
            if output.suffix.lower() != final_ext:
                new_output = output.with_suffix(final_ext)
                output.rename(new_output)
                output = new_output
                
            orig_kb = res['original_size'] / 1024
            new_kb = res['new_size'] / 1024
            pct = res['reduction_pct']
            
            print(f"📦 {original.name} → {output.name}")
            if orig_kb > 1024:
                print(f"📉 {orig_kb/1024:.1f}MB → {new_kb/1024:.1f}MB (-{pct:.0f}%)")
            else:
                print(f"📉 {orig_kb:.1f}KB → {new_kb:.1f}KB (-{pct:.0f}%)")
            
            resize_str = " (Resized to max 1024px)" if res['resized'] else ""
            print(f"⚙️ Mode: Avatar Format | quality={res['quality']}{resize_str}")
            print(f"✅ Saved: {output}")

        except Exception as e:
            print(f"❌ Error processing {image.name}")
            print(f"   ↳ {e}")

    print("\n🎉 All avatars formatted successfully")


def main_vectorize():
    parser = argparse.ArgumentParser(
        description="Convert raster images to SVG vectors (vtracer + skeleton)"
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Input image path (optional, defaults to batch processing app/images/)",
    )

    parser.add_argument(
        "-o", "--output",
        help="Output SVG path (only when single input file is given)",
    )

    parser.add_argument(
        "--mode",
        choices=["outline", "centerline"],
        default="outline",
        help="Vectorization mode: outline (filled shapes, vtracer) or centerline (single stroke, handwriting) (default: outline)",
    )

    parser.add_argument(
        "--colormode",
        choices=["color", "binary"],
        default="color",
        help="Color mode for outline: color preserves palette, binary is B/W only (default: color)",
    )

    parser.add_argument(
        "--preset",
        choices=["excellent", "standard", "draft"],
        default="excellent",
        help="Quality preset (default: excellent)",
    )

    parser.add_argument(
        "--hierarchical",
        choices=["stacked", "cutout"],
        default="stacked",
        help="SVG stacking strategy for outline (default: stacked)",
    )

    parser.add_argument(
        "--filter-speckle",
        type=int,
        help="Discard patches smaller than X px (overrides preset)",
    )

    parser.add_argument(
        "--color-precision",
        type=int,
        help="Bits per channel for color (1-8, overrides preset)",
    )

    parser.add_argument(
        "--corner-threshold",
        type=int,
        help="Min angle to be corner in degrees (overrides preset)",
    )

    parser.add_argument(
        "--length-threshold",
        type=float,
        help="Min length for spline segment (overrides preset)",
    )

    parser.add_argument(
        "--path-precision",
        type=int,
        help="Decimal precision for SVG paths (overrides preset)",
    )

    parser.add_argument(
        "--upscale",
        type=int,
        default=1,
        help="Upscale factor before tracing for higher quality on small images (default: 1)",
    )

    # Centerline specific
    parser.add_argument(
        "--threshold",
        type=int,
        help="Binarization threshold 0-255 for centerline (default: Otsu auto)",
    )

    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert binary for centerline (use if stroke is white on dark)",
    )

    parser.add_argument(
        "--stroke-width",
        type=int,
        default=3,
        help="Stroke width for centerline SVG (default: 3)",
    )

    parser.add_argument(
        "--no-preserve-original",
        action="store_true",
        help="Don't move originals to originals/ folder (default: moves)",
    )

    args = parser.parse_args()

    from app.vectorizer import vectorize_image

    base = Path(__file__).parent
    images_dir = base / "images"

    ensure_dirs(base)

    # Determine input list
    images: list[Path] = []
    single_mode = False

    if args.input:
        p = Path(args.input)
        if not p.is_absolute():
            # try relative to cwd, then to base
            if not p.exists():
                p2 = base / p
                if p2.exists():
                    p = p2
                else:
                    p3 = Path.cwd() / args.input
                    if p3.exists():
                        p = p3
        if not p.exists():
            print(f"❌ Input not found: {args.input}")
            return
        if p.is_file():
            images = [p]
            single_mode = True
        else:
            # directory
            from app.fs import SUPPORTED_EXTENSIONS
            images = [f for f in p.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
    else:
        images = list_valid_images(images_dir)

    if not images:
        print("⚠️ No valid images found in app/images/ (or input path)")
        return

    print(f"🖼 Found {len(images)} image(s) for vectorization")
    print(f"⚙ Mode: {args.mode.upper()} | Preset: {args.preset} | Color: {args.colormode if args.mode=='outline' else 'N/A (centerline)'}")

    for image in images:
        print(f"\n➡ Processing {image.name} → SVG")

        try:
            # Preserve original unless --no-preserve-original or single_mode with absolute path outside app/images
            should_move = not args.no_preserve_original and not single_mode and image.parent == images_dir
            if should_move:
                original = move_original(image, base)
            else:
                # For single file mode, use file directly; ensure it exists
                original = image
                if single_mode and args.input and Path(args.input).exists():
                    # keep as is
                    pass

            if single_mode and args.output:
                output = Path(args.output)
                if not output.is_absolute():
                    output = Path.cwd() / output
                output.parent.mkdir(parents=True, exist_ok=True)
            else:
                output = vectorized_output_path(base, original.name)

            # Build kwargs for vectorizer
            if args.mode == "outline":
                kwargs = {
                    "colormode": args.colormode,
                    "hierarchical": args.hierarchical,
                    "preset": args.preset,
                    "upscale": args.upscale,
                }
                if args.filter_speckle is not None:
                    kwargs["filter_speckle"] = args.filter_speckle
                if args.color_precision is not None:
                    kwargs["color_precision"] = args.color_precision
                if args.corner_threshold is not None:
                    kwargs["corner_threshold"] = args.corner_threshold
                if args.length_threshold is not None:
                    kwargs["length_threshold"] = args.length_threshold
                if args.path_precision is not None:
                    kwargs["path_precision"] = args.path_precision

                res = vectorize_image(original, output, mode="outline", **kwargs)
            else:
                kwargs = {
                    "threshold": args.threshold,
                    "invert": args.invert,
                    "stroke_width": args.stroke_width,
                }
                res = vectorize_image(original, output, mode="centerline", **kwargs)

            orig_kb = res.get("original_size", 0) / 1024
            svg_kb = res.get("svg_size", 0) / 1024
            n_paths = res.get("num_paths", res.get("num_strokes", "?"))

            print(f"📦 {original.name} → {output.name}")
            if orig_kb > 1024:
                print(f"📊 {orig_kb/1024:.1f}MB → {svg_kb:.1f}KB | Paths: {n_paths}")
            else:
                print(f"📊 {orig_kb:.1f}KB → {svg_kb:.1f}KB | Paths: {n_paths}")
            if res.get("backend") == "vtracer":
                print(f"⚙️ Backend: vtracer | Params: {res.get('params')}")
            else:
                print(f"⚙️ Backend: skeleton | Strokes: {res.get('num_strokes')}")
            print(f"✅ Saved: {output}")

        except Exception as e:
            import traceback
            print(f"❌ Error processing {image.name}")
            print(f"   ↳ {e}")
            traceback.print_exc()

    print("\n🎉 All images vectorized successfully")
    if not single_mode:
        print(f"📁 Output: {base / 'vectorized'}")
