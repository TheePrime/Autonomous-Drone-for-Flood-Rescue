import cv2
from ultralytics import YOLO

# Load model
model = YOLO("yolov8n.pt")

# Open video
cap = cv2.VideoCapture("videos/drone.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Run detection
    results = model(frame)

    # Create clean frame
    annotated_frame = frame.copy()

    # Process detections
    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            conf = float(box.conf[0])

            # PERSON ONLY
            if cls == 0 and conf > 0.5:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Draw box
                cv2.rectangle(
                    annotated_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # Label
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

    # Show frame
    cv2.imshow("Human Detection Only", annotated_frame)

    # ESC to quit
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()