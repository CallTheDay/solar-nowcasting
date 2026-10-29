import json
import os
import shutil
import sys
import time
import cv2
import image_capture
import cloud_detection
import config
import runtime_paths

CAPTURE_FOLDER = str(runtime_paths.CAPTURE_FOLDER)
CAPTURE_PATH = str(runtime_paths.CAPTURE_PATH)
RESULT_FOLDER = str(runtime_paths.RESULT_FOLDER)
RESULT_PATH = str(runtime_paths.RESULT_PATH)
STATS_PATH = str(runtime_paths.STATS_PATH)
DEFAULT_DATASET_DIR = str(runtime_paths.DEFAULT_DATASET_DIR)
SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def choose_mode():
    while True:
        mode = input("Choose input: [l]ive camera or [d]ataset: ").strip().lower()
        if mode in ("l", "live"):
            return "live"
        if mode in ("d", "dataset"):
            return "dataset"
        print("Please enter 'l' for live camera or 'd' for dataset.")


def choose_dataset_folder():
    folder = input(f"Dataset folder [{DEFAULT_DATASET_DIR}]: ").strip()
    return folder or DEFAULT_DATASET_DIR


def clean_live_output_folders():
    for folder in (CAPTURE_FOLDER, RESULT_FOLDER):
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if "latest_capture" not in filename and "mask" not in filename and "latest_result" not in filename:
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Failed to delete {file_path}: {e}")
            print(f"Cleared historical images in: {folder}")


def publish_results(img_raw, frame_label, mask_path):
    wind_dir, sky_cond, shade_eta = cloud_detection.process_cloud_tracking(
        img_raw, RESULT_PATH, str(mask_path)
    )
    stats_data = {
        "wind_direction": wind_dir if wind_dir else "Calculating...",
        "sky_condition": sky_cond if sky_cond else "Analyzing...",
        "shade_eta": shade_eta if shade_eta else "Clear",
        "last_update": time.strftime("%H:%M:%S")
    }
    os.makedirs(os.path.dirname(STATS_PATH), exist_ok=True)
    with open(STATS_PATH, "w") as stats_file:
        json.dump(stats_data, stats_file)
    print(f"Dashboard updated for {frame_label}.")


def wait_for_dataset_key():
    print("Press SPACE for the next image or 'q' to quit.", end="", flush=True)

    if os.name == "nt":
        import msvcrt

        while True:
            try:
                key = msvcrt.getwch().lower()
            except OSError as error:
                raise RuntimeError(
                    "This PyCharm console cannot read standalone keypresses. "
                    "Enable 'Emulate terminal in output console' in the run configuration."
                ) from error
            if key == " ":
                print()
                return True
            if key == "q":
                print()
                return False
    else:
        import termios
        import tty

        if not sys.stdin.isatty():
            raise RuntimeError(
                "Dataset navigation needs a terminal. Run this in an interactive terminal."
            )

        terminal_fd = sys.stdin.fileno()
        previous_settings = termios.tcgetattr(terminal_fd)
        try:
            tty.setcbreak(terminal_fd)
            while True:
                key = os.read(terminal_fd, 1).decode(errors="ignore").lower()
                if key == " ":
                    print()
                    return True
                if key == "q":
                    print()
                    return False
        finally:
            termios.tcsetattr(terminal_fd, termios.TCSADRAIN, previous_settings)


def run_live_pipeline():
    if not runtime_paths.IS_RASPBERRY_PI:
        raise RuntimeError("Live camera capture is only available when running on the Raspberry Pi.")

    print("Starting live image capture...")
    clean_live_output_folders()
    while True:
        start_time = time.time()
        try:
            print("\n--- New Frame Cycle ---")
            captured_data = image_capture.capture_photo(CAPTURE_PATH)
            if captured_data is not None:
                raw_img, _history_path = captured_data
                if raw_img is not None:
                    mask_path = runtime_paths.mask_path_for(CAPTURE_FOLDER)
                    publish_results(raw_img, "live capture", mask_path)
        except Exception as e:
            print(f"Error in pipeline cycle: {e}")

        elapsed = time.time() - start_time
        sleep_time = max(0.1, config.time_interval - elapsed)
        time.sleep(sleep_time)


def run_dataset(dataset_dir):
    if not os.path.isdir(dataset_dir):
        raise FileNotFoundError(f"Dataset directory does not exist: {dataset_dir}")

    dataset_images = sorted(
        [
            filename for filename in os.listdir(dataset_dir)
            if filename.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)
            and "mask" not in filename.lower()
            and os.path.isfile(os.path.join(dataset_dir, filename))
        ],
    )

    if not dataset_images:
        raise FileNotFoundError(f"No supported images found in dataset directory: {dataset_dir}")

    os.makedirs(CAPTURE_FOLDER, exist_ok=True)
    print(f"Starting dataset playback: {dataset_dir}")
    print("Each image is fully analyzed before navigation is enabled.")

    for index, filename in enumerate(dataset_images, start=1):
        image_path = os.path.join(dataset_dir, filename)
        print(f"\n--- Image {index}/{len(dataset_images)}: {filename} ---")
        raw_img = cv2.imread(image_path)
        if raw_img is None:
            raise RuntimeError(f"Could not read dataset image: {image_path}")

        shutil.copyfile(image_path, CAPTURE_PATH)
        mask_path = runtime_paths.mask_path_for(dataset_dir)
        publish_results(raw_img, filename, mask_path)
        if index < len(dataset_images) and not wait_for_dataset_key():
            print("Dataset playback stopped.")
            return

    print("Dataset playback finished.")


def main_pipeline():
    runtime = "Raspberry Pi" if runtime_paths.IS_RASPBERRY_PI else "Desktop"
    print(f"Solar Nowcasting ({runtime} runtime)")
    mode = choose_mode()
    if mode == "live":
        run_live_pipeline()
    else:
        dataset_dir = choose_dataset_folder()
        run_dataset(dataset_dir)


if __name__ == "__main__":
    main_pipeline()