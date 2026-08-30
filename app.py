import argparse
from pathlib import Path

import cv2

from attendance import AttendanceStore
from face_engine import FaceEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mark attendance using face recognition and a webcam."
    )
    parser.add_argument(
        "--training-dir",
        type=Path,
        default=Path("Training_images"),
        help="Directory containing one face image per person.",
    )
    parser.add_argument(
        "--attendance-file",
        type=Path,
        default=Path("Attendance.csv"),
        help="CSV file used to store attendance.",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Camera index passed to OpenCV.",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="Face distance threshold; lower values are stricter.",
    )
    return parser.parse_args()


def draw_result(frame, name, location, distance) -> None:
    top, right, bottom, left = location
    color = (0, 180, 0) if name else (0, 0, 220)
    label = f"{name.upper()} ({distance:.2f})" if name else f"UNKNOWN ({distance:.2f})"

    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    cv2.putText(
        frame,
        label,
        (left + 6, bottom - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


def main() -> None:
    args = parse_args()

    try:
        engine = FaceEngine(args.training_dir, tolerance=args.tolerance)
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        raise SystemExit(f"Startup error: {error}") from error

    attendance = AttendanceStore(args.attendance_file)
    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        raise SystemExit(
            f"Could not open camera {args.camera}. Check the camera index and permissions."
        )

    print("Recognition started. Press 'q' to quit.")

    try:
        while True:
            success, frame = camera.read()
            if not success or frame is None:
                print("Warning: failed to read a frame from the camera.")
                break

            for name, location, distance in engine.recognize(frame):
                draw_result(frame, name, location, distance)
                if name and attendance.mark_present(name):
                    print(f"Attendance marked for {name}.")

            cv2.imshow("Face Recognition Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()
        print("Recognition stopped.")


if __name__ == "__main__":
    main()
