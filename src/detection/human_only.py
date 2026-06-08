import cv2
import os
from datetime import datetime
from ultralytics import YOLO

from detection_utils import DetectionDeduplicator, append_detection_log, build_detection_record, detections_dir

# Load trained model
model = YOLO("runs/detect/train/weights/best.pt")

# Ask user for video path
video_path = input("Enter video path: ")

# Open video
cap = cv2.VideoCapture(video_path)

# Create detections folder
os.makedirs("detections", exist_ok=True)
deduplicator = DetectionDeduplicator()
frame_index = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_index += 1

    # Run detection
    results = model(frame)

    # Copy frame for annotations
    annotated_frame = frame.copy()
    frame_height, frame_width = frame.shape[:2]

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # Human class only
            if cls == 0 and conf > 0.5:

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bbox = (x1, y1, x2, y2)

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

                if deduplicator.is_new(bbox):
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    image_name = detections_dir() / f"human_only_{timestamp}_{frame_index:06d}.jpg"

                    cv2.imwrite(str(image_name), annotated_frame)

                    detection_data = build_detection_record(
                        frame_index=frame_index,
                        confidence=conf,
                        bbox=bbox,
                        frame_width=frame_width,
                        frame_height=frame_height,
                        image_path=image_name,
                    )

                    # Print detection
                    print(detection_data)

                    # Save log
                    append_detection_log(detection_data)

    # Show output
    cv2.imshow("UAV Human Detection", annotated_frame)

    # ESC key to exit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()