import os
import time
import subprocess
from subprocess import DEVNULL

SAVE_DIR = "../data/images"
os.makedirs(SAVE_DIR, exist_ok=True)
time_interval = 10

def capture_photo():
    timestamp = time.strftime("%Y%m%d-%H%M%S") # Format: YearMonthDay-HourMinuteSecond
    filename = f"sky_{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)

    # rpicam-still: activate camera
    # --nopreview: no preview window
    # --immediate: no delay (for focus)
    cmd = f"rpicam-still -o {filepath} --nopreview --immediate"

    try:
        # subprocess.run: run command in terminal
        # stderr=DEVNULL, stdout=DEVNULL: send system logging (information) to DEVNULL (trash)
        subprocess.run(cmd, shell=True, check=True, stderr=DEVNULL, stdout=DEVNULL)
        print(f"[{time.strftime('%H:%M:%S')}] Success: {filename} saved.")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture failed: {e}")


if __name__ == "__main__":
    print(f"--- Capturing Images ({time_interval}s interval)---")
    print(f"Saving to: {os.path.abspath(SAVE_DIR)}")
    print("Ctrl+C to stop image capture.")

    try:
        while True:
            capture_photo()
            time.sleep(time_interval)  # capture image every x seconds
    except KeyboardInterrupt:
        print("\nImaging stopped by user.")