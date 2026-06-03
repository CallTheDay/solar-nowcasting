# Solar Nowcasting System Setup Guide

Follow these steps to configure and run the solar nowcasting and cloud tracking software.

## Setup Instructions

### Step 1: Physical Installation
Set up the Raspberry Pi camera module at your preferred location with a clear view of the sky.

### Step 2: Create an Environment Mask
If any buildings, trees, or windows are visible in the frame, you must mask them out to avoid false cloud detections.
* Open a sample capture in image editing software (Photoshop, GIMP, etc.).
* Paint all non-sky parts completely **black** (Pixel value 0).
* Leave the open sky area untouched.
* Save the image as a PNG file here: `/home/pi/solar-nowcasting/data/sky captures/mask.png`

### Step 3: Measure Camera Metrics
Note down the following physical measurements of your camera setup:
* **Azimuth:** The horizontal compass heading the camera points toward (e.g., 270.0 for W).
* **Tilt:** The vertical angle the camera points up into the sky from the flat horizon (e.g., 25.0 degrees).

### Step 4: Remote Connection
Power on the Raspberry Pi and establish a connection via SSH.

### Step 5: Configure the System
Open the `config.py` file and input your specific geographic and hardware variables. This ensures accurate solar tracking calculations.

### Step 6: Start the Web Dashboard
Launch the Flask web server application by running `python3 app.py` in your terminal. Open a web browser and navigate to `http://localhost:8000` to view the UI.

### Step 7: Launch the Pipeline
Run the primary processing loop by running `python3 main.py` in a separate terminal window to start image capture, solar tracking, and cloud movement analytics.

### Step 8: Monitor Results
The dashboard updates dynamically every 10 seconds to display the live raw sky captures alongside processed cloud detection masks. It will feature the real-time Sky Condition classifications, Wind Direction headings, and image timestamps.