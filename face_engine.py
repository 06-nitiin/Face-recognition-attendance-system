from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import cv2
import face_recognition
import numpy as np


@dataclass
class KnownPerson:
    name: str
    encodings: List[np.ndarray] = field(default_factory=list)


class FaceEngine:
    """Loads and matches one or more face samples for each person."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
    SAMPLE_SEPARATOR = "__"

    def __init__(self, training_dir: Path, tolerance: float = 0.5) -> None:
        self.training_dir = training_dir
        self.tolerance = tolerance
        self.known_people: List[KnownPerson] = []
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
                "Enroll a person before starting attendance."
            )

        grouped_encodings: dict[str, list[np.ndarray]] = defaultdict(list)
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

            person_name = self.person_name_from_stem(image_path.stem)
            grouped_encodings[person_name].append(encodings[0])

        self.known_people = [
            KnownPerson(name=name, encodings=encodings)
            for name, encodings in sorted(grouped_encodings.items())
        ]
        if not self.known_people:
            raise ValueError("No valid training images could be encoded.")

    @classmethod
    def person_name_from_stem(cls, stem: str) -> str:
        return stem.split(cls.SAMPLE_SEPARATOR, maxsplit=1)[0]

    def recognize(
        self, frame: np.ndarray, scale: float = 0.25
    ) -> List[Tuple[str | None, Tuple[int, int, int, int], float]]:
        """Return name, full-size location, and closest sample distance."""
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small_frame)
        encodings = face_recognition.face_encodings(rgb_small_frame, locations)

        results = []
        for encoding, location in zip(encodings, locations):
            person_distances = []
            for person in self.known_people:
                distances = face_recognition.face_distance(person.encodings, encoding)
                person_distances.append(float(np.min(distances)))

            best_index = int(np.argmin(person_distances))
            best_distance = person_distances[best_index]
            name = (
                self.known_people[best_index].name
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
