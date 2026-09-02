import argparse
from pathlib import Path

import cv2
import face_recognition

from enrollment_utils import safe_person_name


def has_exactly_one_face(frame) -> bool:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return len(face_recognition.face_locations(rgb_frame)) == 1


def face_is_large_enough(frame, minimum_size: int = 120) -> bool:
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    locations = face_recognition.face_locations(rgb_frame)
    if len(locations) != 1:
        return False
    top, right, bottom, left = locations[0]
    return (right - left) >= minimum_size and (bottom - top) >= minimum_size


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enroll one person using a validated webcam image."
    )
    parser.add_argument("name", help="Person's name, used as the image filename.")
    parser.add_argument(
        "--training-dir",
        type=Path,
        default=Path("Training_images"),
        help="Directory where the enrolled image will be stored.",
    )
    parser.add_argument(
        "--camera", type=int, default=0, help="Camera index passed to OpenCV."
    )
    parser.add_argument(
        "--force", action="store_true", help="Replace an existing enrollment image."
    )
    return parser.parse_args()


def enroll(name: str, training_dir: Path, camera_index: int, force: bool) -> Path:
    safe_name = safe_person_name(name)
    training_dir.mkdir(parents=True, exist_ok=True)
    output_path = training_dir / f"{safe_name}.jpg"

    if output_path.exists() and not force:
        raise FileExistsError(
            f"{output_path} already exists. Use --force to replace it."
        )

    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        raise RuntimeError(
            f"Could not open camera {camera_index}. Check camera permissions."
        )

    print("Enrollment started.")
    print("Position one face in the frame, then press 's' to save or 'q' to cancel.")

    try:
        while True:
            success, frame = camera.read()
            if not success or frame is None:
                raise RuntimeError("Could not read a frame from the camera.")

            preview = frame.copy()
            valid = has_exactly_one_face(frame) and face_is_large_enough(frame)
            message = "READY - press s to save" if valid else "Need exactly one close face"
            color = (0, 180, 0) if valid else (0, 0, 220)
            cv2.putText(
                preview,
                message,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Face Enrollment", preview)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                raise RuntimeError("Enrollment cancelled.")
            if key == ord("s"):
                if not valid:
                    print("Image rejected: show exactly one face closer to the camera.")
                    continue
                cv2.imwrite(str(output_path), frame)
                return output_path
    finally:
        camera.release()
        cv2.destroyAllWindows()


def main() -> None:
    args = parse_args()
    try:
        output_path = enroll(args.name, args.training_dir, args.camera, args.force)
    except (ValueError, FileExistsError, RuntimeError) as error:
        raise SystemExit(f"Enrollment error: {error}") from error
    print(f"Enrollment saved to {output_path}")


if __name__ == "__main__":
    main()
