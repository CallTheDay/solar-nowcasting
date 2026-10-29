# solar-nowcasting
Short-term cloud and PV power forecasting ('nowcasting') using a sky-facing camera on a Raspberry Pi. Visualization via a website with a simple GUI.

## Running on desktop or Raspberry Pi

Run `src/backend/main.py` and `src/frontend/app.py` with the interpreter for the machine you want to test. In an IDE, select the local interpreter/run configuration for desktop debugging or the SSH interpreter/run configuration for the Raspberry Pi. The program detects the runtime and uses that machine's data and output paths; both scripts must use the same runtime so the dashboard shows the results produced by the pipeline.

On the desktop, dataset mode defaults to `data/images/dataset1`, outputs go under `data/images`, and the dashboard polls every 500 ms. On the Raspberry Pi, dataset mode defaults to `data/datasets/horizon/reversed_dataset`, outputs go under `data`, and the dashboard polls every 10 seconds. Dataset navigation remains manual: press Space after each frame has finished processing. Live camera capture is available only on the Raspberry Pi.

Set `SOLAR_NOWCASTING_DATA_DIR` to override the data directory, or `SOLAR_NOWCASTING_MASK_PATH` to select a different cloud-detection mask.
