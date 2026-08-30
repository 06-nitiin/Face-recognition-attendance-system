from datetime import datetime
from pathlib import Path


class AttendanceStore:
    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_path.touch(exist_ok=True)

    def mark_present(self, name: str) -> bool:
        existing_names = self._read_names()
        if name in existing_names:
            return False

        timestamp = datetime.now().strftime("%H:%M:%S")
        with self.csv_path.open("a", encoding="utf-8", newline="") as file:
            if self.csv_path.stat().st_size > 0:
                file.write("\n")
            file.write(f"{name},{timestamp}")
        return True

    def _read_names(self) -> set[str]:
        names = set()
        with self.csv_path.open("r", encoding="utf-8") as file:
            for line in file:
                name = line.strip().split(",", maxsplit=1)[0]
                if name and name.lower() != "name":
                    names.add(name)
        return names
