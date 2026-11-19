import argparse
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "src" / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import cloud_detection_original


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff"}
DETECTION_SIZE = (648, 486)

# Evaluation script for comparing detected cloud shapes with ground-truth binary masks.
# UI Shows the original image, detected cloud mask, and ground-truth mask side by side, as well as
# percentage of ground-truth clouds detected, missed, and false positives.
def find_image_pairs(input_dir):
    pairs = []
    for image_path in sorted(input_dir.iterdir()):
        if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if image_path.stem.lower().endswith(("_bin", "_mask")):
            continue

        ground_truth_path = image_path.with_name(
            f"{image_path.stem}_bin{image_path.suffix}"
        )
        if not ground_truth_path.is_file():
            print(f"Skipping {image_path.name}: missing {ground_truth_path.name}")
            continue
        pairs.append((image_path, ground_truth_path))
    return pairs


def find_mask_path(image_path, ground_truth_path):
    mask_path = image_path.with_name(f"{image_path.stem}_mask{image_path.suffix}")
    if mask_path.is_file():
        return mask_path

    ground_truth_mask_path = ground_truth_path.with_name(
        f"{ground_truth_path.stem}_mask{ground_truth_path.suffix}"
    )
    if ground_truth_mask_path.is_file():
        return ground_truth_mask_path

    raise FileNotFoundError(
        f"No mask found for {image_path.name}; expected {mask_path.name} "
        f"(or {ground_truth_mask_path.name})"
    )


def load_binary_mask(image_path, size):
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")
    if (image.shape[1], image.shape[0]) != size:
        image = cv2.resize(image, size, interpolation=cv2.INTER_NEAREST)
    return cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)[1]


def make_comparison(
    original_image, detected_mask, ground_truth_mask, evaluation_mask,
    image_name, index, total,
):
    valid_pixels = cv2.countNonZero(evaluation_mask)
    valid_ground_truth_clouds = cv2.bitwise_and(ground_truth_mask, evaluation_mask)
    ground_truth_cloud_pixels = cv2.countNonZero(valid_ground_truth_clouds)
    valid_detected_clouds = cv2.bitwise_and(detected_mask, evaluation_mask)

    if valid_pixels == 0:
        metric_text = "No valid pixels in mask  |  Score: N/A"
        false_positive_text = "False positives: N/A"
        console_text = "no valid pixels in mask; score unavailable"
    else:
        false_positive_mask = cv2.bitwise_and(
            valid_detected_clouds, cv2.bitwise_not(valid_ground_truth_clouds)
        )
        false_positive_pixels = cv2.countNonZero(false_positive_mask)
        false_positive_percent = false_positive_pixels * 100.0 / valid_pixels
        false_positive_text = (
            f"False positives: {false_positive_pixels} pixels "
            f"({false_positive_percent:.2f}% of valid area)"
        )

        if ground_truth_cloud_pixels:
            detected_cloud_pixels = cv2.countNonZero(
                cv2.bitwise_and(detected_mask, valid_ground_truth_clouds)
            )
            detected_percent = detected_cloud_pixels * 100.0 / ground_truth_cloud_pixels
            missed_percent = 100.0 - detected_percent
            metric_text = (
                f"Ground-truth clouds detected: {detected_percent:.2f}%  |  "
                f"Missed: {missed_percent:.2f}%"
            )
            console_text = (
                f"{detected_percent:.2f}% of ground-truth clouds detected, "
                f"{missed_percent:.2f}% missed; {false_positive_pixels} false-positive "
                f"pixels ({false_positive_percent:.2f}% of valid area)"
            )
        else:
            metric_text = "No ground-truth clouds"
            console_text = (
                f"no ground-truth clouds; {false_positive_pixels} false-positive "
                f"pixels ({false_positive_percent:.2f}% of valid area)"
            )

    width, height = DETECTION_SIZE
    header_height = 132
    panel = np.zeros((height + header_height, width * 3, 3), dtype=np.uint8)
    original_with_outline = cv2.resize(
        original_image, DETECTION_SIZE, interpolation=cv2.INTER_AREA
    )
    contours, _ = cv2.findContours(
        detected_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    cv2.drawContours(original_with_outline, contours, -1, (0, 255, 0), 2)
    panel[header_height:, :width] = original_with_outline
    panel[header_height:, width:width * 2] = cv2.cvtColor(detected_mask, cv2.COLOR_GRAY2BGR)
    panel[header_height:, width * 2:] = cv2.cvtColor(ground_truth_mask, cv2.COLOR_GRAY2BGR)

    cv2.putText(panel, image_name, (12, 24), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(panel, metric_text,
                (12, 53), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(panel, false_positive_text, (12, 78), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(panel, f"Image {index + 1}/{total}  |  Left/Right arrows: navigate  |  Q/Esc: quit",
                (12, 103), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
    cv2.putText(panel, "Detected outline", (12, 125), cv2.FONT_HERSHEY_SIMPLEX,
                0.55, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(panel, "Detected", (width + 12, 125),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
    cv2.putText(panel, "Ground truth", (width * 2 + 12, 125),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
    return panel, console_text


def get_navigation_action(key):
    if key in (ord("q"), ord("Q"), 27):
        return "quit"
    if key in (2424832, 65361):
        return "previous"
    if key in (2555904, 65363):
        return "next"
    return None


def evaluate(input_dir):
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Evaluation folder does not exist: {input_dir}")

    image_pairs = find_image_pairs(input_dir)
    if not image_pairs:
        raise FileNotFoundError(f"No images with matching *_bin ground truth found in {input_dir}")

    with tempfile.TemporaryDirectory(prefix="cloud_detection_evaluation_") as temp_dir:
        result_path = Path(temp_dir) / "detection_result.jpg"
        window_name = "Cloud detection evaluation"
        index = 0
        try:
            while 0 <= index < len(image_pairs):
                image_path, ground_truth_path = image_pairs[index]
                mask_path = find_mask_path(image_path, ground_truth_path)
                image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
                if image is None:
                    raise ValueError(f"Could not read image: {image_path}")

                cloud_detection_original.reset_tracking_state()
                _, _, _, detected_mask = cloud_detection_original.process_cloud_tracking(
                    image,
                    str(result_path),
                    str(mask_path),
                    return_cloud_mask=True,
                )
                detected_mask = cv2.resize(
                    detected_mask, DETECTION_SIZE, interpolation=cv2.INTER_NEAREST
                )
                ground_truth_mask = load_binary_mask(ground_truth_path, DETECTION_SIZE)
                evaluation_mask = load_binary_mask(mask_path, DETECTION_SIZE)
                comparison, metric_summary = make_comparison(
                    image, detected_mask, ground_truth_mask, evaluation_mask,
                    image_path.name, index, len(image_pairs),
                )

                print(
                    f"[{index + 1}/{len(image_pairs)}] {image_path.name}: {metric_summary}"
                )
                cv2.imshow(window_name, comparison)
                action = get_navigation_action(cv2.waitKeyEx(0))
                if action == "quit":
                    break
                if action == "previous":
                    index = max(0, index - 1)
                elif action == "next":
                    index = min(len(image_pairs) - 1, index + 1)
        finally:
            cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(
        description="Compare detected cloud shapes with matching *_bin ground-truth images."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "datasets" / "evaluation" / "binary",
        help="Folder containing source images and their *_bin ground truth images.",
    )
    args = parser.parse_args()
    evaluate(args.input_dir.resolve())


if __name__ == "__main__":
    main()