import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
GUI_PATH = GAME_DIR / "gui.rpy"
SCREENS_PATH = GAME_DIR / "screens.rpy"
OPENING_SYSTEM_PATH = GAME_DIR / "screens_opening_system.rpy"
COMMON_TRANSLATION_PATH = GAME_DIR / "tl" / "None" / "common.rpym"
PRIMARY_FONT_NAME = "fonts/source-han-serif/SourceHanSerifSC-SemiBold.otf"
FALLBACK_FONT_NAME = "SourceHanSansLite.ttf"
UI_FONT_VARIABLE = "rememorial_ui_font"
UI_FONT_GROUP_EXPR = (
    'FontGroup().add("fonts/source-han-serif/SourceHanSerifSC-SemiBold.otf", None, None)'
    '.add("SourceHanSansLite.ttf", None, None)'
)
DIALOGUE_FONT_VARIABLE = "rememorial_dialogue_font"
DIALOGUE_FONT_GROUP_EXPR = (
    'FontGroup().add("fonts/source/HuiwenMincho.otf", None, None)'
    '.add("SourceHanSansLite.ttf", None, None)'
)


class FontConfigurationTests(unittest.TestCase):
    def test_primary_and_fallback_font_files_exist(self):
        source_dir = GAME_DIR / "fonts" / "source"

        self.assertTrue((source_dir / "HuiwenMincho.otf").is_file())
        self.assertGreater((source_dir / "HuiwenMincho.otf").stat().st_size, 1_000_000)
        self.assertTrue((GAME_DIR / FALLBACK_FONT_NAME).is_file())
        self.assertGreater((GAME_DIR / FALLBACK_FONT_NAME).stat().st_size, 1_000_000)
        self.assertTrue((source_dir / "FONT_SOURCES.md").is_file())
        self.assertGreater((GAME_DIR / PRIMARY_FONT_NAME).stat().st_size, 1_000_000)
        license_text = (GAME_DIR / "fonts/source-han-serif/LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn("SIL OPEN FONT LICENSE Version 1.1", license_text)

    def test_ui_font_group_uses_source_han_serif_with_existing_fallback(self):
        source = GUI_PATH.read_text(encoding="utf-8")

        self.assertIn(
            f"define {UI_FONT_VARIABLE} = {UI_FONT_GROUP_EXPR}",
            source,
        )

    def test_gui_controls_use_ui_font_group(self):
        source = GUI_PATH.read_text(encoding="utf-8")

        for name in (
            "gui.text_font",
            "gui.interface_text_font",
            "gui.button_text_font",
            "gui.choice_button_text_font",
        ):
            with self.subTest(name=name):
                self.assertRegex(
                    source,
                    rf"(?m)^define\s+{re.escape(name)}\s+=\s+{UI_FONT_VARIABLE}$",
                )

    def test_story_body_keeps_huiwen_font_group(self):
        source = GUI_PATH.read_text(encoding="utf-8")
        self.assertIn(f"define {DIALOGUE_FONT_VARIABLE} = {DIALOGUE_FONT_GROUP_EXPR}", source)
        self.assertRegex(source, rf"(?m)^define\s+gui\.dialogue_text_font\s+=\s+{DIALOGUE_FONT_VARIABLE}$")
        screens = SCREENS_PATH.read_text(encoding="utf-8")
        for name in ("history_text", "nvl_thought", "bubble_what"):
            self.assertIn(f"style {name}:\n    font {DIALOGUE_FONT_VARIABLE}", screens)

    def test_names_keep_original_font_without_synthetic_bold(self):
        source = GUI_PATH.read_text(encoding="utf-8")
        self.assertRegex(source, rf"(?m)^define\s+gui\.name_text_font\s+=\s+{DIALOGUE_FONT_VARIABLE}$")
        screens = SCREENS_PATH.read_text(encoding="utf-8")
        say_screen = screens.split("screen say(who, what):", 1)[1].split("init python:", 1)[0]
        self.assertEqual(say_screen.count('id "who"'), 1)
        self.assertNotIn("bold True", say_screen)
        self.assertIn('style say_label:\n    properties gui.text_properties("name", accent=True)\n    bold False', screens)
        for name in ("history_name_text", "bubble_who"):
            self.assertIn(f"style {name}:\n    font {DIALOGUE_FONT_VARIABLE}\n    bold False", screens)

    def test_runtime_ui_references_use_shared_ui_font_group(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                GUI_PATH,
                SCREENS_PATH,
                OPENING_SYSTEM_PATH,
                COMMON_TRANSLATION_PATH,
            )
        )

        self.assertNotIn("DejaVuSans.ttf", combined)
        self.assertNotIn("ReMemorialLayeredMing.ttf", combined)
        self.assertIn(f'font {UI_FONT_VARIABLE}', combined)
        self.assertIn(f"define opening_document_font = {UI_FONT_VARIABLE}", combined)
        self.assertIn(f"define gui.system_font = {UI_FONT_GROUP_EXPR}", combined)


if __name__ == "__main__":
    unittest.main()
