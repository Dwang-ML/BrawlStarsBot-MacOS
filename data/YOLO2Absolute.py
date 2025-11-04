import os
from PIL import Image

# CONFIG
IMG_DIR = "images/train"
YOLO_LABEL_DIR = "labels/Yolo"
OUTPUT_DIR = "labels/train"
os.makedirs(OUTPUT_DIR, exist_ok=True)

for label_file in os.listdir(YOLO_LABEL_DIR):
    if not label_file.endswith(".txt"):
        continue

    img_name = label_file.replace(".txt", ".png")
    img_path = os.path.join(IMG_DIR, img_name)
    if not os.path.exists(img_path):
        print(f"Image not found for {label_file}, skipping")
        continue

    img = Image.open(img_path)
    w, h = img.size

    abs_lines = []
    with open(os.path.join(YOLO_LABEL_DIR, label_file)) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) != 5:
                continue

            cls = parts[0]
            x_center, y_center, bw, bh = map(float, parts[1:])

            # convert to absolute coordinates
            x_min = (x_center - bw/2) * w
            y_min = (y_center - bh/2) * h
            x_max = (x_center + bw/2) * w
            y_max = (y_center + bh/2) * h

            # Skip boxes with zero or negative width/height
            if x_max <= x_min or y_max <= y_min:
                continue

            abs_lines.append(f"{cls} {x_min} {y_min} {x_max} {y_max}")

    if abs_lines:
        out_path = os.path.join(OUTPUT_DIR, label_file)
        with open(out_path, "w") as out_f:
            out_f.write("\n".join(abs_lines))

print("Conversion complete! Absolute labels saved in:", OUTPUT_DIR)
