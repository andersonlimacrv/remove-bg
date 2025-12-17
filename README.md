# 🖼️ remove-bg

A clean and script-friendly Python tool to remove image backgrounds automatically or using forced strategies.

Designed for batch processing with clear logs, organized folders and zero cloud dependency.

---

## ✨ Features

- 🧠 **Automatic strategy selection** (default)
- 🤖 AI-based background removal (rembg)
- 🎨 Fast color-based removal for solid backgrounds
- 📂 Automatic folder organization by date
- 🧼 Input folder is cleaned after processing
- 🖥️ Verbose and friendly terminal output with emojis
- 📦 Managed with Poetry

---

## 📁 Project Structure

```text
remove-bg/
├── app/
│   ├── fs.py
│   ├── processor.py
│   ├── main.py
│   └── __init__.py
├── images/                 # Drop images here
├── originals/
│   └── YYYY-MM-DD/         # Archived original images
├── no-bg/
│   └── YYYY-MM-DD/         # Processed images (no background)
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
   * Keep the `images/` folder clean

---

## 🧰 Requirements

* Python **3.13+**
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

## 🧠 AUTO Strategy Explained

In AUTO mode, the tool:

1. Samples pixels from the image
2. Detects if the background is mostly white
3. Chooses:

   * 🎨 COLOR strategy for solid backgrounds
   * 🤖 AI strategy for complex backgrounds

This improves performance and avoids unnecessary AI processing.

---

## 🧪 Supported Formats

* PNG
* JPG / JPEG
* WEBP

---

## 🛠️ Tech Stack

* Python
* Poetry
* Pillow
* rembg

---

## 📄 License

MIT License — free for personal and commercial use.

