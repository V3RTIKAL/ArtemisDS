from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
GAME = ROOT / "app/src/main/java/com/limelight/Game.java"


class SecondaryDisplayOrchestrationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = GAME.read_text(encoding="utf-8")

    def test_game_owns_and_shows_secondary_presentation(self):
        self.assertIn("SecondaryDisplayPresentation secondaryDisplayPresentation", self.source)
        self.assertIn("secondaryDisplayPresentation.show()", self.source)

    def test_second_decoder_bridge_is_armed_before_connection_start(self):
        arm = self.source.index("MoonBridge.setupSecondDisplayBridge(")
        start = self.source.index("conn.start(")
        self.assertLess(arm, start)

    def test_connection_waits_for_both_requested_surfaces(self):
        self.assertIn("primarySurfaceReady && secondarySurfaceReady", self.source)
        self.assertIn("maybeStartConnection()", self.source)

    def test_secondary_surface_detaches_before_presentation_dismissal(self):
        detach = self.source.index("MoonBridge.detachSecondDisplayBridge()")
        dismiss = self.source.index("secondaryDisplayPresentation.dismiss()")
        self.assertLess(detach, dismiss)


if __name__ == "__main__":
    unittest.main()
