import re
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_DIR / "game"
OPENING_STATS_PATH = GAME_DIR / "opening_stats.rpy"
CRT_EFFECT_PATH = GAME_DIR / "crt_effect.rpy"


def function_block(source, function_name):
    match = re.search(
        rf"(?ms)^    def {re.escape(function_name)}\s*\([^)]*\):.*?"
        rf"(?=^    def |\Z)",
        source,
    )
    if match is None:
        return ""
    return match.group(0)


class OpeningStatsContractTests(unittest.TestCase):
    def test_stat_defaults_have_one_exact_canonical_value(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(GAME_DIR.glob("*.rpy"))
        )

        expected_defaults = {
            "con": 3,
            "str": 1,
            "dex": 1,
            "int": 1,
            "pow": 1,
        }
        for stat_name, value in expected_defaults.items():
            with self.subTest(stat_name=stat_name):
                declarations = re.findall(
                    rf"(?m)^\s*default\s+stat_{stat_name}\s*=\s*(.*?)\s*$",
                    source,
                )
                self.assertEqual([str(value)], declarations)

    def test_opening_stats_defines_public_wrappers(self):
        self.assertTrue(
            OPENING_STATS_PATH.is_file(),
            "game/opening_stats.rpy must exist",
        )
        source = OPENING_STATS_PATH.read_text(encoding="utf-8")
        function_names = (
            "opening_stat_points_remaining",
            "opening_can_adjust_stat",
            "opening_adjust_stat",
            "opening_stats_complete",
            "get_base_stat",
            "get_effective_stat",
            "get_attribute_dice",
            "perform_attribute_check",
            "_validate_stat_name",
        )

        for function_name in function_names:
            with self.subTest(function_name=function_name):
                self.assertRegex(
                    source,
                    rf"(?m)^\s*def\s+{function_name}\s*\(",
                )

    def test_public_stat_readers_validate_names(self):
        source = OPENING_STATS_PATH.read_text(encoding="utf-8")

        for function_name in (
            "get_base_stat",
            "get_attribute_dice",
            "perform_attribute_check",
        ):
            with self.subTest(function_name=function_name):
                block = function_block(source, function_name)
                self.assertIn(
                    "_validate_stat_name(stat_name)",
                    block,
                )

    def test_attribute_checks_remain_unavailable(self):
        source = OPENING_STATS_PATH.read_text(encoding="utf-8")
        block = function_block(source, "perform_attribute_check")

        self.assertIn(
            "return attribute_check_unavailable(stat_name)",
            block,
        )
        self.assertNotIn('"available": True', source)


class CrtEffectContractTests(unittest.TestCase):
    def setUp(self):
        self.source = CRT_EFFECT_PATH.read_text(encoding="utf-8")

    def test_crt_screen_accepts_mode_and_keeps_overlay_behavior(self):
        self.assertIn('screen crt_effect(mode="subtle"):', self.source)
        self.assertRegex(
            self.source,
            r'crt_mode_settings\.get\(\s*mode,\s*crt_mode_settings\["subtle"\]\s*\)',
        )
        self.assertRegex(self.source, r"(?m)^\s*modal\s+False\s*$")
        self.assertRegex(self.source, r"(?m)^\s*zorder\s+1000\s*$")

    def test_crt_mode_settings_define_all_presets_and_parameters(self):
        self.assertIn("define crt_mode_settings =", self.source)
        expected_settings = {
            "subtle": {
                "scanline": "0.22",
                "noise": "0.18",
                "flicker": "0.012",
                "jitter": "0",
            },
            "interference": {
                "scanline": "0.46",
                "noise": "0.42",
                "flicker": "0.045",
                "jitter": "8",
            },
            "shutdown": {
                "scanline": "0.75",
                "noise": "0.78",
                "flicker": "0.18",
                "jitter": "22",
            },
        }

        for mode, settings in expected_settings.items():
            with self.subTest(mode=mode):
                mode_match = re.search(
                    rf'(?ms)^\s*"{mode}"\s*:\s*\{{(.*?)^\s*\}},?\s*$',
                    self.source,
                )
                self.assertIsNotNone(mode_match)
                mode_block = mode_match.group(1)
                for key, value in settings.items():
                    self.assertRegex(
                        mode_block,
                        rf'(?m)^\s*"{key}"\s*:\s*{re.escape(value)}\s*,?\s*$',
                    )

    def test_crt_horizontal_jitter_is_defined_and_applied(self):
        self.assertIn("transform crt_horizontal_jitter(amount=0):", self.source)
        self.assertRegex(self.source, r"(?m)^\s*xoffset\s+0\s*$")
        self.assertIn("xoffset amount", self.source)
        self.assertIn("xoffset -amount", self.source)
        self.assertIn(
            'at crt_horizontal_jitter(settings["jitter"])',
            self.source,
        )

    def test_crt_screen_uses_each_mode_parameter(self):
        expected_uses = (
            'alpha settings["scanline"]',
            'alpha settings["noise"]',
            'crt_flicker(settings["flicker"])',
            'crt_horizontal_jitter(settings["jitter"])',
        )
        for expected_use in expected_uses:
            with self.subTest(expected_use=expected_use):
                self.assertIn(expected_use, self.source)


if __name__ == "__main__":
    unittest.main()
