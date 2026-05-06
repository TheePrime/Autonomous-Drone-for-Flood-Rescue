from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

# Run detection
results = model("images/test.jpg")

# Show results
results[0].show()

# Print detections
for r in results:
    for box in r.boxes:
        cls = int(box.cls[0])

        # Class 0 = person
        if cls == 0:
            print("Human detected")