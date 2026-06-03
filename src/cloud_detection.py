import os
import cv2
import numpy as np
import gc
import config

# persistent historical tracking between function calls
movement_history = []
accumulated_movements = {}
prev_centers = []
avg_rb_mask = None
mask_binary = None
clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))


def get_cardinal_direction(degrees):
    # Converts degrees (0-360) to a cardinal string.
    degrees = degrees % 360
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((degrees + 22.5) / 45) % 8
    return directions[idx]


def process_cloud_tracking(img_raw, save_path_newest):
    global movement_history, accumulated_movements, prev_centers, avg_rb_mask, mask_binary, clahe

    min_frames_required = config.MIN_FRAMES_REQUIRED  # Wait for at least this many frame transitions before global wind reading

    w, h = 648, 486  # images are resized to fixed dimension to reduce ram usage (1/4th of camera resolution)
    image_dimensions = (w, h)

    if img_raw is None:
        return "Unknown", "Unknown"

    # resize image if it doesnt match the target tracking dimensions
    if img_raw.shape[1] != w or img_raw.shape[0] != h:
        img_raw = cv2.resize(img_raw, image_dimensions, interpolation=cv2.INTER_AREA)

    # Lighting settings-----------------------------------------------
    # CLAHE (Contrast Limited Adaptive Histogram Equalization): locally enhances cloud contrast to handle global lighting shifts
    if avg_rb_mask is None:
        print("Attempting to allocate memory buffers...")
        avg_rb_mask = np.zeros((h, w), dtype=np.float32)
        print("Memory buffers allocated.")

    if mask_binary is None:
        # Mask Setup (to remove buildings etc.)
        mask_path = "/home/pi/solar-nowcasting/data/sky captures/mask.png"
        mask_raw = cv2.imread(mask_path)

        if mask_raw is not None:
            mask_gray = cv2.cvtColor(mask_raw, cv2.COLOR_BGR2GRAY)
            mask_binary = cv2.threshold(mask_gray, 1, 255, cv2.THRESH_BINARY)[1]
            mask_binary = cv2.resize(mask_binary, image_dimensions, interpolation=cv2.INTER_NEAREST)
        else:
            print("Using default white mask")
            mask_binary = np.full((h, w), 255, dtype=np.uint8)
        print("Mask loaded and resized")

    # Finetuning Parameters
    alpha = 0.8  # prevent shape jumps (1.0 = no prevention, 0.1 = high prevention)
    morph_k = np.ones((15, 15), np.uint8)  # Noise removal
    gc.collect()

    # NRBR Feature Extraction-----------------------------------------
    """
    NRBR = Normalized red blue ratio
    Clear sky reflects mostly blue light, while clouds reflect red and blue light equally. 
    Comparing color channels make separating clouds easier.
    Red and blue parts of picture are extracted.
    """
    blue_channel, green_channel, red_channel = cv2.split(img_raw)
    # only converting red and blue
    b = blue_channel.astype(np.float32)
    r = red_channel.astype(np.float32)
    # Clean up to free RAM
    del blue_channel, green_channel, red_channel  # freeing up memory space

    # 1e-6 is failsafe of div/0 (in case a pixel is perfectly black)
    r_b_feature = np.clip(r / (b + 1e-6), 0.4, 1.6)
    # transform decimals back to 0-255 ratio
    rb_norm = cv2.normalize(r_b_feature, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    del r, b, r_b_feature

    rb_masked = cv2.bitwise_and(rb_norm, rb_norm, mask=mask_binary)
    del rb_norm

    # enhance contrast (clahe)
    rb_clahe = clahe.apply(rb_masked)
    del rb_masked

    # cloud threshold (finetuning)
    _, rb_thresh_raw = cv2.threshold(rb_clahe, 120, 255, cv2.THRESH_BINARY)
    del rb_clahe

    # Sky condition measurement (cloudy, clear etc.) ---------------------------------
    valid_sky_mask = cv2.inRange(mask_binary, 1, 255)
    total_sky_pixels = cv2.countNonZero(valid_sky_mask)

    if total_sky_pixels > 0:
        # Count white cloud pixels within sky mask
        cloud_pixels_in_sky = cv2.bitwise_and(rb_thresh_raw, rb_thresh_raw, mask=valid_sky_mask)
        cloud_pixels = cv2.countNonZero(cloud_pixels_in_sky)
        cloud_percentage = (cloud_pixels / total_sky_pixels) * 100

        # forecast based on percentage
        if cloud_percentage < 10:
            sky_condition = "Clear"
        elif cloud_percentage < 30:
            sky_condition = "Mostly Clear"
        elif cloud_percentage < 60:
            sky_condition = "Partly Cloudy"
        elif cloud_percentage < 90:
            sky_condition = "Mostly Cloudy"
        else:
            sky_condition = "Overcast"
    else:
        sky_condition = "Unknown"


    # shape stability
    cv2.accumulateWeighted(rb_thresh_raw, avg_rb_mask, alpha)
    rb_stable = cv2.threshold(avg_rb_mask.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)[1]

    # Post-Processing (Remove small noise and smooth jagged edges)
    rb_stable = cv2.morphologyEx(rb_stable, cv2.MORPH_OPEN, morph_k)

    # determine contours
    rb_output = img_raw.copy()
    contours, _ = cv2.findContours(rb_stable, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 400]  # sort out small contours

    cv2.drawContours(rb_output, valid_contours, -1, (0, 0, 0), 1)  # visualizing contours
    print("contours drawn")

    # Calculate current centers--------------------------------
    current_centers = []
    frame_dxs = []
    frame_dys = []
    next_accumulated = {}

    for idx, cnt in enumerate(valid_contours):
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            current_centers.append((cX, cY))
            cv2.circle(rb_output, (cX, cY), 4, (0, 0, 0), -1)  # mark center with black dot

    if prev_centers and current_centers:
        for c_idx, (cX, cY) in enumerate(current_centers):
            distances = [np.hypot(cX - pX, cY - pY) for (pX, pY) in prev_centers]
            min_distance_idx = np.argmin(distances)
            closest_distance = distances[min_distance_idx]

            if closest_distance < 60:
                pX, pY = prev_centers[min_distance_idx]
                dx = cX - pX
                dy = cY - pY

                if dx != 0 or dy != 0:
                    frame_dxs.append(dx)
                    frame_dys.append(dy)

                prev_total_dx, prev_total_dy = accumulated_movements.get((pX, pY), (0, 0))
                total_dx = prev_total_dx + dx
                total_dy = prev_total_dy + dy
                next_accumulated[(cX, cY)] = (total_dx, total_dy)

                # object specific compass
                if total_dx != 0 or total_dy != 0:
                    # Convert object pixel movement to (cardinal) degrees
                    obj_pixel_angle = np.degrees(np.arctan2(total_dy, total_dx))
                    obj_compass_dir = (90 - obj_pixel_angle) % 360
                    obj_true_bearing = (config.CAMERA_DIRECTION + obj_compass_dir) % 360
                    obj_cardinal = get_cardinal_direction(obj_true_bearing)
                    obj_heading_text = f"{obj_true_bearing:.0f} deg ({obj_cardinal})"
                else:
                    obj_heading_text = "Heading: Tracking..."

                cv2.putText(rb_output, obj_heading_text, (cX - 25, cY + 15),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 100, 0), 1, cv2.LINE_AA)

        if frame_dxs and frame_dys:
            # using median, to remove outliers (false movement tracking)
            movement_history.append((np.median(frame_dxs), np.median(frame_dys)))
            if len(movement_history) > 90:
                movement_history.pop(0)

    accumulated_movements = next_accumulated

    if len(movement_history) >= min_frames_required:
        dx_values = [v[0] for v in movement_history]
        dy_values = [v[1] for v in movement_history]

        # remove extreme outlier spikes
        def filter_outliers(data):
            q25, q75 = np.percentile(data, [25, 75])
            iqr = q75 - q25
            lower_bound = q25 - (1.5 * iqr)
            upper_bound = q75 + (1.5 * iqr)
            return [x for x in data if lower_bound <= x <= upper_bound]

        filtered_dx = filter_outliers(dx_values)
        filtered_dy = filter_outliers(dy_values)

        final_dx = np.mean(filtered_dx) if filtered_dx else np.mean(dx_values)
        final_dy = np.mean(filtered_dy) if filtered_dy else np.mean(dy_values)

        pixel_angle_rad = np.arctan2(final_dy, final_dx)
        pixel_angle_deg = np.degrees(pixel_angle_rad)
        compass_movement_direction = (90 - pixel_angle_deg) % 360

        true_bearing = (config.CAMERA_DIRECTION + compass_movement_direction) % 360
        cardinal = get_cardinal_direction(true_bearing)

        global_cardinal_result = f"{true_bearing:.1f} deg ({cardinal})"
        print(f"Calculated Wind Direction: {global_cardinal_result}")
    else:
        global_cardinal_result = "Calculating..."

    # save current centers for the next frames comparison
    prev_centers = current_centers

    os.makedirs(os.path.dirname(save_path_newest), exist_ok=True)
    cv2.imwrite(save_path_newest, rb_output)
    print(f"Processed and saved cloud detection result to {save_path_newest}.")

    del rb_output, contours, valid_contours, rb_stable, rb_thresh_raw
    gc.collect()

    return global_cardinal_result, sky_condition