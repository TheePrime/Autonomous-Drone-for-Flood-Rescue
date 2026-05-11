import cv2
import json
import os
from datetime import datetime
from ultralytics import YOLO

# Load trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Ask user for video path
video_path = input("Enter video path: ")

# Open video
cap = cv2.VideoCapture(video_path)

# Create detections folder
os.makedirs("detections", exist_ok=True)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Run detection
    results = model(frame)

    # Copy frame for annotations
    annotated_frame = frame.copy()

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Human classes only
            if cls in [0, 1] and conf > 0.5:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Draw bounding box
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = f"Human {conf:.2f}"

                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

                # Timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                # Save detection image
                image_name = f"detections/{timestamp}.jpg"

                cv2.imwrite(image_name, annotated_frame)

                # Detection log data
                detection_data = {
                    "time": timestamp,
                    "confidence": round(conf, 2),
                    "bbox": [x1, y1, x2, y2],
                    "image": image_name
                }

                # Print detection
                print(detection_data)

                # Save log
                with open("detections.json", "a") as f:
                    json.dump(detection_data, f)
                    f.write("\n")

    # Show output
    cv2.imshow("UAV Human Detection", annotated_frame)

    # ESC key to exit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()