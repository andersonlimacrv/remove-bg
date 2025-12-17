from pathlib import Path
from datetime import datetime
import shutil


def today_folder() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def ensure_dirs(base: Path):
    (base / "images").mkdir(exist_ok=True)
    (base / "originals").mkdir(exist_ok=True)
    (base / "no-bg").mkdir(exist_ok=True)


def move_original(image_path: Path, base: Path) -> Path:
    date = today_folder()
    target_dir = base / "originals" / date
    target_dir.mkdir(parents=True, exist_ok=True)

    target = target_dir / image_path.name
    shutil.move(str(image_path), target)
    return target


def output_no_bg_name(original_name: str) -> str:
    stem = Path(original_name).stem
    return f"{stem}_NO_BG.png"


def no_bg_output_path(base: Path, original_name: str) -> Path:
    date = today_folder()
    target_dir = base / "no-bg" / date
    target_dir.mkdir(parents=True, exist_ok=True)

    return target_dir / output_no_bg_name(original_name)


