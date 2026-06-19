import re
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_DIR / "game"
OPENING_STATS_PATH = GAME_DIR / "opening_stats.rpy"


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


if __name__ == "__main__":
    unittest.main()
