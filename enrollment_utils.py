import re
from pathlib import Path


def safe_person_name(raw_name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9 _-]", "_", raw_name).strip(" _-")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_-")
    if not name or not re.search(r"[A-Za-z0-9]", name):
        raise ValueError("Name must contain at least one letter or number.")
    return name[:80]


def enrollment_paths(training_dir: Path, safe_name: str) -> list[Path]:
    """Find both legacy single-image and multi-sample enrollments."""
    paths = []
    for path in training_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        if path.stem == safe_name or path.stem.startswith(f"{safe_name}__"):
            paths.append(path)
    return sorted(paths)
