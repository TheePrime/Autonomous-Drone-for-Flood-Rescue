import cv2
import json
from datetime import datetime
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

# Open video
cap = cv2.VideoCapture("videos/drone.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    results = model(frame)

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Detect humans only
            if cls == 0 and conf > 0.5:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                detection_data = {
                    "time": str(datetime.now()),
                    "confidence": round(conf, 2),
                    "bbox": [x1, y1, x2, y2]
                }

                # Print to terminal
                print(detection_data)

                # Save to file
                with open("detections.json", "a") as f:
                    json.dump(detection_data, f)
                    f.write("\n")

    cv2.imshow("Detection Logging", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()