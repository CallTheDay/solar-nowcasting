import os
import time
import subprocess
import shutil
import cv2
import csv
from subprocess import DEVNULL
import runtime_paths
import board
import adafruit_tsl2591

IMAGE_DIR = str(runtime_paths.CAPTURE_FOLDER)
CSV_PATH = os.path.join(IMAGE_DIR, "light_log.csv")

# Initialize sensor once
i2c = board.I2C()
sensor = adafruit_tsl2591.TSL2591(i2c)
sensor.gain = adafruit_tsl2591.GAIN_LOW  # low gain for very bright light conditions ------------
sensor.integration_time = adafruit_tsl2591.INTEGRATIONTIME_100MS

# Ensure CSV header exists
os.makedirs(IMAGE_DIR, exist_ok=True)
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "timestamp", "lux", "full_spectrum", "ir"])

def capture_photo(target_latest_path=None):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    filename = f"sky_{time.strftime('%Y%m%d-%H%M%S')}.jpg"  # Format: YearMonthDay-HourMinuteSecond
    filepath = os.path.join(IMAGE_DIR, filename)

    if target_latest_path is None:
        target_latest_path = os.path.join(IMAGE_DIR, "latest_capture.jpg")

    # rpicam-still: activate camera
    # --nopreview: no preview window
    # --immediate: no delay (for focus)
    cmd = f"rpicam-still -o '{filepath}' --nopreview --immediate"

    try:
        # Read sensor data right before capture
        lux = sensor.lux
        full_spectrum = sensor.full_spectrum
        ir = sensor.infrared
        timestamp = time.time()

        # subprocess.run: run command in terminal
        # stderr=DEVNULL, stdout=DEVNULL: send system logging (information) to DEVNULL (trash)
        subprocess.run(cmd, shell=True, check=True, stderr=DEVNULL, stdout=DEVNULL)

        os.makedirs(os.path.dirname(target_latest_path), exist_ok=True)
        shutil.copy(filepath, target_latest_path)  # overwrite latest_capture

        # Append metadata to CSV
        with open(CSV_PATH, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([filename, timestamp, lux, full_spectrum, ir])

        print(f"[{time.strftime('%H:%M:%S')}] Success: {filename} saved. Lux: {lux:.2f}")

        img_raw = cv2.imread(target_latest_path)
        if img_raw is not None:
            img_raw = cv2.rotate(img_raw, cv2.ROTATE_180)  # rotate image (because camera is upside down)
            cv2.imwrite(filepath, img_raw)
            cv2.imwrite(target_latest_path, img_raw)

        return img_raw, filepath
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Capture failed: {e}")
        return None, None