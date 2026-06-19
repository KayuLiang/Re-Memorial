import ast
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


def block_with_header(source, stripped_header, start_line=0):
    lines = source.splitlines()
    for index in range(start_line, len(lines)):
        if lines[index].strip() != stripped_header:
            continue

        indent = len(lines[index]) - len(lines[index].lstrip(" "))
        block = [lines[index]]
        for nested_index in range(index + 1, len(lines)):
            line = lines[nested_index]
            if line.strip():
                nested_indent = len(line) - len(line.lstrip(" "))
                if nested_indent <= indent:
                    break
            block.append(line)

        return "\n".join(block), index

    raise AssertionError(f"block {stripped_header!r} not found")


def direct_child_lines(block):
    lines = block.splitlines()
    header_indent = len(lines[0]) - len(lines[0].lstrip(" "))
    child_indent = header_indent + 4
    return [
        line.strip()
        for line in lines[1:]
        if line.strip() and len(line) - len(line.lstrip(" ")) == child_indent
    ]


def parse_renpy_dict(source, definition_name):
    match = re.search(
        rf"(?m)^\s*define\s+{re.escape(definition_name)}\s*=\s*",
        source,
    )
    if match is None:
        raise AssertionError(f"define {definition_name} = not found")

    start = -1
    in_single_quote = False
    in_double_quote = False
    in_comment = False
    escaped = False

    for index in range(match.end(), len(source)):
        char = source[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if escaped:
            escaped = False
            continue
        if char == "\\" and (in_single_quote or in_double_quote):
            escaped = True
            continue
        if in_single_quote:
            if char == "'":
                in_single_quote = False
            continue
        if in_double_quote:
            if char == '"':
                in_double_quote = False
            continue
        if char == "#":
            in_comment = True
            continue
        if char == "'":
            in_single_quote = True
            continue
        if char == '"':
            in_double_quote = True
            continue
        if char == "{":
            start = index
            break

    if start == -1:
        raise AssertionError(f"define {definition_name} = has no opening brace")

    depth = 0
    end = None
    in_single_quote = False
    in_double_quote = False
    in_comment = False
    escaped = False
    for index in range(start, len(source)):
        char = source[index]
        if in_comment:
            if char == "\n":
                in_comment = False
            continue
        if escaped:
            escaped = False
            continue
        if char == "\\" and (in_single_quote or in_double_quote):
            escaped = True
            continue
        if in_single_quote:
            if char == "'":
                in_single_quote = False
            continue
        if in_double_quote:
            if char == '"':
                in_double_quote = False
            continue
        if char == "#":
            in_comment = True
            continue
        if char == "'":
            in_single_quote = True
            continue
        if char == '"':
            in_double_quote = True
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise ValueError(f"define {definition_name} = has unbalanced braces")
            if depth == 0:
                end = index + 1
                break

    if end is None:
        raise ValueError(f"define {definition_name} = has unbalanced braces")

    return ast.literal_eval(source[start:end])


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

    def test_parse_renpy_dict_preserves_extra_modes_and_keys(self):
        sample_source = '''
define crt_mode_settings = {
    "subtle": {
        "scanline": 0.22,
        "noise": 0.18,
        "flicker": 0.012,
        "jitter": 0,
    },
    "interference": {
        "scanline": 0.46,
        "noise": 0.42,
        "flicker": 0.045,
        "jitter": 8,
    },
    "shutdown": {
        "scanline": 0.75,
        "noise": 0.78,
        "flicker": 0.18,
        "jitter": 22,
    },
    "bonus": {
        "scanline": 0.91,
        "noise": 0.33,
        "flicker": 0.07,
        "jitter": 3,
        "phase": "extra",
    },
}
'''

        parsed = parse_renpy_dict(sample_source, "crt_mode_settings")

        self.assertIn("bonus", parsed)
        self.assertEqual(parsed["bonus"]["phase"], "extra")

    def test_parse_renpy_dict_scans_nested_braces_without_stopping_early(self):
        sample_source = '''
define crt_mode_settings = {
    "outer": {
        "inner": {
            "scanline": 0.12,
            "noise": 0.34,
        },
        "flicker": 0.56,
    },
    "tail": 9,
}
'''

        parsed = parse_renpy_dict(sample_source, "crt_mode_settings")

        self.assertEqual(parsed["outer"]["inner"]["scanline"], 0.12)
        self.assertEqual(parsed["outer"]["flicker"], 0.56)
        self.assertEqual(parsed["tail"], 9)

    def test_parse_renpy_dict_ignores_braces_inside_strings_comments_and_escapes(self):
        sample_source = r'''
define crt_mode_settings = {
    "quoted": {
        "text": "brace in string } and escaped quote \" { still string",
        'single': 'literal { brace and escaped quote \' }',
        "value": 7, # comment closes nothing }
    },
    # full line comment with stray brace {
    "tail": {
        "nested": 3,
    },
}
'''

        parsed = parse_renpy_dict(sample_source, "crt_mode_settings")

        self.assertEqual(
            {
                "quoted": {
                    "text": 'brace in string } and escaped quote " { still string',
                    "single": "literal { brace and escaped quote ' }",
                    "value": 7,
                },
                "tail": {
                    "nested": 3,
                },
            },
            parsed,
        )

    def test_crt_screen_accepts_mode_and_keeps_overlay_behavior(self):
        self.assertIn('screen crt_effect(mode="subtle"):', self.source)
        self.assertRegex(
            self.source,
            r'crt_mode_settings\.get\(\s*mode,\s*crt_mode_settings\["subtle"\]\s*\)',
        )
        self.assertRegex(self.source, r"(?m)^\s*modal\s+False\s*$")
        self.assertRegex(self.source, r"(?m)^\s*zorder\s+1000\s*$")

    def test_crt_mode_settings_define_all_presets_and_parameters(self):
        expected_settings = {
            "subtle": {
                "scanline": 0.22,
                "noise": 0.18,
                "flicker": 0.012,
                "jitter": 0,
            },
            "interference": {
                "scanline": 0.46,
                "noise": 0.42,
                "flicker": 0.045,
                "jitter": 8,
            },
            "shutdown": {
                "scanline": 0.75,
                "noise": 0.78,
                "flicker": 0.18,
                "jitter": 22,
            },
        }

        parsed_settings = parse_renpy_dict(self.source, "crt_mode_settings")
        self.assertEqual(expected_settings, parsed_settings)

    def test_crt_horizontal_jitter_is_defined_and_applied(self):
        self.assertIn("transform crt_horizontal_jitter(amount=0):", self.source)
        self.assertRegex(self.source, r"(?m)^\s*xoffset\s+0\s*$")
        self.assertIn("xoffset amount", self.source)
        self.assertIn("xoffset -amount", self.source)

    def test_crt_screen_wraps_jitter_in_clipped_outer_fixed_and_inner_overscan_fixed(self):
        overscan_match = re.search(
            r"(?m)^\s*define\s+crt_overscan\s*=\s*(\d+)\s*$",
            self.source,
        )
        self.assertIsNotNone(overscan_match)
        self.assertGreaterEqual(int(overscan_match.group(1)), 22)

        screen_block, _ = block_with_header(
            self.source,
            'screen crt_effect(mode="subtle"):',
        )
        outer_fixed, outer_index = block_with_header(screen_block, "fixed:")
        outer_children = direct_child_lines(outer_fixed)
        self.assertEqual(
            [
                "xsize config.screen_width",
                "ysize config.screen_height",
                "clipping True",
                "fixed:",
            ],
            outer_children[:4],
        )
        self.assertNotIn(
            'at crt_horizontal_jitter(settings["jitter"])',
            outer_children,
        )

        inner_fixed, _ = block_with_header(screen_block, "fixed:", start_line=outer_index + 1)
        inner_children = direct_child_lines(inner_fixed)
        self.assertEqual(
            "xsize config.screen_width + crt_overscan * 2",
            inner_children[0],
        )
        self.assertEqual("ysize config.screen_height", inner_children[1])
        self.assertEqual("xpos -crt_overscan", inner_children[2])
        self.assertEqual(
            'at crt_horizontal_jitter(settings["jitter"])',
            inner_children[3],
        )

    def test_crt_layers_render_inside_overscan_fixed(self):
        screen_block, _ = block_with_header(
            self.source,
            'screen crt_effect(mode="subtle"):',
        )
        _, outer_fixed_index = block_with_header(screen_block, "fixed:")
        inner_fixed, _ = block_with_header(screen_block, "fixed:", start_line=outer_fixed_index + 1)

        self.assertIn('add "images/effects/crt_scanlines.png":', inner_fixed)
        self.assertIn("xsize config.screen_width + crt_overscan * 2", inner_fixed)
        self.assertIn("ysize config.screen_height", inner_fixed)
        self.assertIn('add "crt_noise_cycle":', inner_fixed)
        self.assertIn('add Solid("#ffffff"):', inner_fixed)

    def test_crt_noise_cycle_and_transforms_remain_wired_to_screen(self):
        expected_fragments = (
            "image crt_noise_cycle:",
            '"images/effects/crt_noise_01.png"',
            '"images/effects/crt_noise_02.png"',
            '"images/effects/crt_noise_03.png"',
            "transform crt_scanline_scroll(speed=6.0):",
            "transform crt_flicker(strength=0.025):",
            "at crt_scanline_scroll(crt_scroll_speed)",
            'at crt_flicker(settings["flicker"])',
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

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
