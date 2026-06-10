import os
import json
import cv2
import cloud_detection

# Path setup
DATASET_DIR = "/home/pi/solar-nowcasting/data/dataset3"
RESULT_PATH = "/home/pi/solar-nowcasting/data/detection results/latest_result.jpg"
STATS_FILE = "/home/pi/solar-nowcasting/data/stats.json"

def main_dataset_test():
    print("Starting Dataset Test Loop...")
    print("Press ENTER in this terminal window to load the next frame. Type 'q' and press Enter to quit.\n")

    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset directory {DATASET_DIR} does not exist.")
        return

    supported_extensions = (".jpg", ".jpeg", ".png")
    dataset_images = sorted([
        f for f in os.listdir(DATASET_DIR)
        if f.lower().endswith(supported_extensions) and "mask" not in f.lower()
    ], reverse=False)

    if not dataset_images:
        print("No test images found in the dataset folder.")
        return

    # simulated timeline
    simulated_seconds = 0

    for filename in dataset_images:
        img_path = os.path.join(DATASET_DIR, filename)
        print(f"--- Processing Frame: {filename} ---")

        raw_img = cv2.imread(img_path)

        if raw_img is not None:
            wind_dir, sky_cond, shade_eta = cloud_detection.process_cloud_tracking(raw_img, RESULT_PATH)

            # 10 simulated seconds per frame
            simulated_seconds += 10
            hours = (simulated_seconds // 3600) % 24
            minutes = (simulated_seconds // 60) % 60
            seconds = simulated_seconds % 60
            simulated_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            stats_data = {
                "wind_direction": wind_dir if wind_dir else "Calculating...",
                "sky_condition": sky_cond if sky_cond else "Analyzing...",
                "shade_eta": shade_eta if shade_eta else "Clear",
                "last_update": simulated_time_str
            }
            with open(STATS_FILE, "w") as f:
                json.dump(stats_data, f)

            print(f"Frame {filename} processed. View updates on your Flask Dashboard.")

            user_input = input("Press ENTER for next frame (or 'q' to quit): ").strip().lower()
            print("-" * 40)
            if user_input == 'q':
                print("Exiting test loop.")
                break
        else:
            print(f"Failed to load image: {filename}")

    print("Dataset playback finished.")


if __name__ == "__main__":
    main_dataset_test()