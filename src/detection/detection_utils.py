from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


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
        "coordinate_system": "gps-estimated",
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