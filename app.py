import argparse
from pathlib import Path

import cv2

from attendance import AttendanceStore
from face_engine import FaceEngine
from recognition_state import FrameConfirmation, SessionCooldown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mark attendance using face recognition and a webcam."
    )
    parser.add_argument(
        "--training-dir", type=Path, default=Path("Training_images")
    )
    parser.add_argument(
        "--database", type=Path, default=Path("attendance.db")
    )
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="Face distance threshold; lower values are stricter.",
    )
    parser.add_argument(
        "--confirm-frames",
        type=int,
        default=5,
        help="Consecutive frames required before attendance is attempted.",
    )
    parser.add_argument(
        "--cooldown",
        type=float,
        default=10.0,
        help="Seconds before the same name can be processed again in this session.",
    )
    return parser.parse_args()


def draw_result(frame, name, location, distance, confirmation_progress, required_frames):
    top, right, bottom, left = location
    color = (0, 180, 0) if name else (0, 0, 220)

    if name and confirmation_progress < required_frames:
        label = f"{name.upper()} | confirming {confirmation_progress}/{required_frames}"
    elif name:
        label = f"{name.upper()} | distance: {distance:.2f}"
    else:
        label = f"UNKNOWN | distance: {distance:.2f}"

    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    cv2.putText(
        frame,
        label,
        (left + 6, bottom - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )


def main() -> None:
    args = parse_args()
    if args.confirm_frames < 1:
        raise SystemExit("--confirm-frames must be at least 1.")
    if args.cooldown < 0:
        raise SystemExit("--cooldown cannot be negative.")

    try:
        engine = FaceEngine(args.training_dir, tolerance=args.tolerance)
    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        raise SystemExit(f"Startup error: {error}") from error

    attendance = AttendanceStore(args.database)
    confirmer = FrameConfirmation(required_frames=args.confirm_frames)
    cooldown = SessionCooldown(seconds=args.cooldown)
    camera = cv2.VideoCapture(args.camera)

    if not camera.isOpened():
        attendance.close()
        raise SystemExit(
            f"Could not open camera {args.camera}. Check the camera index and permissions."
        )

    print("Recognition started. Press 'q' in the camera window to quit.")

    try:
        while True:
            success, frame = camera.read()
            if not success or frame is None:
                print("Warning: failed to read a frame from the camera.")
                break

            # Mirror the preview so it behaves like a normal front-facing mirror.
            frame = cv2.flip(frame, 1)
            results = engine.recognize(frame)
            confirmer.start_frame()

            for name, location, distance in results:
                progress_before_confirmation = confirmer.progress(name)
                confirmed_name = confirmer.observe(name)
                progress = confirmer.progress(name)
                draw_result(
                    frame,
                    name,
                    location,
                    distance,
                    progress,
                    args.confirm_frames,
                )

                if confirmed_name and cooldown.allows(confirmed_name):
                    marked = attendance.mark_present(confirmed_name)
                    cooldown.record(confirmed_name)
                    if marked:
                        print(f"Attendance marked for {confirmed_name}.")
                    else:
                        print(f"Attendance already recorded today for {confirmed_name}.")

            confirmer.finish_frame()
            cv2.imshow("Face Recognition Attendance", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        print("\nRecognition interrupted.")
    finally:
        camera.release()
        cv2.destroyAllWindows()
        attendance.close()
        print("Recognition stopped.")


if __name__ == "__main__":
    main()
