import re


def safe_person_name(raw_name: str) -> str:
    """Return a safe, readable filename stem for an enrolled person."""
    name = re.sub(r"[^A-Za-z0-9 _-]", "_", raw_name).strip(" _-")
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_-")
    if not name or not re.search(r"[A-Za-z0-9]", name):
        raise ValueError("Name must contain at least one letter or number.")
    return name[:80]
