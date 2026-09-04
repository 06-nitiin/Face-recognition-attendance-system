import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectConfig:
    database: Path = Path("attendance.db")
    training_dir: Path = Path("Training_images")
    camera: int = 0
    tolerance: float = 0.5
    confirm_frames: int = 5
    cooldown: float = 10.0
    dashboard_host: str = "127.0.0.1"
    dashboard_port: int = 5000

    @classmethod
    def from_environment(cls) -> "ProjectConfig":
        return cls(
            database=Path(os.getenv("ATTENDANCE_DATABASE", "attendance.db")),
            training_dir=Path(os.getenv("ATTENDANCE_TRAINING_DIR", "Training_images")),
            camera=int(os.getenv("ATTENDANCE_CAMERA", "0")),
            tolerance=float(os.getenv("ATTENDANCE_TOLERANCE", "0.5")),
            confirm_frames=int(os.getenv("ATTENDANCE_CONFIRM_FRAMES", "5")),
            cooldown=float(os.getenv("ATTENDANCE_COOLDOWN", "10")),
            dashboard_host=os.getenv("DASHBOARD_HOST", "127.0.0.1"),
            dashboard_port=int(os.getenv("DASHBOARD_PORT", "5000")),
        )

    def validate(self) -> None:
        if self.camera < 0:
            raise ValueError("ATTENDANCE_CAMERA cannot be negative.")
        if not 0 < self.tolerance <= 1:
            raise ValueError("ATTENDANCE_TOLERANCE must be greater than 0 and at most 1.")
        if self.confirm_frames < 1:
            raise ValueError("ATTENDANCE_CONFIRM_FRAMES must be at least 1.")
        if self.cooldown < 0:
            raise ValueError("ATTENDANCE_COOLDOWN cannot be negative.")
        if not 1 <= self.dashboard_port <= 65535:
            raise ValueError("DASHBOARD_PORT must be between 1 and 65535.")
