# remove-bg 🔥

A lightweight, developer-first CLI to remove backgrounds and optimize images with zero friction.
Process batches, auto-select strategies, compress intelligently, vectorize to SVG — all locally, fast, and free.

<p align="center">
  <img src="logo.png" alt="remove-bg before/after logo" width="300" style="border-radius: 8px;">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Poetry-Package%20Manager-blueviolet?logo=poetry&logoColor=white" alt="Poetry">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [📁 Project Structure](#-project-structure)
- [🚀 How It Works](#-how-it-works)
- [🧰 Requirements](#-requirements)
- [📦 Installation](#-installation)
- [▶️ Usage](#️-usage)
- [🔠 Image to SVG (Vectorization)](#-image-to-svg-vectorization)
- [🗜️ Image Compression](#️-image-compression)
- [🧪 Supported Formats](#-supported-formats)
- [🛠️ Tech Stack](#️-tech-stack)
- [📄 License](#-license)

---

## ✨ Features

- 🧠 **Automatic strategy selection** (default)
- 🤖 AI-based background removal (rembg)
- 🎨 Fast color-based removal for solid backgrounds
- 📂 Automatic folder organization by date
- 🧼 Input folder is cleaned after processing
- 🖥️ Verbose and friendly terminal output with emojis
- 📦 Managed with Poetry
- 🔠 **Image to SVG vectorization** — high-quality `outline` (vtracer) and handwriting `centerline` (skeleton)
- 🎯 **Excellent preset by default** — curved splines, 8-decimal precision, zero config

---

## 📁 Project Structure

```text
remove-bg/
├── app/
│   ├── fs.py              # Filesystem helpers (images/originals/no-bg/compressed/vectorized)
│   ├── processor.py       # Background removal + compression
│   ├── vectorizer.py      # Raster → Vector (vtracer outline + skeleton centerline)
│   ├── main.py            # CLI entry points (rmbg, cmpss, anlz-cmpss, fmt-avt, img2svg)
│   └── __init__.py
├── app/images/            # Drop images here
├── app/originals/
│   └── YYYY-MM-DD/        # Archived original images
├── app/no-bg/
│   └── YYYY-MM-DD/        # Processed images (no background)
├── app/compressed/
│   └── YYYY-MM-DD/        # Compressed images
├── app/vectorized/
│   └── YYYY-MM-DD/        # Vectorized SVGs
├── pyproject.toml
└── README.md
````

---

## 🚀 How It Works

1. Place images inside the `app/images/` folder
2. Run the command
3. The tool will:

   * Decide the best strategy automatically (**AUTO mode**)
   * Or use a forced strategy if specified
   * Move original images to `originals/<date>/`
   * Save background-removed images to `no-bg/<date>/`
   * Save compressed images to `compressed/<date>/`
   * Save vectorized SVGs to `vectorized/<date>/`
   * Keep the `images/` folder clean

---

## 🧰 Requirements

* Python **3.12+**
* Poetry **2.x**
* Linux / macOS (Windows should work but is not the main target)

---

## 📦 Installation

```bash
git clone https://github.com/andersonlimacrv/remove-bg.git
cd remove-bg
poetry install
```

---

## ▶️ Usage

### 🔹 Automatic mode (default)

Uses a heuristic to choose the best strategy:

* Solid / mostly white background → 🎨 **COLOR**
* Complex background → 🤖 **AI**

```bash
poetry run rmbg
```

---

### 🔹 Force AI strategy

Recommended for people, products and complex images.

```bash
poetry run rmbg --type ai
```

---

### 🔹 Force color-based strategy

Recommended for logos, icons and solid backgrounds.

```bash
poetry run rmbg --type color
```

---

### 🔹 Force specific background color
```bash
poetry run rmbg --type color --color white
poetry run rmbg --type color --color "#f5f5f5"
```

### 🔹 Adjust color tolerance
```bash
poetry run rmbg --type color --tolerance 25
```

##  AUTO Strategy Explained

In AUTO mode, the tool :

1. Samples pixels from the image
2. Detects if the background is mostly white
3. Chooses:

   * 🎨 COLOR strategy for solid backgrounds
   * 🤖 AI strategy for complex backgrounds

This improves performance and avoids unnecessary AI processing.

## 🧠 AUTO Mode Logic

```yaml
AUTO:
 ├─ Solid / bright background?
 │   ├─ Yes → Detect color → COLOR
 │   └─ No  → AI (rembg)
```

---

## 🔠 Image to SVG (Vectorization)

Convert any raster image (`PNG/JPG/WEBP`) into a scalable `SVG` vector with excellent quality. Optimized for **logos, icons, line-art and alphabets** — including a full alphabet sheet with all letters in a single image (no grid required).

Two modes are available:

| Mode | Backend | Output | Best for | Animatable as handwriting? |
|---|---|---|---|---|
| `outline` (default) | `vtracer` (Rust) | `<path fill="...">` closed shapes | Logos, icons, filled alphabets | No (filled area) |
| `centerline` | `scikit-image` skeleton | `<path fill="none" stroke="...">` single stroke | Handwriting / thin strokes | **Yes** (`stroke-dasharray`) |

> **Excellent quality is the default** (`--preset excellent`). No tuning needed for most cases.

### 🔹 Batch mode (recommended)

Drop your images into `app/images/` and run:

```bash
# Outline with excellent quality, binary (B/W) — ideal for P&B alphabets
poetry run img2svg --mode outline --preset excellent --colormode binary

# Outline color — preserves palette (teal, red, etc.)
poetry run img2svg --mode outline --preset excellent --colormode color

# Centerline — single stroke for handwriting animation
poetry run img2svg --mode centerline
```

Output goes to `app/vectorized/YYYY-MM-DD/*.svg`. Originals are archived to `app/originals/` (use `--no-preserve-original` to keep them in `images/`).

**Example output:**
```text
🖼 Found 1 image(s) for vectorization
⚙ Mode: OUTLINE | Preset: excellent | Color: binary

➡ Processing alphabet.png → SVG
📦 alphabet.png → alphabet.svg
📊 69.5KB → 62.7KB | Paths: 27
⚙️ Backend: vtracer | Params: {'filter_speckle': 2, 'color_precision': 8, ...}
✅ Saved: app/vectorized/2026-08-23/alphabet.svg
```

### 🔹 Single file

```bash
# Vectorize a specific file outside app/images
poetry run img2svg /path/to/alphabet.png -o ./alphabet.svg --mode outline --colormode binary

# Or keep inside project with custom output
poetry run img2svg app/images/demo_alphabet.png --mode outline -o /tmp/out.svg --no-preserve-original
```

### 🔹Alfabeto completo (todas as letras em uma única imagem, sem grade) — caso atual

Se sua imagem já contém `A-Z` espalhadas (ex: `alphabet.png` 2400x800), use **outline binary excellent**:

```bash
poetry run img2svg --mode outline --preset excellent --colormode binary
```

Isso gera um único `alphabet.svg` com ~26-27 paths (um por letra), curvas spline suaves e precisão de 8 casas decimais. Para alfabeto colorido, troque para `--colormode color`.

### 🔹 Presets de qualidade

```bash
--preset excellent  # default: filter_speckle=2, color_precision=8, corner=30, length=2.0, path_precision=8
--preset standard   # balanced: speckle=4, precision=6
--preset draft      # fast/light: speckle=16, precision=4
```

### 🔹 Fine-tuning (override do preset)

```bash
# Keep tiny details (lower speckle) or discard noise (higher)
poetry run img2svg --filter-speckle 4

# Bits per channel for color (1-8)
poetry run img2svg --color-precision 6

# Smoothing controls
poetry run img2svg --corner-threshold 60 --length-threshold 4.0 --path-precision 5

# Upscale small images before tracing for higher fidelity
poetry run img2svg --upscale 2
```

### 🔹 Centerline options (handwriting)

```bash
# Default Otsu threshold (auto)
poetry run img2svg --mode centerline

# Fixed threshold 0-255 (for low contrast scans)
poetry run img2svg --mode centerline --threshold 128

# Invert if stroke is white on dark background
poetry run img2svg --mode centerline --invert

# Thicker stroke for animation visibility
poetry run img2svg --mode centerline --stroke-width 5
```

Centerline SVGs are ready for handwriting animation via `stroke-dasharray`:

```css
path {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  animation: draw 1.2s ease-in-out forwards;
}
@keyframes draw { to { stroke-dashoffset: 0; } }
```

Each stroke is a separate `<path>` with `pathLength="1"` and `stroke-linecap="round"`, so `stroke-dashoffset` animates exactly one pencil trace at a time — ideal for the future `A-Z` writing animation.

### 🔹 When to use which

- **Filled alphabet / logos with solid fills** → `outline --colormode binary` (or `color` if you need teal/red preserved)
- **Thin handwritten alphabet (pencil, 1 stroke per letter)** → `centerline`
- **Photo** → not recommended (SVG would be huge, use `cmpss` instead)

### 🔹 Notes

- SVG output preserves original dimensions via `viewBox`; scale infinitely without loss.
- Transparency (`RGBA`) is composited over white before tracing (vtracer has no alpha).
- `filter_speckle` removes dust < X px; increase if anti-aliased font generates tiny gray paths.

---

## 🧪 Supported Formats

**Input:**
* PNG
* JPG / JPEG
* WEBP

**Output:**
* PNG (no-bg)
* WEBP/JPG/PNG (compressed)
* **SVG** (vectorized)

---

## 🗜️ Image Compression

The `remove-bg` tool now includes an image compression module, providing smart compression and analysis without heavy dependencies.

### 🔹 Analyze Images (anlz-cmpss)

Analyze images in the `images/` folder to get compression suggestions without modifying any files. This is great for checking which strategy will be best, especially for AI-generated images.

```bash
poetry run anlz-cmpss
```

**Example Output:**
```text
🔍 avatar.png
- No transparency
- Medium complexity
→ Suggest: WEBP (quality=80)
→ Expected reduction: ~60-80%
Trade-offs:
- Slight loss in sharp edges possible
- Much smaller size
```

### 🔹 Compress Images (cmpss)

Compress images using the suggested strategies or force a specific format.

```bash
# Auto mode (chooses best format based on heuristics)
poetry run cmpss

# Force keeping the original format (no conversion)
poetry run cmpss --keep-format

# Force conversion to a specific format
poetry run cmpss --format webp

# Adjust quality (lossy formats)
poetry run cmpss --quality 75

# Force lossless compression
poetry run cmpss --lossless
```

**Format Conversion Priority:**
1. `--keep-format`: ALWAYS preserves the original extension.
2. `--format X`: Forces conversion to format X.
3. No arguments: Automatically decides based on heuristics.

**Note:** Files smaller than 50KB are automatically skipped to avoid unnecessary quality loss or size increases.

### 🔹 Format Avatars (fmt-avt)

Guarantees the image is formatted and compressed to fit under a specific size limit (default 1MB) and resizes it to a standard maximum dimension (1024px). Ideal for standardizing user avatars.

```bash
# Format to standard avatar size (< 1MB)
poetry run fmt-avt

# Set a custom max size (e.g., 500KB)
poetry run fmt-avt --max-size 500

# Force keeping the original format (prevents conversion to WebP)
poetry run fmt-avt --keep-format
```

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-white?style=for-the-badge&logo=poetry&logoColor=whit60A5FAe)
![Pillow](https://img.shields.io/badge/Pillow-violet?style=for-the-badge)
![rembg](https://img.shields.io/badge/rembg-green?style=for-the-badge)
![vtracer](https://img.shields.io/badge/vtracer-Rust-orange?style=for-the-badge)
![scikit-image](https://img.shields.io/badge/scikit--image-blue?style=for-the-badge)
![svgwrite](https://img.shields.io/badge/svgwrite-lightgrey?style=for-the-badge)

Core libs: `rembg` + `onnxruntime` (AI matting), `Pillow` (imaging), `vtracer` (Rust vectorizer), `scikit-image`/`scipy`/`numpy` (skeleton), `svgwrite` (SVG).

---

## 📄 License

MIT License — free for personal and commercial use.
