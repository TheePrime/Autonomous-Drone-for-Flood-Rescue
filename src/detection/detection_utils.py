from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import cv2
import numpy as np


GPS_ORIGIN_LATITUDE = 37.7749
GPS_ORIGIN_LONGITUDE = -122.4194
METERS_PER_DEGREE_LATITUDE = 111_111.0



def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def detections_dir() -> Path:
    output_dir = project_root() / "detections"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def detections_log_path() -> Path:
    return project_root() / "detections.json"


def box_iou(first_box: tuple[int, int, int, int], second_box: tuple[int, int, int, int]) -> float:
    first_left, first_top, first_right, first_bottom = first_box
    second_left, second_top, second_right, second_bottom = second_box

    intersection_left = max(first_left, second_left)
    intersection_top = max(first_top, second_top)
    intersection_right = min(first_right, second_right)
    intersection_bottom = min(first_bottom, second_bottom)

    if intersection_right <= intersection_left or intersection_bottom <= intersection_top:
        return 0.0

    intersection_area = (intersection_right - intersection_left) * (intersection_bottom - intersection_top)
    first_area = (first_right - first_left) * (first_bottom - first_top)
    second_area = (second_right - second_left) * (second_bottom - second_top)

    return intersection_area / float(first_area + second_area - intersection_area)


def simulate_dummy_coordinates(
    frame_index: int,
    bbox: tuple[int, int, int, int],
    frame_width: int,
    frame_height: int,
) -> dict[str, Any]:
    left, top, right, bottom = bbox
    center_x = (left + right) / 2.0
    center_y = (top + bottom) / 2.0

    drone_north_m = math.sin(frame_index / 18.0) * 28.0 + frame_index * 0.35
    drone_east_m = math.cos(frame_index / 22.0) * 18.0
    drone_altitude_m = round(30.0 + math.cos(frame_index / 15.0) * 2.0, 2)

    human_east_m = (center_x / max(frame_width, 1) - 0.5) * 40.0
    human_north_m = (0.5 - center_y / max(frame_height, 1)) * 40.0

    drone_latitude = GPS_ORIGIN_LATITUDE + drone_north_m / METERS_PER_DEGREE_LATITUDE
    drone_longitude = GPS_ORIGIN_LONGITUDE + drone_east_m / (
        METERS_PER_DEGREE_LATITUDE * math.cos(math.radians(GPS_ORIGIN_LATITUDE))
    )

    human_latitude = drone_latitude + human_north_m / METERS_PER_DEGREE_LATITUDE
    human_longitude = drone_longitude + human_east_m / (
        METERS_PER_DEGREE_LATITUDE * math.cos(math.radians(drone_latitude))
    )

    return {
        "frame": frame_index,
        "drone_position": {
            "latitude": round(drone_latitude, 6),
            "longitude": round(drone_longitude, 6),
            "altitude_m": drone_altitude_m,
        },
        "human_position": {
            "latitude": round(human_latitude, 6),
            "longitude": round(human_longitude, 6),
        },
        "drone_position_m": {
            "north_m": round(drone_north_m, 2),
            "east_m": round(drone_east_m, 2),
            "altitude_m": round(drone_altitude_m, 2),
        },
        "human_position_m": {
            "north_m": round(human_north_m, 2),
            "east_m": round(human_east_m, 2),
        },
        "coordinate_system": "gps-estimated+metric",
    }


def relative_image_path(image_path: Path) -> str:
    try:
        return image_path.resolve().relative_to(project_root()).as_posix()
    except ValueError:
        return image_path.name


def build_detection_record(
    *,
    frame_index: int,
    confidence: float,
    bbox: tuple[int, int, int, int],
    frame_width: int,
    frame_height: int,
    image_path: Path | None = None,
) -> dict[str, Any]:
    timestamp = datetime.now().isoformat(timespec="seconds")
    record: dict[str, Any] = {
        "time": timestamp,
        "frame": frame_index,
        "confidence": round(confidence, 2),
        "bbox": list(bbox),
        **simulate_dummy_coordinates(frame_index, bbox, frame_width, frame_height),
    }

    if image_path is not None:
        record["image"] = relative_image_path(image_path)

    return record


def append_detection_log(record: dict[str, Any]) -> None:
    with detections_log_path().open("a", encoding="utf-8") as file_handle:
        json.dump(record, file_handle)
        file_handle.write("\n")


def overlay_detection_text(frame: "np.ndarray", record: dict[str, Any]) -> "np.ndarray":
    """Draws detection metadata (time, confidence, GPS coords, bbox) onto the image.

    Returns the modified frame.
    """
    if frame is None:
        return frame

    h, w = frame.shape[:2]
    pad = 8
    line_height = 18
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.5
    thickness = 1

    lines = []
    if record.get("time"):
        lines.append(f"Time: {record['time']}")
    lines.append(f"Conf: {record.get('confidence', 0):.2f}")

    dp = record.get("drone_position") or {}
    hp = record.get("human_position") or {}

    # Prefer metric fields for overlay (useful for live/webcam runs)
    dp_m = record.get("drone_position_m") or {}
    hp_m = record.get("human_position_m") or {}

    if dp_m.get("north_m") is not None and dp_m.get("east_m") is not None:
        lines.append(f"Drone (m): N={dp_m.get('north_m')} E={dp_m.get('east_m')} Alt={dp_m.get('altitude_m', '-')}")
    elif dp.get("latitude") is not None and dp.get("longitude") is not None:
        lines.append(f"Drone: {dp.get('latitude')}, {dp.get('longitude')} (alt {dp.get('altitude_m', '-')})")
    else:
        lines.append(f"Drone: {dp}")

    if hp_m.get("north_m") is not None and hp_m.get("east_m") is not None:
        lines.append(f"Human (m): N={hp_m.get('north_m')} E={hp_m.get('east_m')}")
    elif hp.get("latitude") is not None and hp.get("longitude") is not None:
        lines.append(f"Human: {hp.get('latitude')}, {hp.get('longitude')}")
    else:
        lines.append(f"Human: {hp}")

    if record.get("bbox"):
        bb = record["bbox"]
        lines.append(f"BBox: [{', '.join(map(str, bb))}]")

    # compute background rect size
    widths = [cv2.getTextSize(l, font, scale, thickness)[0][0] for l in lines]
    max_w = max(widths) if widths else 0
    bg_w = max_w + pad * 2
    bg_h = line_height * len(lines) + pad * 2

    # bottom-left corner for the box
    x = pad
    y = h - bg_h - pad

    # draw background
    cv2.rectangle(frame, (x, y), (x + bg_w, y + bg_h), (0, 0, 0), cv2.FILLED)
    cv2.rectangle(frame, (x, y), (x + bg_w, y + bg_h), (255, 255, 255), 1)

    # draw text lines
    ty = y + pad + line_height - 4
    for line in lines:
        cv2.putText(frame, line, (x + pad, ty), font, scale, (255, 255, 255), thickness, cv2.LINE_AA)
        ty += line_height

    return frame


@dataclass
class DetectionDeduplicator:
    iou_threshold: float = 0.65
    seen_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)

    def is_new(self, bbox: tuple[int, int, int, int]) -> bool:
        for seen_box in self.seen_boxes:
            if box_iou(seen_box, bbox) >= self.iou_threshold:
                return False

        self.seen_boxes.append(bbox)
        return True