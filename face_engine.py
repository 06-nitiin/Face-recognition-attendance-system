from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import cv2
import face_recognition
import numpy as np


@dataclass
class KnownFace:
    name: str
    encoding: np.ndarray


class FaceEngine:
    """Loads known faces and matches faces found in webcam frames."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    def __init__(self, training_dir: Path, tolerance: float = 0.5) -> None:
        self.training_dir = training_dir
        self.tolerance = tolerance
        self.known_faces: List[KnownFace] = []
        self.load_known_faces()

    def load_known_faces(self) -> None:
        if not self.training_dir.exists():
            raise FileNotFoundError(
                f"Training directory does not exist: {self.training_dir}"
            )

        if not self.training_dir.is_dir():
            raise NotADirectoryError(
                f"Training path is not a directory: {self.training_dir}"
            )

        image_paths = sorted(
            path
            for path in self.training_dir.iterdir()
            if path.is_file() and path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

        if not image_paths:
            raise ValueError(
                f"No training images found in {self.training_dir}. "
                "Add one image per person, such as Alice.jpg."
            )

        for image_path in image_paths:
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"Warning: could not read {image_path}; skipping.")
                continue

            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_image)

            if len(locations) != 1:
                print(
                    f"Warning: {image_path.name} contains {len(locations)} faces; "
                    "exactly one is required. Skipping."
                )
                continue

            encodings = face_recognition.face_encodings(rgb_image, locations)
            if not encodings:
                print(f"Warning: could not encode {image_path.name}; skipping.")
                continue

            self.known_faces.append(
                KnownFace(name=image_path.stem, encoding=encodings[0])
            )

        if not self.known_faces:
            raise ValueError("No valid training images could be encoded.")

    def recognize(
        self, frame: np.ndarray, scale: float = 0.25
    ) -> List[Tuple[str | None, Tuple[int, int, int, int], float]]:
        """Return name, full-size location, and distance for each detected face."""
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small_frame)
        encodings = face_recognition.face_encodings(rgb_small_frame, locations)

        known_encodings = [face.encoding for face in self.known_faces]
        results = []

        for encoding, location in zip(encodings, locations):
            distances = face_recognition.face_distance(known_encodings, encoding)
            best_index = int(np.argmin(distances))
            best_distance = float(distances[best_index])
            name = (
                self.known_faces[best_index].name
                if best_distance <= self.tolerance
                else None
            )

            top, right, bottom, left = location
            full_size_location = (
                int(top / scale),
                int(right / scale),
                int(bottom / scale),
                int(left / scale),
            )
            results.append((name, full_size_location, best_distance))

        return results
