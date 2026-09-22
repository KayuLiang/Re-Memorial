import re
import struct
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
SCREENS_PATH = GAME_DIR / "screens.rpy"
STORY_HUD_PATH = GAME_DIR / "screens_story_hud.rpy"
HOSPITAL_STORY_PATH = GAME_DIR / "story" / "1-1-2.rpy"
UI_ASSET_DIR = GAME_DIR / "gui" / "story_ui"


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


def renpy_define_int(source, name):
    match = re.search(rf"(?m)^define\s+{re.escape(name)}\s+=\s+(\d+)\s*$", source)
    if not match:
        raise AssertionError(f"integer define {name!r} not found")
    return int(match.group(1))


class NotebookDialogueUiTests(unittest.TestCase):
    def test_say_screen_uses_centered_bleed_canvas_layers(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        say = block_with_header(source, "screen say(who, what):")
        surface = block_with_header(source, "screen quick_menu():")
        self.assertIn('gui/hud_flat/notebook_page.svg', surface)
        self.assertIn('gui/hud_flat/photo_mount.svg', say)
        self.assertIn('照片待绘', say)
        self.assertNotIn('rm_hud_portrait', say)
        self.assertNotIn('phone_panel', say)
        self.assertNotIn('ui_notebook_canvas', say)
        self.assertIn('use quick_menu', say)
        self.assertIn('QueueEvent("dismiss_unfocused")', say)
        self.assertIn('id "what"', say)

    def test_bleed_canvas_transform_uses_qhd_scale_centering(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        transform_block = block_with_header(source, "transform story_ui_bleed_canvas:")

        self.assertIn("zoom (2.0 / 3.0)", transform_block)
        self.assertIn("xalign 0.5", transform_block)
        self.assertIn("yalign 0.5", transform_block)

    def test_say_text_uses_dedicated_window_separate_from_decorations(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        say = block_with_header(source, "screen say(who, what):")
        window = block_with_header(say, "window:")
        self.assertIn('id "window"', window)
        self.assertIn('id "what"', window)
        self.assertNotIn('imagebutton', window)
        self.assertIn("xpos notebook_dialogue_x", window)
        self.assertIn("ypos notebook_dialogue_y", window)
        self.assertIn("xsize notebook_dialogue_width", window)
        self.assertIn("color RM_HUD_INK", window)

    def test_notebook_dialogue_layout_constants_clear_portrait_area(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        x = renpy_define_int(source, "notebook_dialogue_x")
        y = renpy_define_int(source, "notebook_dialogue_y")
        width = renpy_define_int(source, "notebook_dialogue_width")
        self.assertGreaterEqual(x, 91 + 213 + 32)
        self.assertLessEqual(x + width, 2133)
        self.assertEqual(y, 1173)

    def test_name_is_larger_than_body_and_centered_within_title_row(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        say = block_with_header(source, "screen say(who, what):")
        name = block_with_header(say, 'text who:')
        body = block_with_header(source, 'style notebook_say_dialogue is say_dialogue:')
        self.assertIn('yalign .5', name)
        self.assertIn('size 51', name)
        self.assertIn('size 43', body)
        self.assertIn('xysize (notebook_dialogue_width, 75)', say)
        flat = (GAME_DIR / 'ui/rm_hud_flat.rpy').read_text(encoding='utf-8')
        self.assertNotIn('crop=', flat)

    def test_dialogue_controls_are_five_aligned_icon_tabs(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        quick_block = block_with_header(source, "screen quick_menu():")
        controls = re.findall(r'\("([a-z-]+)", "([^"]+)", (\d+),', quick_block)
        self.assertEqual([row[1] for row in controls], ['历史', '隐藏 UI', '自动', '快进', '设置'])
        self.assertIn('HideInterface()', quick_block)
        self.assertIn('background None', quick_block)
        self.assertIn('hover_background None', quick_block)
        self.assertIn('alt caption', quick_block)
        self.assertIn('renpy.is_selected(target)', quick_block)
        self.assertIn('xysize (96, 117)', quick_block)
        self.assertIn('RM_HUD_DIALOGUE_Y - 96', quick_block)
        self.assertIn('at notebook_tab_pull', quick_block)
        self.assertLess(quick_block.index('button:'), quick_block.index('add "gui/hud_flat/notebook_page.svg"'))
        self.assertNotIn('text "AUTO"', quick_block)
        self.assertEqual([int(row[2]) for row in controls], [1931, 2037, 2144, 2251, 2357])
        for removed_action in ('Rollback()', 'QuickSave()', 'QuickLoad()', 'ShowMenu("save")'):
            self.assertNotIn(removed_action, quick_block)
        height = renpy_define_int(source, "notebook_dialogue_height")
        flat = (GAME_DIR / 'ui/rm_hud_flat.rpy').read_text(encoding='utf-8')
        self.assertEqual(renpy_define_int(flat, 'RM_HUD_DIALOGUE_Y') + height, 1382)
        for icon, _, x in controls:
            self.assertLessEqual(int(x) + 96, 2453)
            for state in ('idle', 'hover', 'selected'):
                asset = (GAME_DIR / 'gui/hud_flat' / ('dialogue_' + icon + '_' + state + '.svg')).read_text(encoding='utf-8')
                self.assertIn('viewBox="0 0 72 88"', asset)
                self.assertIn('translate(16 4) scale(.15625)', asset)
                self.assertNotIn('<polyline points=', asset)
                self.assertNotIn('clipPath id="graphite"', asset)

    def test_touch_and_desktop_share_controls_without_a_detached_overlay(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        self.assertEqual(source.count('screen quick_menu():'), 1)
        self.assertNotIn('config.overlay_screens.append("quick_menu")', source)
        self.assertIn('use quick_menu', block_with_header(source, 'screen say(who, what):'))

    def test_narration_lines_do_not_show_player_name_as_speaker(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        say_block = block_with_header(source, "screen say(who, what):")

        self.assertIn("if who is not None:", say_block)
        self.assertNotIn("else:", say_block)
        self.assertNotIn("player_name", say_block)

    def test_reference_ui_assets_exist(self):
        expected_assets = (
            "ui_dialogue_backdrop.png",
            "ui_phone_canvas.png",
            "ui_notebook_canvas.png",
            "ui_pen_canvas.png",
            "ui_portrait_frame_canvas.png",
            "ui_name_tape_canvas.png",
            "ui_paperclip_canvas.png",
            "ui_top_status.png",
            "ui_btn_character_idle.png",
            "ui_btn_character_hover.png",
            "ui_btn_inventory_idle.png",
            "ui_btn_inventory_hover.png",
            "ui_btn_medicine_idle.png",
            "ui_btn_medicine_hover.png",
        )

        for filename in expected_assets:
            with self.subTest(filename=filename):
                path = UI_ASSET_DIR / filename
                self.assertTrue(path.is_file(), path)
                self.assertGreater(path.stat().st_size, 1000)

    def test_bleed_canvas_assets_keep_source_dimensions(self):
        expected_assets = (
            "ui_dialogue_backdrop.png",
            "ui_phone_canvas.png",
            "ui_notebook_canvas.png",
            "ui_pen_canvas.png",
            "ui_portrait_frame_canvas.png",
            "ui_name_tape_canvas.png",
            "ui_paperclip_canvas.png",
        )

        for filename in expected_assets:
            with self.subTest(filename=filename):
                data = (UI_ASSET_DIR / filename).read_bytes()
                width, height = struct.unpack(">II", data[16:24])
                bit_depth = data[24]
                color_type = data[25]
                self.assertEqual((width, height), (4224, 2376))
                self.assertEqual(bit_depth, 8)
                self.assertEqual(color_type, 6)

    def test_old_textbox_background_is_no_longer_used_for_desktop_say_window(self):
        source = SCREENS_PATH.read_text(encoding="utf-8")
        window_style = block_with_header(source, "style window:")

        self.assertNotIn('background Image("gui/textbox.png"', window_style)
        self.assertIn("background None", window_style)

    def test_top_status_overlay_exists_for_mockup_status_bar(self):
        source = STORY_HUD_PATH.read_text(encoding="utf-8")
        self.assertIn('config.overlay_screens.append("top_status")', source)
        self.assertIn("use rm_flat_status", source)
        flat = (GAME_DIR / "ui/rm_hud_flat.rpy").read_text(encoding="utf-8")
        for helper in ("rm_status_mood_value()", "rm_status_energy_points()", "rm_status_energy_max()"):
            self.assertIn(helper, flat)
        self.assertIn("RM_HUD_ENERGY_WIDTH = 480", flat)
        self.assertIn("RM_HUD_TRACK_WIDTH = 720", flat)

    def test_story_unlocks_ui_at_corresponding_beats(self):
        source = HOSPITAL_STORY_PATH.read_text(encoding="utf-8")

        medicine_index = source.index('$ inventory.append("药盒")')
        phone_index = source.index('$ inventory.append("手机")')
        time_index = source.index("call story_time_transition")

        self.assertGreater(
            source.index("call unlock_story_status_hud"),
            time_index,
        )
        self.assertGreater(
            source.index("call unlock_character_panel_button"),
            source.index("call unlock_story_status_hud"),
        )
        self.assertGreater(
            source.index("call unlock_medicine_button"),
            medicine_index,
        )
        self.assertGreater(
            source.index("call unlock_inventory_button"),
            medicine_index,
        )
        self.assertLess(source.index("call unlock_character_panel_button"), medicine_index)
        self.assertGreater(phone_index, medicine_index)


if __name__ == "__main__":
    unittest.main()
