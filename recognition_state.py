import time
from collections import defaultdict


class FrameConfirmation:
    """Confirms a name only after it is seen in consecutive frames."""

    def __init__(self, required_frames: int = 5) -> None:
        if required_frames < 1:
            raise ValueError("required_frames must be at least 1")
        self.required_frames = required_frames
        self._counts: dict[str, int] = defaultdict(int)
        self._seen_this_frame: set[str] = set()
        self._confirmed: set[str] = set()

    def start_frame(self) -> None:
        self._seen_this_frame.clear()

    def observe(self, name: str | None) -> str | None:
        if not name:
            return None

        self._seen_this_frame.add(name)
        if name in self._confirmed:
            return None

        self._counts[name] += 1
        if self._counts[name] >= self.required_frames:
            self._confirmed.add(name)
            return name
        return None

    def finish_frame(self) -> None:
        missing_names = set(self._counts) - self._seen_this_frame
        for name in missing_names:
            self._counts[name] = 0

    def progress(self, name: str | None) -> int:
        return self._counts.get(name or "", 0)


class SessionCooldown:
    """Avoids repeated processing of the same name during a camera session."""

    def __init__(self, seconds: float = 10.0) -> None:
        if seconds < 0:
            raise ValueError("seconds cannot be negative")
        self.seconds = seconds
        self._last_processed: dict[str, float] = {}

    def allows(self, name: str, now: float | None = None) -> bool:
        current_time = time.monotonic() if now is None else now
        last_time = self._last_processed.get(name)
        return last_time is None or current_time - last_time >= self.seconds

    def record(self, name: str, now: float | None = None) -> None:
        current_time = time.monotonic() if now is None else now
        self._last_processed[name] = current_time
