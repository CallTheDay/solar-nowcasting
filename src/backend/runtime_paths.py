import os
import platform
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IS_RASPBERRY_PI = (
    PROJECT_ROOT == Path("/home/pi/solar-nowcasting")
    or platform.machine().lower().startswith(("arm", "aarch64"))
)
DATA_DIR = Path(os.environ.get("SOLAR_NOWCASTING_DATA_DIR", PROJECT_ROOT / "data"))
OUTPUT_DIR = DATA_DIR if IS_RASPBERRY_PI else DATA_DIR / "images"
CAPTURE_FOLDER = OUTPUT_DIR / "sky captures"
CAPTURE_PATH = CAPTURE_FOLDER / "latest_capture.jpg"
RESULT_FOLDER = OUTPUT_DIR / "detection results"
RESULT_PATH = RESULT_FOLDER / "latest_result.jpg"
STATS_PATH = DATA_DIR / "stats.json"
DEFAULT_DATASET_DIR = (
    DATA_DIR / "datasets" / "horizon" / "reversed_dataset"
)
MASK_FILENAME = "mask.png"
DASHBOARD_REFRESH_MS = 10000 if IS_RASPBERRY_PI else 500


def mask_path_for(image_directory):
    override = os.environ.get("SOLAR_NOWCASTING_MASK_PATH")
    if override:
        return Path(override)
    return Path(image_directory) / MASK_FILENAME
