import tempfile
import unittest
from pathlib import Path

from enrollment_utils import enrollment_paths, safe_person_name


class EnrollmentUtilsTests(unittest.TestCase):
    def test_sanitizes_person_name(self) -> None:
        self.assertEqual(safe_person_name("Nitin Bhardwaj"), "Nitin_Bhardwaj")

    def test_rejects_name_without_alphanumeric_characters(self) -> None:
        with self.assertRaises(ValueError):
            safe_person_name("///")

    def test_finds_legacy_and_multi_sample_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            training_dir = Path(directory)
            for filename in ("Nitin.jpg", "Nitin__1.jpg", "Nitin__2.png", "Other.jpg"):
                (training_dir / filename).touch()

            found = enrollment_paths(training_dir, "Nitin")
            self.assertEqual(
                [path.name for path in found],
                ["Nitin.jpg", "Nitin__1.jpg", "Nitin__2.png"],
            )

    def test_does_not_match_similar_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            training_dir = Path(directory)
            (training_dir / "Nitin__1.jpg").touch()
            (training_dir / "Nitin2.jpg").touch()

            found = enrollment_paths(training_dir, "Nitin")
            self.assertEqual([path.name for path in found], ["Nitin__1.jpg"])


if __name__ == "__main__":
    unittest.main()
