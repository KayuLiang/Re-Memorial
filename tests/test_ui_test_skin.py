import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
UI_TEST_SKIN_PATH = GAME_DIR / "screens_ui_test_skin.rpy"
TEST_STORY_PATH = GAME_DIR / "story" / "9-9-9-test-flow.rpy"
STORY_HUD_PATH = GAME_DIR / "screens_story_hud.rpy"
SCREENS_PATH = GAME_DIR / "screens.rpy"
ATTRIBUTE_CHECKS_PATH = GAME_DIR / "screens_attribute_checks.rpy"
TEST_SCHEDULES_PATH = GAME_DIR / "systems" / "rm_test_schedules.rpy"
UI_TEST_ASSET_DIR = GAME_DIR / "gui" / "ui_test_skin"


def block_with_header(source, stripped_header):
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != stripped_header:
            continue

        indent = len(line) - len(line.lstrip(" "))
        block = [line]
        for nested in lines[index + 1:]:
            if nested.strip():
                nested_indent = len(nested) - len(nested.lstrip(" "))
                if nested_indent <= indent:
                    break
            block.append(nested)
        return "\n".join(block)

    raise AssertionError(f"{stripped_header!r} not found")


class UiTestSkinTests(unittest.TestCase):
    def test_processed_ui_test_skin_assets_exist_as_transparent_pngs(self):
        expected_assets = (
            "dialogue_photo_avatar.png",
            "dialogue_paper.png",
            "name_tape.png",
            "clock_face.png",
            "clock_hand.png",
            "mood_bar.png",
            "mood_cursor.png",
            "dice_check_panel.png",
            "check_stage.png",
            "dice_list.png",
            "dice_card.png",
            "option_button.png",
        )

        for filename in expected_assets:
            with self.subTest(filename=filename):
                path = UI_TEST_ASSET_DIR / filename
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 1000)
                data = path.read_bytes()
                self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
                width, height = struct.unpack(">II", data[16:24])
                color_type = data[25]
                self.assertGreater(width, 40)
                self.assertGreater(height, 40)
                self.assertEqual(color_type, 6)

    def test_ui_test_skin_screens_are_defined_and_use_skin_assets(self):
        source = UI_TEST_SKIN_PATH.read_text(encoding="utf-8")

        self.assertIn("default rm_ui_test_skin_active = False", source)
        self.assertIn('config.overlay_screens.append("rm_ui_test_skin_hud")', source)
        self.assertIn("screen rm_ui_test_dialogue_preview():", source)
        self.assertIn("screen rm_ui_test_hud_preview():", source)
        self.assertIn("screen rm_ui_test_skin_hud():", source)
        self.assertIn("def rm_ui_test_mood_cursor_offset(value):", source)
        self.assertIn("rm_status_mood_value()", source)
        self.assertIn("story_hud_clock_rotation(current_time_minutes)", source)

        for filename in (
            "dialogue_photo_avatar.png",
            "dialogue_paper.png",
            "name_tape.png",
            "clock_face.png",
            "clock_hand.png",
            "mood_bar.png",
            "mood_cursor.png",
        ):
            with self.subTest(filename=filename):
                self.assertIn(f"gui/ui_test_skin/{filename}", source)

    def test_ui_test_menu_exposes_dialogue_hud_and_skinned_check_flows(self):
        source = TEST_STORY_PATH.read_text(encoding="utf-8")
        menu_block = block_with_header(source, "label rm_ui_test_menu:")
        regular_test_block = block_with_header(source, "label rm_test_flow_start:")

        self.assertIn('"对话框UI":', menu_block)
        self.assertIn("call screen rm_ui_test_dialogue_preview", menu_block)
        self.assertIn('"时钟与心境条":', menu_block)
        self.assertIn("call screen rm_ui_test_hud_preview", menu_block)
        self.assertIn("$ rm_ui_test_skin_active = True", menu_block)
        self.assertIn("$ rm_ui_test_skin_active = False", menu_block)
        self.assertIn('"检定界面":', menu_block)
        self.assertIn("jump rm_test_flow_loop", menu_block)
        self.assertIn("$ rm_ui_test_skin_active = False", regular_test_block)

    def test_formal_say_and_top_status_do_not_directly_use_test_skin_assets(self):
        say_source = SCREENS_PATH.read_text(encoding="utf-8")
        hud_source = STORY_HUD_PATH.read_text(encoding="utf-8")
        say_block = block_with_header(say_source, "screen say(who, what):")
        top_status_block = block_with_header(hud_source, "screen top_status():")

        self.assertNotIn("gui/ui_test_skin", say_block)
        self.assertNotIn("gui/ui_test_skin", top_status_block)
        self.assertIn("not rm_ui_test_skin_active", top_status_block)

    def test_dice_and_test_schedule_styles_are_gated_by_ui_test_skin_flag(self):
        attribute_source = ATTRIBUTE_CHECKS_PATH.read_text(encoding="utf-8")
        schedule_source = TEST_SCHEDULES_PATH.read_text(encoding="utf-8")

        for filename in (
            "dice_check_panel.png",
            "check_stage.png",
            "dice_list.png",
            "dice_card.png",
            "option_button.png",
        ):
            with self.subTest(filename=filename):
                self.assertIn(f"gui/ui_test_skin/{filename}", attribute_source + schedule_source)

        self.assertGreaterEqual((attribute_source + schedule_source).count("rm_ui_test_skin_active"), 8)
        self.assertIn("ConditionSwitch", attribute_source)
        self.assertIn("ConditionSwitch", schedule_source)


if __name__ == "__main__":
    unittest.main()
