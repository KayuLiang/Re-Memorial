import re
import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
STORY_HUD_PATH = GAME_DIR / "screens_story_hud.rpy"
RM_UI_PATH = GAME_DIR / "systems" / "rm_ui.rpy"
PHONE_SCREENS_PATH = GAME_DIR / "screens_phone.rpy"
INVENTORY_SCREENS_PATH = GAME_DIR / "screens_inventory.rpy"
HOSPITAL_STORY_PATH = GAME_DIR / "story" / "1-1-2.rpy"
UI_ASSET_DIR = GAME_DIR / "gui" / "story_ui"


class StoryHudUnlockTests(unittest.TestCase):
    def test_story_hud_overlay_is_registered_once(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        self.assertEqual(
            1,
            source.count('config.overlay_screens.append("story_hud_buttons")'),
        )

    def test_unlock_state_defaults_start_hidden(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        for variable in (
            "story_hud_status_unlocked",
            "story_hud_character_panel_unlocked",
            "story_hud_inventory_unlocked",
            "story_hud_medicine_unlocked",
        ):
            with self.subTest(variable=variable):
                self.assertRegex(
                    source,
                    rf"(?m)^default\s+{re.escape(variable)}\s+=\s+False\s*$",
                )

    def test_status_hud_uses_new_canvas_assets_and_dynamic_values(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")
        flat = (GAME_DIR / "ui/rm_hud_flat.rpy").read_text(encoding="utf-8")
        self.assertIn("use rm_flat_status", source)
        for asset in ("mood_track.svg", "lightning_track.svg", "heart_reserved.svg", "star_reserved.svg"):
            self.assertIn(asset, flat)
        for helper in ("rm_status_mood_value()", "rm_status_energy_points()", "rm_status_energy_max()", "rm_status_mood_tooltip()", "rm_status_energy_tooltip()"):
            self.assertIn(helper, flat)
        self.assertIn("if rm_hud_visible() and story_hud_status_unlocked:", flat)
        self.assertIn("RM_HUD_ENERGY_WIDTH = 480", flat)
        self.assertIn("RM_HUD_TRACK_WIDTH = 720", flat)
        self.assertNotIn("star_fill.svg", flat)

    def test_status_hud_helpers_define_required_ranges(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        self.assertIn("def story_hud_clamp(value, minimum, maximum):", source)
        self.assertIn("def story_hud_mood_cursor_offset(value):", source)
        self.assertIn("story_hud_clamp(value, -200, 200)", source)
        self.assertIn("400.0", source)
        self.assertIn("def story_hud_energy_fill_width(points, maximum):", source)
        self.assertIn("def story_hud_clock_rotation(minutes):", source)

    def test_new_hud_canvas_assets_exist_with_source_dimensions(self):
        expected_assets = (
            "ui_btn_character_canvas.png",
            "ui_btn_inventory_canvas.png",
            "ui_btn_medicine_canvas.png",
            "ui_clock_canvas.png",
            "ui_clock_hand_canvas.png",
            "ui_mood_bar_canvas.png",
            "ui_mood_cursor_canvas.png",
            "ui_energy_empty_canvas.png",
            "ui_energy_full_canvas.png",
        )

        for filename in expected_assets:
            with self.subTest(filename=filename):
                path = UI_ASSET_DIR / filename
                self.assertTrue(path.is_file(), path)
                data = path.read_bytes()
                width, height = struct.unpack(">II", data[16:24])
                self.assertEqual((width, height), (4224, 2376))
                self.assertEqual(data[24], 8)
                self.assertEqual(data[25], 6)

    def test_story_unlock_labels_set_each_hud_button(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        expected = {
            "unlock_character_panel_button": "character_panel",
            "unlock_inventory_button": "inventory",
            "unlock_medicine_button": "medicine",
        }
        for label, button_id in expected.items():
            with self.subTest(label=label):
                self.assertRegex(source, rf"(?m)^label\s+{label}\s*:\s*$")
                self.assertIn(f'$ story_hud_unlock("{button_id}")', source)

    def test_story_hud_buttons_only_render_after_unlocks(self):
        source = (GAME_DIR / "ui/rm_hud_flat.rpy").read_text(encoding="utf-8")
        for flag in ("story_hud_character_panel_unlocked", "story_hud_inventory_unlocked", "story_hud_medicine_unlocked"):
            self.assertIn("if " + flag + ":", source)
        self.assertIn('if "手机" in inventory:', source)
        for index, icon in enumerate(("pill", "device-mobile", "backpack", "dice-five", "user-square")):
            self.assertIn('rm_hud_nav_item({}, "{}"'.format(index, icon), source)
        self.assertIn('Show("character_panel", start_tab="dice")', source)
        self.assertIn('Show("medicine_panel")', source)
        self.assertIn('Show("phone_panel")', source)
        self.assertIn('Show("inventory_panel")', source)

    def test_character_panel_reads_numeric_backend_summary_and_dice_pool(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        self.assertIn('screen character_panel(start_tab="summary"):', source)
        self.assertIn("$ summary = rm_status_character_summary()", source)
        self.assertIn("$ dice_pool = rm_status_dice_pool_summary()", source)
        self.assertIn("textbutton \"概览\"", source)
        self.assertIn("textbutton \"骰组\"", source)
        for label in ("Mood", "病程状态", "精力", "属性"):
            with self.subTest(label=label):
                self.assertIn(label, source)
        self.assertNotIn("人物资料占位", source)

    def test_rm_ui_wrappers_expose_hud_ready_backend_values(self):
        source = RM_UI_PATH.read_text(encoding="utf-8")

        for helper in (
            "rm_status_character_summary",
            "rm_status_dice_pool_summary",
            "rm_status_mood_value",
            "rm_status_energy_points",
            "rm_status_energy_max",
            "rm_status_mood_tooltip",
            "rm_status_energy_tooltip",
        ):
            with self.subTest(helper=helper):
                self.assertIn("def {}(".format(helper), source)
        self.assertIn("rm_core.character_summary(character)", source)
        self.assertIn("rm_core.dice_pool_summary(character)", source)

    def test_story_1_1_2_unlocks_status_and_character_after_time_then_medicine_later(self):
        source = HOSPITAL_STORY_PATH.read_text(encoding="utf-8")

        time_index = source.index("call story_time_transition")
        status_index = source.index("call unlock_story_status_hud")
        character_index = source.index("call unlock_character_panel_button")
        medicine_item_index = source.index('$ inventory.append("药盒")')
        inventory_unlock_index = source.index("call unlock_inventory_button")
        medicine_unlock_index = source.index("call unlock_medicine_button")

        self.assertGreater(status_index, time_index)
        self.assertGreater(character_index, status_index)
        self.assertLess(character_index, medicine_item_index)
        self.assertGreater(inventory_unlock_index, medicine_item_index)
        self.assertGreater(medicine_unlock_index, medicine_item_index)

    def test_legacy_side_button_overlays_are_not_registered(self):
        phone_source = PHONE_SCREENS_PATH.read_text(encoding="utf-8")
        inventory_source = INVENTORY_SCREENS_PATH.read_text(encoding="utf-8")

        self.assertNotIn('config.overlay_screens.append("phone_button")', phone_source)
        self.assertNotIn(
            'config.overlay_screens.append("inventory_button")',
            inventory_source,
        )
        self.assertNotIn("screen phone_button():", phone_source)
        self.assertNotIn("screen inventory_button():", inventory_source)

    def test_hud_has_no_legacy_shadow_state_or_unused_lock_helper(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")

        for legacy_name in (
            "day_count",
            "mood_value",
            "energy_points",
            "max_energy_points",
        ):
            with self.subTest(legacy_name=legacy_name):
                self.assertNotRegex(
                    source,
                    rf"(?m)^default\s+{re.escape(legacy_name)}\s+=",
                )
        self.assertNotRegex(source, r"(?m)^\s*def\s+story_hud_lock\s*\(")

    def test_inventory_panel_accepts_initial_category_for_medicine_entry(self):
        source = INVENTORY_SCREENS_PATH.read_text(encoding="utf-8")

        self.assertIn('screen inventory_panel(start_category="all"):', source)
        self.assertIn("default current_category = start_category", source)


if __name__ == "__main__":
    unittest.main()
