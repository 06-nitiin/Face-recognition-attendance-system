import unittest

from enrollment_utils import safe_person_name


class EnrollmentHelperTests(unittest.TestCase):
    def test_converts_spaces_to_underscores(self) -> None:
        self.assertEqual(safe_person_name("Nitin Bhardwaj"), "Nitin_Bhardwaj")

    def test_replaces_unsafe_filename_characters(self) -> None:
        self.assertEqual(safe_person_name("Nitin/../test"), "Nitin_test")

    def test_rejects_empty_or_unsafe_names(self) -> None:
        with self.assertRaises(ValueError):
            safe_person_name("///")

    def test_limits_name_length(self) -> None:
        self.assertLessEqual(len(safe_person_name("A" * 100)), 80)


if __name__ == "__main__":
    unittest.main()
