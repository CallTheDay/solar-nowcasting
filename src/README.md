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
