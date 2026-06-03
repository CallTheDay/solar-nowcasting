import os
import time
import subprocess
import shutil
import cv2
from subprocess import DEVNULL

IMAGE_DIR = "/home/pi/solar-nowcasting/data/sky captures"
os.makedirs(IMAGE_DIR, exist_ok=True)

def capture_photo(target_latest_path=None):
    filename = f"sky_{time.strftime('%Y%m%d-%H%M%S')}.jpg"  # Format: YearMonthDay-HourMinuteSecond
    filepath = os.path.join(IMAGE_DIR, filename)

    if target_latest_path is None:
        target_latest_path = os.path.join(IMAGE_DIR, "latest_capture.jpg")

    # rpicam-still: activate camera
    # --nopreview: no preview window
    # --immediate: no delay (for focus)
    cmd = f"rpicam-still -o '{filepath}' --nopreview --immediate"

    try:
        # subprocess.run: run command in terminal
        # stderr=DEVNULL, stdout=DEVNULL: send system logging (information) to DEVNULL (trash)
        subprocess.run(cmd, shell=True, check=True, stderr=DEVNULL, stdout=DEVNULL)

        os.makedirs(os.path.dirname(target_latest_path), exist_ok=True)
        shutil.copy(filepath, target_latest_path)  # overwrite latest_capture
        print(f"[{time.strftime('%H:%M:%S')}] Success: {filename} saved.")

        img_raw = cv2.imread(target_latest_path)
        return img_raw, filepath
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture failed: {e}")
        return None, None


# for testing/debugging
if __name__ == "__main__":
    print(f"capturing test image")
    print(f"Saving history to: {os.path.abspath(IMAGE_DIR)}")
    capture_photo()