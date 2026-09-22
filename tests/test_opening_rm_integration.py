import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"


class OpeningRMIntegrationTests(unittest.TestCase):
    def test_opening_rpy_no_longer_declares_legacy_stat_variables(self):
        opening_stats = (GAME_DIR / "opening_stats.rpy").read_text(encoding="utf-8")

        self.assertNotIn("default stat_", opening_stats)
        self.assertIn("rm_opening_adjust_attribute", opening_stats)
        self.assertIn("rm_start_opening_allocation", opening_stats)
        self.assertIn("create_opening_draft_character", opening_stats)

    def test_opening_screen_reads_new_rm_opening_values(self):
        opening_screen = (GAME_DIR / "screens_opening_system.rpy").read_text(encoding="utf-8")

        for legacy_name in ("stat_con", "stat_str", "stat_dex", "stat_int", "stat_pow"):
            self.assertNotIn(legacy_name, opening_screen)
        self.assertIn('rm_opening_attribute_value("str")', opening_screen)
        self.assertIn('rm_opening_attribute_value("pow")', opening_screen)

    def test_opening_scene_starts_draft_before_identity_confirmation(self):
        opening_story = (GAME_DIR / "story" / "0-1-0.rpy").read_text(encoding="utf-8")

        self.assertLess(
            opening_story.index("rm_start_opening_allocation()"),
            opening_story.index("call screen opening_identity_document"),
        )

    def test_opening_adjust_action_does_not_return_from_screen(self):
        opening_stats = (GAME_DIR / "opening_stats.rpy").read_text(encoding="utf-8")

        self.assertIn("def opening_adjust_stat(attribute, delta):", opening_stats)
        self.assertIn("rm_opening_adjust_attribute(attribute, delta)", opening_stats)
        self.assertIn("return None", opening_stats)
        self.assertNotIn("return rm_opening_adjust_attribute(attribute, delta)", opening_stats)

    def test_legacy_opening_stats_logic_has_been_removed(self):
        self.assertFalse((GAME_DIR / "opening_stats_logic.py").exists())
        for path in list((PROJECT_ROOT / "tests").glob("*.py")) + list((PROJECT_ROOT / "tools").glob("*.py")):
            if path.name == "test_opening_rm_integration.py":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("opening_stats_logic", text, str(path))

    def test_attribute_dice_select_uses_scrollable_grid_for_full_rm_pool(self):
        attribute_screen = (GAME_DIR / "screens_attribute_checks.rpy").read_text(encoding="utf-8")

        self.assertNotIn("grid 3 2:", attribute_screen)
        self.assertIn("vpgrid:", attribute_screen)
        self.assertIn("cols 3", attribute_screen)


if __name__ == "__main__":
    unittest.main()
