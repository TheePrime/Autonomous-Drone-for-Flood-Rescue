import os

# Dataset paths
DATASET_PATHS = [
    "datasets/VisDrone/VisDrone2019-DET-train",
    "datasets/VisDrone/VisDrone2019-DET-val"
]

# VisDrone class mapping
CLASS_MAP = {
    1: 0,  # pedestrian
    2: 1,  # people
    3: 2,  # bicycle
    4: 3,  # car
    5: 4,  # van
    6: 5,  # truck
    7: 6,  # tricycle
    8: 7,  # awning-tricycle
    9: 8,  # bus
    10: 9  # motor
}

for dataset_path in DATASET_PATHS:

    images_path = os.path.join(dataset_path, "images")
    annotations_path = os.path.join(dataset_path, "annotations")
    labels_path = os.path.join(dataset_path, "labels")

    os.makedirs(labels_path, exist_ok=True)

    image_files = os.listdir(images_path)

    for image_file in image_files:

        image_name = os.path.splitext(image_file)[0]

        annotation_file = os.path.join(
            annotations_path,
            image_name + ".txt"
        )

        label_file = os.path.join(
            labels_path,
            image_name + ".txt"
        )

        image_path = os.path.join(images_path, image_file)

        try:
            import cv2

            img = cv2.imread(image_path)

            h, w = img.shape[:2]

        except:
            continue

        yolo_lines = []

        if os.path.exists(annotation_file):

            with open(annotation_file, "r") as f:

                lines = f.readlines()

                for line in lines:

                    parts = line.strip().split(",")

                    if len(parts) < 6:
                        continue

                    x, y, bw, bh = map(float, parts[:4])

                    cls = int(parts[5])

                    if cls not in CLASS_MAP:
                        continue

                    cls_id = CLASS_MAP[cls]

                    # Convert to YOLO format
                    x_center = (x + bw / 2) / w
                    y_center = (y + bh / 2) / h
                    width = bw / w
                    height = bh / h

                    yolo_line = (
                        f"{cls_id} "
                        f"{x_center:.6f} "
                        f"{y_center:.6f} "
                        f"{width:.6f} "
                        f"{height:.6f}"
                    )

                    yolo_lines.append(yolo_line)

        with open(label_file, "w") as f:
            f.write("\n".join(yolo_lines))

print("VisDrone conversion completed successfully!")