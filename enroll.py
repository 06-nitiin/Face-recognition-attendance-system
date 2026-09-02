import argparse
from pathlib import Path

import cv2
import face_recognition

from attendance import AttendanceStore
from enrollment_utils import enrollment_paths, safe_person_name


def valid_face(frame, minimum_size: int = 120) -> bool:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb_frame)
    if len(locations) != 1:
        return False
    top, right, bottom, left = locations[0]
    return (right - left) >= minimum_size and (bottom - top) >= minimum_size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enroll face samples and register person metadata."
    )
    parser.add_argument("name", help="Person's full name.")
    parser.add_argument("--email", help="Optional email address.")
    parser.add_argument("--person-id", dest="external_id", help="Optional student/employee ID.")
    parser.add_argument("--database", type=Path, default=Path("attendance.db"))
    parser.add_argument("--training-dir", type=Path, default=Path("Training_images"))
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def enroll(name, training_dir, camera_index, sample_count, force, database_path, email, external_id):
    if sample_count < 1:
        raise ValueError("Sample count must be at least 1.")

    safe_name = safe_person_name(name)
    training_dir.mkdir(parents=True, exist_ok=True)
    existing_paths = enrollment_paths(training_dir, safe_name)
    if existing_paths and not force:
        raise FileExistsError(
            f"Existing enrollment found for {safe_name}. Use --force to replace it."
        )
    if force:
        for path in existing_paths:
            path.unlink()

    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(f"Could not open camera {camera_index}. Check permissions.")

    saved_paths = []
    print(f"Enrollment started for {safe_name}; capture {sample_count} samples.")
    print("Press 's' when the frame says READY. Press 'q' to cancel.")
    try:
        while len(saved_paths) < sample_count:
            success, frame = camera.read()
            if not success or frame is None:
                raise RuntimeError("Could not read a frame from the camera.")
            ready = valid_face(frame)
            remaining = sample_count - len(saved_paths)
            message = f"READY - press s ({remaining} remaining)" if ready else "Need exactly one close face"
            color = (0, 180, 0) if ready else (0, 0, 220)
            preview = frame.copy()
            cv2.putText(preview, message, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
            cv2.imshow("Face Enrollment", preview)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                raise RuntimeError("Enrollment cancelled.")
            if key == ord("s"):
                if not ready:
                    print("Image rejected: show exactly one close face.")
                    continue
                output_path = training_dir / f"{safe_name}__{len(saved_paths) + 1}.jpg"
                if not cv2.imwrite(str(output_path), frame):
                    raise RuntimeError(f"Could not save {output_path}.")
                saved_paths.append(output_path)
                print(f"Saved sample {len(saved_paths)}/{sample_count}.")
    finally:
        camera.release()
        cv2.destroyAllWindows()

    store = AttendanceStore(database_path)
    try:
        person = store.register_person(safe_name, external_id=external_id, email=email)
    finally:
        store.close()
    print(f"Registered person #{person.id}: {person.name}")
    return saved_paths


def main() -> None:
    args = parse_args()
    try:
        saved_paths = enroll(
            args.name, args.training_dir, args.camera, args.samples, args.force,
            args.database, args.email, args.external_id,
        )
    except (ValueError, FileExistsError, RuntimeError) as error:
        raise SystemExit(f"Enrollment error: {error}") from error
    print(f"Enrollment complete. Saved {len(saved_paths)} sample(s).")


if __name__ == "__main__":
    main()
