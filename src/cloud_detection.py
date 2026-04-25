import os
import cv2
import numpy as np
import gc

def cloud_detection(image_folder):
    extensions = ('.jpg', '.png', '.jpeg')
    filenames = []
    w, h = 648, 486 # images are resized to fixed dimension to reduce ram usage (1/4th of camera resolution)
    image_dimensions = (w, h)

    print("Starting Cloud Detection")

    # sort filenames and ignore mask
    for f in os.listdir(image_folder):
        name_lower = f.lower()
        if name_lower.endswith(extensions) and 'mask' not in name_lower:
            filenames.append(f)

    filenames.sort()

    if not filenames:
        print("No images found.")
        return

    # Mask Setup (to remove buildings etc.).
    mask_path = os.path.join(image_folder, "mask.png")
    mask_raw = cv2.imread(mask_path)

    if mask_raw is not None:
        mask_gray = cv2.cvtColor(mask_raw, cv2.COLOR_BGR2GRAY)
        mask_binary = cv2.threshold(mask_gray, 1, 255, cv2.THRESH_BINARY)[1]
        mask_binary = cv2.resize(mask_binary, image_dimensions, interpolation=cv2.INTER_NEAREST)
    else:
        print("Using default white mask")
        mask_binary = np.full((h, w), 255, dtype=np.uint8)

    print("Mask loaded and resized")

    # Lighting settings
    # CLAHE (Contrast Limited Adaptive Histogram Equalization): locally enhances cloud contrast to handle global lighting shifts
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # long-term memory buffer (remove big light changes)
    print("Attempting to allocate memory buffers...")
    avg_rb_mask = np.zeros((h, w), dtype=np.float32)
    print("Memory buffers allocated.")

    # Finetuning Parameters
    alpha = 0.8  # prevent shape jumps (1.0 = no prevention, 0.1 = high prevention)
    morph_k = np.ones((15, 15), np.uint8)  # Noise removal

    i = 0
    while i < len(filenames):
        gc.collect()

        img_path = os.path.join(image_folder, filenames[i])

        # load the image at 1/4th size
        img_raw = cv2.imread(img_path, cv2.IMREAD_REDUCED_COLOR_4)

        if img_raw is None:
            i += 1
            continue

        print(f"Successfully loaded and resized: {filenames[i]}")
        # NRBR Feature Extraction
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
        r_b_feature = np.clip(r / (b + 1e-6), 0.4,1.6)
        # transform decimals back to 0-255 ratio
        rb_norm = cv2.normalize(r_b_feature, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        del r, b, r_b_feature

        # Ensure mask matches current frame dimensions
        if mask_binary.shape[:2] != rb_norm.shape[:2]:
            mask_binary = cv2.resize(mask_binary, (rb_norm.shape[1], rb_norm.shape[0]), interpolation=cv2.INTER_NEAREST)

        rb_masked = cv2.bitwise_and(rb_norm, rb_norm, mask=mask_binary)
        del rb_norm

        # enhance contrast (clahe) and blur (for smoother shapes)
        rb_clahe = clahe.apply(rb_masked)
        # rb_blurred = cv2.GaussianBlur(rb_clahe, blur_k, 0) # heavy operation for mc. often causes crash
        rb_blurred = rb_clahe
        del rb_masked, rb_clahe

        # cloud threshold (finetuning)
        _, rb_thresh_raw = cv2.threshold(rb_blurred, 120, 255, cv2.THRESH_BINARY)
        del rb_blurred

        # shape stability
        cv2.accumulateWeighted(rb_thresh_raw, avg_rb_mask, alpha)
        rb_stable = cv2.threshold(avg_rb_mask.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)[1]

        # Post-Processing (Remove small noise and smooth jagged edges)
        rb_stable = cv2.morphologyEx(rb_stable, cv2.MORPH_OPEN, morph_k)

        # draw result (contours)
        rb_output = img_raw.copy()
        contours, _ = cv2.findContours(rb_stable, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 5000]
        cv2.drawContours(rb_output, valid_contours, -1, (0, 0, 0), 1)
        print("contours drawn")

        save_path = "/home/pi/solar-nowcasting/data/test/latest_capture.jpg"
        cv2.imwrite(save_path, rb_output)
        print(f"Processed and saved {filenames[i]} as latest_capture.jpg")

        del rb_output, img_raw, contours, valid_contours, rb_stable, rb_thresh_raw
        gc.collect()

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
    path = "/home/pi/solar-nowcasting/data/dataset3"  # folder path
    cloud_detection(path)

