import os
import time
import subprocess
import shutil
from subprocess import DEVNULL

IMAGE_DIR = "/home/pi/solar-nowcasting/data/images"
os.makedirs(IMAGE_DIR, exist_ok=True)
time_interval = 10

def capture_photo():
    filename = f"sky_{time.strftime('%Y%m%d-%H%M%S')}.jpg" # Format: YearMonthDay-HourMinuteSecond
    filepath = os.path.join(IMAGE_DIR, filename)
    latest_image_path = os.path.join(IMAGE_DIR, "latest_capture.jpg")

    # rpicam-still: activate camera
    # --nopreview: no preview window
    # --immediate: no delay (for focus)
    cmd = f"rpicam-still -o {filepath} --nopreview --immediate"

    try:
        # subprocess.run: run command in terminal
        # stderr=DEVNULL, stdout=DEVNULL: send system logging (information) to DEVNULL (trash)
        subprocess.run(cmd, shell=True, check=True, stderr=DEVNULL, stdout=DEVNULL)
        shutil.copy(filepath, latest_image_path) # save latest image seperately (for stream)
        print(f"[{time.strftime('%H:%M:%S')}] Success: {filename} saved.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture failed: {e}")


if __name__ == "__main__":
    print(f"--- Capturing Images ({time_interval}s interval)---")
    print(f"Saving to: {os.path.abspath(IMAGE_DIR)}")
    print("Ctrl+C to stop image capture.")

    try:
        while True:
            capture_photo()
            time.sleep(time_interval)  # capture image every x seconds
    except KeyboardInterrupt:
        print("\nImaging stopped by user.")