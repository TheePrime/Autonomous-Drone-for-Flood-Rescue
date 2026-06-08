import cv2
from ultralytics import YOLO

from detection_utils import DetectionDeduplicator, append_detection_log, build_detection_record, detections_dir, overlay_detection_text

model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture(0)
deduplicator = DetectionDeduplicator()
frame_index = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_index += 1
    results = model(frame)
    annotated_frame = frame.copy()
    frame_height, frame_width = frame.shape[:2]

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if cls == 0 and conf > 0.5:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bbox = (x1, y1, x2, y2)

                cv2.rectangle(
                    annotated_frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    annotated_frame,
                    f"Human {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

                if deduplicator.is_new(bbox):
                    image_name = detections_dir() / f"live_{frame_index:06d}_{x1}_{y1}_{x2}_{y2}.jpg"

                    detection_record = build_detection_record(
                        frame_index=frame_index,
                        confidence=conf,
                        bbox=bbox,
                        frame_width=frame_width,
                        frame_height=frame_height,
                        image_path=image_name,
                    )

                    overlay_detection_text(annotated_frame, detection_record)
                    cv2.imwrite(str(image_name), annotated_frame)
                    append_detection_log(detection_record)

    cv2.imshow("YOLO Detection", annotated_frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()