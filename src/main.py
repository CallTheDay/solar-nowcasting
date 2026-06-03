import time
import os
import json
import image_capture
import cloud_detection

CAPTURE_PATH = "/home/pi/solar-nowcasting/data/sky captures/latest_capture.jpg"
RESULT_PATH = "/home/pi/solar-nowcasting/data/detection results/latest_result.jpg"

# NOTE: main only runs image capture and tracking. for visualization, run app.py seperately
def main_pipeline():
    print("Starting Solar Nowcasting Main Loop...")

    # Clear old historical images on startup to prevent disk space filling up
    folders_to_clean = [
        "/home/pi/solar-nowcasting/data/sky captures",
        "/home/pi/solar-nowcasting/data/detection results"
    ]

    for folder in folders_to_clean:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # Keep mask file and latest_capture/result intact
                if "latest_capture" not in filename and "mask" not in filename and "latest_result" not in filename:
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
            print(f"Cleared historical images in: {folder}")

    while True:
        try:
            print("\n--- New Frame Cycle ---")

            # capture image and save it to CAPTURE_PATH
            captured_data = image_capture.capture_photo(CAPTURE_PATH)

            if captured_data is not None:
                raw_img, history_path = captured_data

                if raw_img is not None:
                    # cloud tracking results
                    wind_dir, sky_cond = cloud_detection.process_cloud_tracking(raw_img, RESULT_PATH)
                    # save data points to JSON file
                    stats_data = {
                        "wind_direction": wind_dir if wind_dir else "Calculating...",
                        "sky_condition": sky_cond if sky_cond else "Analyzing...",
                        "last_update": time.strftime("%H:%M:%S")
                    }
                    with open("/home/pi/solar-nowcasting/data/stats.json", "w") as f:
                        json.dump(stats_data, f)
                    print("Dashboard feeds synchronized successfully.")

        except Exception as e:
            print(f"Error in pipeline cycle: {e}")

        # execution frequency
        time.sleep(10)

if __name__ == "__main__":
    main_pipeline()