from ultralytics import YOLO
import os

model = YOLO("yolov8n.pt")

image_path = os.path.join("images", "test.jpg")

results = model(image_path)

results[0].show()

for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])

        if cls == 0:
            print("Human detected")