# Solar Nowcasting System Setup Guide

## System Overview

This system performs real-time solar nowcasting using a Raspberry Pi camera. It captures sky images, tracks cloud movement, estimates cloud trajectories, and predicts potential shading events on solar panels.

The system consists of:

* Camera capture and processing pipeline (`main.py`)
* Cloud detection and cloud tracking algorithms
* Solar position calculations
* Flask web dashboard (`app.py`)
* Offline dataset testing mode (`dataset_test.py`)

---

## Prerequisites

Before starting, ensure you have:

* Raspberry Pi with a compatible camera module installed
* Python 3.x
* Required Python dependencies installed
* SSH access enabled on the Raspberry Pi
* Network connectivity configured

---

## Installation and Configuration

### Step 1: Physical Installation

Install the Raspberry Pi camera module at your preferred location with view of the sky and pointing at some cardinal direction at an angle (not pointing directly upwards).

---
### Step 2: Remote Connection

Power on the Raspberry Pi and establish an SSH connection.

---

### Step 3: Create an Environment Mask

To prevent buildings, trees, windows, and other static objects from being detected as clouds:

1. Open a sample sky image (of current setup) in an image editor such as Photoshop or GIMP.
2. Paint all non-sky regions completely black (pixel value 0).
3. Leave all visible sky regions unchanged.
4. Save the resulting image as:

```text
/home/pi/solar-nowcasting/data/sky_captures/mask.png
```

---

### Step 4: Configure the System

Open `config.py` and enter the required configuration values.

| Variable  | Description                                   | Example |
| --------- | --------------------------------------------- | ------- |
| Azimuth   | Horizontal compass heading of the camera      | 270.0   |
| Tilt      | Vertical angle above the horizon              | 25.0    |
| Latitude  | Geographic latitude of the installation site  | 51.5074 |
| Longitude | Geographic longitude of the installation site | -0.1278 |

**Notes:**

* Azimuth and tilt are required for accurate solar tracking calculations.
* Geographic coordinates are currently only used by `sun_position.py`.
* `sun_position.py` is not yet fully integrated into the main processing pipeline and is primarily used for testing purposes.

---

## Running the System

## Running on desktop or Raspberry Pi

Run `src/backend/main.py` and `src/frontend/app.py` with the interpreter for the machine you want to test. In an IDE, select the local interpreter/run configuration for desktop debugging or the SSH interpreter/run configuration for the Raspberry Pi.

### Step 5: Start the Web Dashboard

Launch the Flask web server:

```bash
python3 app.py
```

Open a web browser and navigate to:

```text
http://localhost:8000
```

---

### Step 6: Launch the Processing Pipeline

In a separate terminal window, start the primary processing loop:

```bash
python3 main.py
```

This begins:

* Image capture
* Solar tracking
* Cloud detection
* Cloud movement analysis

#### Offline Testing Mode

Alternatively, you can run:

```bash
python3 dataset_test.py
```

This uses a previously captured dataset of sky images instead of live camera input, making testing and experimentation easier.

#### Evaluating detected cloud shapes

From the project root, run:

```bash
python src/eval/detection_evaluation.py
```

The evaluator processes each non-`_bin` image in `data/datasets/evaluation/binary`, uses its matching `_mask` image as the detector's sky mask, and compares the detected cloud mask with the matching `_bin` ground-truth image. Masks can be named either `<image>_mask` or `<image>_bin_mask`. When ground-truth clouds are present, the detected-cloud percentage is the fraction of white ground-truth cloud pixels detected inside the mask's white (valid) area; the missed percentage is the remainder. False positives (detected cloud pixels outside ground-truth clouds) are also reported as a count and percentage of valid area, including cloudless images. Black mask pixels are excluded from all metrics. If the mask contains no valid pixels, the evaluator displays the image with scores marked N/A rather than stopping. The view shows the detected cloud outline over the original image, the detected mask, and `_bin` ground truth side by side. Use the left/right arrow keys to navigate and `Q`/`Esc` to quit. Use `--input-dir` to evaluate another folder with the same image-pair naming convention.

#### Scoring shade forecasts against the light sensor

To replay a captured dataset and measure how closely its shade-onset forecast matched the light sensor, run from the project root:

```bash
python evaluation/evaluate.py data/datasets/ground_truth/31_10_Abend --lux-threshold 400
```

Set `--lux-threshold` to the lux level that represents shade for the sensor and installation. An onset is the first reading at or below that threshold after a reading above it; by default it must remain below threshold for two consecutive samples (`--confirm-samples`). For each observed onset, the evaluator scores the latest numeric shade ETA issued since the previous onset. A forecast is accurate when its predicted onset is within 60 seconds of the measured onset (`--tolerance-seconds`).

The JSON summary, per-onset event CSV, and replayed forecast CSV are written to `evaluation/results/`. The timing accuracy percentage counts missed shade events as inaccurate; mean absolute timing error is calculated for events that had a forecast. A dataset with no threshold crossing is reported as not scorable. This first metric focuses on timing observed shade-onset events; forecasts that predict shade when no onset occurs are not yet scored as false alarms.

---

## Dashboard Outputs

### Step 7: Monitor Results

The dashboard updates every 10 seconds and displays:

* Live sky captures
* Visualization of detected shapes and readings
* Sky condition classifications
* Wind direction estimates
* Shade ETA predictions
* Image timestamps

---

## Shade ETA Assumptions

The current implementation assumes that the solar panels are located at the same position as the camera.

A cloud is considered capable of shading the solar panels when its projected path intersects the top edge of the captured image.

Clouds whose projected trajectories do not intersect this region are ignored.

Based on detected cloud motion, the system estimates when an intersecting cloud will reach the shading zone and displays the resulting Shade ETA.
