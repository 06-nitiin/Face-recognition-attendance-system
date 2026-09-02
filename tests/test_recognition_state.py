import unittest

from recognition_state import FrameConfirmation, SessionCooldown


class FrameConfirmationTests(unittest.TestCase):
    def test_confirms_after_required_consecutive_frames(self) -> None:
        confirmer = FrameConfirmation(required_frames=3)
        confirmed = []
        for _ in range(3):
            confirmer.start_frame()
            confirmed.append(confirmer.observe("Nitin"))
            confirmer.finish_frame()

        self.assertEqual(confirmed, [None, None, "Nitin"])

    def test_unknown_frame_resets_progress(self) -> None:
        confirmer = FrameConfirmation(required_frames=3)
        confirmer.start_frame()
        confirmer.observe("Nitin")
        confirmer.finish_frame()

        confirmer.start_frame()
        confirmer.observe(None)
        confirmer.finish_frame()

        self.assertEqual(confirmer.progress("Nitin"), 0)

    def test_switching_identity_resets_original_progress(self) -> None:
        confirmer = FrameConfirmation(required_frames=3)
        confirmer.start_frame()
        confirmer.observe("Nitin")
        confirmer.finish_frame()

        confirmer.start_frame()
        confirmer.observe("Other")
        confirmer.finish_frame()

        self.assertEqual(confirmer.progress("Nitin"), 0)
        self.assertEqual(confirmer.progress("Other"), 1)


class SessionCooldownTests(unittest.TestCase):
    def test_blocks_name_until_cooldown_expires(self) -> None:
        cooldown = SessionCooldown(seconds=10)
        self.assertTrue(cooldown.allows("Nitin", now=100.0))
        cooldown.record("Nitin", now=100.0)
        self.assertFalse(cooldown.allows("Nitin", now=105.0))
        self.assertTrue(cooldown.allows("Nitin", now=110.0))

    def test_names_have_independent_cooldowns(self) -> None:
        cooldown = SessionCooldown(seconds=10)
        cooldown.record("Nitin", now=100.0)
        self.assertTrue(cooldown.allows("Other", now=100.0))


if __name__ == "__main__":
    unittest.main()
