import os
import cv2
import numpy as np

def cloud_detection(image_folder):
    extensions = ('.jpg', '.png', '.jpeg')
    filenames = []

    for f in os.listdir(image_folder):
        name_lower = f.lower()
        if name_lower.endswith(extensions) and name_lower != 'mask.png':
            filenames.append(f)

    filenames.sort()

    if not filenames:
        print("No images found.")
        return

    # Mask Setup (to remove buildings etc.)
    mask_path = os.path.join(image_folder, "mask.png")
    mask_raw = cv2.imread(mask_path)

    first_img = cv2.imread(os.path.join(image_folder, filenames[0]))
    if first_img is None:
        return
    h, w = first_img.shape[:2]

    if mask_raw is not None:
        mask_gray = cv2.cvtColor(mask_raw, cv2.COLOR_BGR2GRAY)
        mask_binary = cv2.threshold(mask_gray, 1, 255, cv2.THRESH_BINARY)[1]
        if mask_binary.shape[:2] != (h, w):
            mask_binary = cv2.resize(mask_binary, (w, h), interpolation=cv2.INTER_NEAREST)
    else:
        mask_binary = np.full((h, w), 255, dtype=np.uint8)

    # Lighting settings
    # CLAHE (Contrast Limited Adaptive Histogram Equalization): locally enhances cloud contrast to handle global lighting shifts
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    # long-term memory buffer (remove big light changes)
    avg_rb_mask = np.zeros((h, w), dtype=np.float32)

    # Finetuning Parameters
    alpha = 0.8  # prevent shape jumps (1.0 = no prevention, 0.1 = high prevention)
    blur_k = (31, 31)  # Edge smoothness
    morph_k = np.ones((15, 15), np.uint8)  # Noise removal

    i = 0
    fixed_dim = (400, 300)  # 1.33 aspect ratio

    while i < len(filenames):
        img_raw = cv2.imread(os.path.join(image_folder, filenames[i]))
        if img_raw is None:
            i += 1
            continue

        # NRBR Feature Extraction
        """
        NRBR = Normalized red blue ratio
        Clear sky reflects mostly blue light, while clouds reflect red and blue light equally. 
        Comparing color channels make separating clouds easier.
        Red and blue parts of picture are extracted.
        """
        b, g, r = cv2.split(img_raw.astype(np.float32))
        r_b_feature = np.clip(r / (b + 1e-6), 0.4, 1.6)  # 1e-6 is failsafe of div/0 (in case a pixel is perfectly black)
        rb_norm = cv2.normalize(r_b_feature, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)  # transform decimals back to 0-255 ratio
        rb_masked = cv2.bitwise_and(rb_norm, rb_norm, mask=mask_binary)

        # enhance contrast (clahe) and blurr (for smoother shapes)
        rb_clahe = clahe.apply(rb_masked)
        rb_blurred = cv2.GaussianBlur(rb_clahe, blur_k, 0)

        # cloud threshold (finetuning)
        _, rb_thresh_raw = cv2.threshold(rb_blurred, 120, 255, cv2.THRESH_BINARY)
        # ---- Otsu thersholding: automatically find the best value (with correction) ------ Didnt really improve the detection but i leave it here for now
        # otsu_val, _ = cv2.threshold(rb_blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # otsu_correction = min(otsu_val + 50, 255)
        # _, rb_thresh_raw = cv2.threshold(rb_blurred, otsu_correction, 255, cv2.THRESH_BINARY)

        # shape stability
        cv2.accumulateWeighted(rb_thresh_raw, avg_rb_mask, alpha)
        rb_stable = cv2.threshold(avg_rb_mask.astype(np.uint8), 127, 255, cv2.THRESH_BINARY)[1]

        # Post-Processing (Remove small noise and smooth jagged edges)
        # rb_final_mask = rb_stable
        rb_final_mask = cv2.morphologyEx(rb_stable, cv2.MORPH_OPEN, morph_k)

        # draw result (contours)
        rb_output = img_raw.copy()
        contours, _ = cv2.findContours(rb_final_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) > 5000:
                cv2.drawContours(rb_output, [cnt], -1, (0, 0, 0), 3)

        # display result
        # cv2.imshow("NRBR Feature:", cv2.resize(rb_clahe, fixed_dim))
        cv2.imshow("Detection Result", cv2.resize(rb_output, fixed_dim))

        key = cv2.waitKeyEx(0)
        if key == 27:           # ESC=close
            break
        elif key == 2424832:    # left arrow=previous
            i = max(i - 1, 0)
        else:                   # any other key = next
            i = min(i + 1, len(filenames) - 1)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    path = "/home/pi/solar-nowcasting/data/dataset3"  # folder path
    cloud_detection(path)

