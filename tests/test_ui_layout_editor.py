import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
LAYOUT_DATA_PATH = GAME_DIR / "ui" / "rm_ui_layout_data.rpy"
LAYOUT_EDITOR_PATH = GAME_DIR / "ui" / "rm_ui_layout_editor.rpy"
TEST_LABEL_PATH = GAME_DIR / "story" / "9-9-9-test-flow.rpy"


class UiLayoutEditorTests(unittest.TestCase):
    def test_dice_select_layout_data_defines_required_elements_and_fields(self):
        source = LAYOUT_DATA_PATH.read_text(encoding="utf-8")

        self.assertIn("default rm_ui_layouts = {", source)
        self.assertIn('"dice_select": {', source)

        for element_id in (
            "background",
            "clock_face",
            "clock_hand",
            "mood_bar",
            "mood_cursor",
            "energy_bar_green",
            "energy_bar_gray",
            "energy_cursor",
            "status_panel_base",
            "status_note_1",
            "status_note_2",
            "main_clipboard",
            "dice_card_blank",
            "dice_icon_d6",
            "confirm_button",
            "detail_popup_blank",
        ):
            with self.subTest(element_id=element_id):
                self.assertIn(f'"{element_id}": {{', source)

        for field in ("image", "x", "y", "w", "h", "z", "alpha", "rotate", "locked", "visible"):
            self.assertIn(f'"{field}":', source)

    def test_layout_editor_screen_exposes_controls_and_visual_helpers(self):
        source = LAYOUT_EDITOR_PATH.read_text(encoding="utf-8")

        self.assertIn('screen rm_ui_layout_editor(layout_name="dice_select"):', source)
        self.assertIn("rm_ui_layout_sorted_items(layout_name)", source)
        self.assertIn("SetScreenVariable(\"selected_id\"", source)
        self.assertIn("rm_ui_layout_selected_info(layout_name, selected_id)", source)
        self.assertIn("rm_ui_layout_draw_grid", source)
        self.assertIn("rm_ui_layout_draw_safe_frame", source)
        self.assertIn("rm_ui_layout_draw_center_lines", source)
        self.assertIn("renpy.get_mouse_pos()", source)

        for key_name in (
            "K_LEFT",
            "K_RIGHT",
            "K_UP",
            "K_DOWN",
            "shift_K_LEFT",
            "shift_K_RIGHT",
            "shift_K_UP",
            "shift_K_DOWN",
            "ctrl_K_LEFT",
            "ctrl_K_RIGHT",
            "ctrl_K_UP",
            "ctrl_K_DOWN",
            "K_q",
            "K_e",
            "K_a",
            "K_d",
            "K_PAGEUP",
            "K_PAGEDOWN",
            "K_TAB",
            "K_DELETE",
            "K_g",
            "K_h",
            "K_l",
            "K_r",
            "K_s",
            "K_ESCAPE",
        ):
            with self.subTest(key_name=key_name):
                self.assertIn(f'key "{key_name}"', source)

    def test_layout_editor_functions_mutate_save_and_copy_layout(self):
        source = LAYOUT_EDITOR_PATH.read_text(encoding="utf-8")

        for function_name in (
            "rm_ui_layout_move_selected",
            "rm_ui_layout_resize_selected",
            "rm_ui_layout_rotate_selected",
            "rm_ui_layout_alpha_selected",
            "rm_ui_layout_z_selected",
            "rm_ui_layout_toggle_visible",
            "rm_ui_layout_toggle_locked",
            "rm_ui_layout_reset_selected",
            "rm_ui_layout_select_next",
            "save_ui_layout_to_json",
            "rm_ui_layout_copy_text",
        ):
            with self.subTest(function_name=function_name):
                self.assertIn(f"def {function_name}(", source)

        self.assertIn("game/debug_output/ui_layout_", source)
        self.assertIn("ui_layout_dice_select.json", source)
        self.assertIn("json.dump", source)
        self.assertIn("renpy.set_clipboard", source)
        self.assertIn("renpy.log", source)

    def test_debug_label_opens_layout_editor(self):
        source = TEST_LABEL_PATH.read_text(encoding="utf-8")

        self.assertIn("label test_rm_ui_layout_editor:", source)
        self.assertIn('call screen rm_ui_layout_editor("dice_select")', source)
        self.assertIn("return", source)


if __name__ == "__main__":
    unittest.main()
