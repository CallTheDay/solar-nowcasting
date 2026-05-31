import os
import cv2
import datetime
import numpy as np
from pysolar.solar import get_altitude, get_azimuth


def sun_tracker_view(image_folder, cam_azi, cam_alt, hfov=65):
    extensions = ('.jpg', '.png', '.jpeg')
    filenames = [f for f in os.listdir(image_folder) if f.lower().endswith(extensions) and f.lower() != 'mask.png']
    filenames.sort()

    if not filenames:
        print("No images found.")
        return

    lat, lon = 0.0, 0.0  # Coordinates of camera (must be exact position)
    i = 0

    while i < len(filenames):
        img_path = os.path.join(image_folder, filenames[i])
        img = cv2.imread(img_path)
        if img is None:
            i += 1
            continue

        try:
            time_str = filenames[i].split('_')[1].split('.')[0]
            dt = datetime.datetime.strptime(time_str, "%Y%m%d-%H%M%S")
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        except Exception as e:
            print(f"Error parsing time: {e}")
            i += 1
            continue

        sun_alt = get_altitude(lat, lon, dt)
        sun_azi = get_azimuth(lat, lon, dt)

        h, w = img.shape[:2]
        px_per_deg = w / hfov
        center_x, center_y = w // 2, h // 2

        delta_azi = (sun_azi - cam_azi + 180) % 360 - 180
        delta_alt = sun_alt - cam_alt

        # sun coordinates
        sun_x = int(center_x + (delta_azi * px_per_deg))
        sun_y = int(center_y - (delta_alt * px_per_deg))

        # arrow logic (visualization)
        margin = 10  # Keep arrow tip away edge of screen
        target_x = np.clip(sun_x, margin, w - margin)
        target_y = np.clip(sun_y, margin, h - margin)
        cv2.arrowedLine(img, (center_x, center_y), (target_x, target_y), (0, 0, 0), 5, tipLength=0.1)

        cv2.putText(img, f"SUN: {sun_azi:.1f} Az / {sun_alt:.1f} Al", (20, 40), 1, 1.2, (0, 255, 255), 2)

        save_path = "/home/pi/solar-nowcasting/data/test/latest_capture.jpg"
        cv2.imwrite(save_path, img)
        print(f"Processed and saved {filenames[i]} as latest_capture.jpg")
        del img

        # navigation for going through dataset (for debugging)
        cmd = input("Controls: [Enter] Next | [b] Back | [q] Quit: ").lower().strip()

        if cmd == 'q':
            print("Closing detection...")
            break
        elif cmd == 'b':
            i = max(i - 1, 0)
            print(f"Moving back to: {filenames[i]}")
        else:
            i = min(i + 1, len(filenames) - 1)
            if i == len(filenames) - 1:
                print("End of dataset reached.")


if __name__ == "__main__":
    folder_path = "/home/pi/solar-nowcasting/data/sun detection test"  # Path of image dataset

    # Camera parameters must be measured exactly
    MY_CAM_AZIMUTH = 299.0  # left right
    MY_CAM_ALTITUDE = 9.0  # up down

    sun_tracker_view(folder_path, MY_CAM_AZIMUTH, MY_CAM_ALTITUDE)
