import ast
import re
import textwrap
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_DIR / "game"
OPENING_STATS_PATH = GAME_DIR / "opening_stats.rpy"
CRT_EFFECT_PATH = GAME_DIR / "crt_effect.rpy"
OPENING_SYSTEM_PATH = GAME_DIR / "screens_opening_system.rpy"
OPENING_SEQUENCE_PATH = GAME_DIR / "opening_sequence.rpy"
OPENING_AUDIO_README_PATH = GAME_DIR / "audio" / "opening" / "README.md"
INVENTORY_SCREENS_PATH = GAME_DIR / "screens_inventory.rpy"
PHONE_SCREENS_PATH = GAME_DIR / "screens_phone.rpy"
BASE_SCREENS_PATH = GAME_DIR / "screens.rpy"


def function_block(source, function_name):
    match = re.search(
        rf"(?ms)^    def {re.escape(function_name)}\s*\([^)]*\):.*?"
        rf"(?=^    def |^\S|\Z)",
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


def parse_style_tuple(block, property_name):
    match = re.search(
        rf"(?m)^\s*{re.escape(property_name)}\s+(.+?)\s*$",
        block,
    )
    if match is None:
        raise AssertionError(f"{property_name} not found in block")

    value = match.group(1).strip()
    if value.startswith("Borders(") and value.endswith(")"):
        parts = [part.strip() for part in value[8:-1].split(",") if part.strip()]
        return tuple(int(part) for part in parts)

    parsed = ast.literal_eval(value)
    if isinstance(parsed, int):
        return (parsed,)
    return tuple(parsed)


def parse_define_scalar(source, definition_name):
    match = re.search(
        rf"(?m)^\s*define\s+{re.escape(definition_name)}\s*=\s*(.+?)\s*$",
        source,
    )
    if match is None:
        raise AssertionError(f"define {definition_name} = not found")
    return ast.literal_eval(match.group(1).strip())


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

    def test_crt_scanlines_use_overscan_width_double_height_and_scroll_transform(self):
        screen_block, _ = block_with_header(
            self.source,
            'screen crt_effect(mode="subtle"):',
        )
        _, outer_fixed_index = block_with_header(screen_block, "fixed:")
        inner_fixed, _ = block_with_header(screen_block, "fixed:", start_line=outer_fixed_index + 1)
        scanline_block, _ = block_with_header(
            inner_fixed,
            'add "images/effects/crt_scanlines.png":',
        )
        scanline_children = direct_child_lines(scanline_block)

        self.assertEqual(
            [
                "xsize config.screen_width + crt_overscan * 2",
                "ysize config.screen_height * 2",
                'alpha settings["scanline"]',
                "at crt_scanline_scroll(crt_scroll_speed)",
            ],
            scanline_children,
        )

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


class OpeningSystemShellContractTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(
            OPENING_SYSTEM_PATH.is_file(),
            "game/screens_opening_system.rpy must exist",
        )
        self.source = OPENING_SYSTEM_PATH.read_text(encoding="utf-8")

    def test_opening_shell_defines_exact_color_tokens(self):
        expected_tokens = {
            "opening_color_desktop": "#6f8078",
            "opening_color_desktop_dark": "#46534f",
            "opening_color_border": "#5b8db8",
            "opening_color_border_dark": "#315f88",
            "opening_color_paper": "#e7e4d9",
            "opening_color_phosphor": "#a8c7aa",
        }

        for token_name, value in expected_tokens.items():
            with self.subTest(token_name=token_name):
                self.assertRegex(
                    self.source,
                    rf'(?m)^define {re.escape(token_name)} = "{re.escape(value)}"$',
                )

    def test_opening_shell_defines_core_screens_and_scope_transform(self):
        expected_fragments = (
            "screen opening_system_desktop(body_screen, body_args=None):",
            "screen opening_window_frame(title, body_screen, body_args=None):",
            "screen opening_oscilloscope():",
            "screen opening_shell_preview_body():",
            "transform opening_scope_scroll(distance=opening_scope_wave_span):",
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

    def test_opening_shell_window_uses_dynamic_body_screen(self):
        window_block, _ = block_with_header(
            self.source,
            "screen opening_window_frame(title, body_screen, body_args=None):",
        )

        self.assertRegex(
            window_block,
            r"(?m)^\s*use\s+expression\s+body_screen\b",
        )
        self.assertRegex(
            window_block,
            r"(?m)^\s*use\s+expression\s+body_screen\s+pass\s+\(\*body_args\)\s*$",
        )
        self.assertNotRegex(
            window_block,
            r"(?m)^\s*use\s+expression\s+body_screen\s+pass\s+\(\*\*body_args\)\s*$",
        )
        self.assertNotIn("len(body_args)", window_block)
        self.assertNotIn("暂不支持超过四个", window_block)

    def test_opening_shell_window_border_is_uniform_and_explicit(self):
        outer_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_window_outer_frame is frame:",
        )
        inner_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_window_inner_frame is frame:",
        )

        self.assertIn("background Solid(opening_color_border_dark)", outer_style_block)
        padding = parse_style_tuple(outer_style_block, "padding")
        self.assertIn(padding, {(4, 4), (4, 4, 4, 4)})
        inner_padding = parse_style_tuple(inner_style_block, "padding")
        self.assertIn(inner_padding, {(0, 0), (0, 0, 0, 0)})
        self.assertNotIn("background Solid(opening_color_border)", inner_style_block)
        self.assertNotIn("background Solid(opening_color_border_dark)", inner_style_block)

    def test_opening_shell_clips_main_body_region(self):
        style_block, _ = block_with_header(
            self.source,
            "style opening_shell_window_body_frame is frame:",
        )

        self.assertIn("clipping True", style_block)
        self.assertIn("xfill True", style_block)
        self.assertIn("yfill True", style_block)

    def test_title_bar_uses_win7_blue_and_exposes_window_controls(self):
        title_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_title_bar_frame is frame:",
        )
        window_block, _ = block_with_header(
            self.source,
            "screen opening_window_frame(title, body_screen, body_args=None):",
        )

        self.assertIn("background Solid(opening_color_border)", title_style_block)
        self.assertIn('text "—"', window_block)
        self.assertIn('text "□"', window_block)
        self.assertIn('text "×"', window_block)

    def test_taskbar_has_single_top_highlight_without_second_upper_border(self):
        desktop_block, _ = block_with_header(
            self.source,
            "screen opening_system_desktop(body_screen, body_args=None):",
        )
        taskbar_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_taskbar_frame is frame:",
        )
        taskbar_content_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_taskbar_content_frame is frame:",
        )
        time_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_taskbar_time_text is gui_text:",
        )
        status_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_taskbar_status_text is gui_text:",
        )

        highlight_lines = re.findall(
            r'(?m)^\s*add Solid\([^)\n]+\)\s+xpos 0 ypos 0 xsize config\.screen_width ysize 2\s*$',
            desktop_block,
        )
        self.assertEqual(1, len(highlight_lines))
        self.assertNotRegex(
            desktop_block,
            r'(?m)^\s*add Solid\([^)\n]+\)\s+xpos 0 ypos (?:1|2) xsize config\.screen_width ysize (?:1|2)\s*$',
        )
        self.assertIn('text "⊕"', desktop_block)
        self.assertIn('text "特殊治疗管理系统"', desktop_block)
        self.assertIn('text "13:30"', desktop_block)
        self.assertEqual((44,), parse_style_tuple(taskbar_style_block, "ysize"))
        self.assertEqual((14, 6, 14, 6), parse_style_tuple(taskbar_content_style_block, "padding"))
        time_size = parse_style_tuple(time_style_block, "size")[0]
        status_size = parse_style_tuple(status_style_block, "size")[0]
        self.assertLessEqual(time_size + status_size, 32)

    def test_preview_body_keeps_paper_placeholder_and_scope_signature(self):
        preview_block, _ = block_with_header(
            self.source,
            "screen opening_shell_preview_body():",
        )
        paper_style_block, _ = block_with_header(
            self.source,
            "style opening_shell_preview_paper_frame is frame:",
        )

        self.assertIn("use opening_oscilloscope", preview_block)
        self.assertNotIn("background Solid(opening_color_paper)", preview_block)
        self.assertIn("background Solid(opening_color_paper)", paper_style_block)
        paper_width = parse_style_tuple(paper_style_block, "xsize")
        self.assertEqual((1030,), paper_width)

    def test_scope_screen_uses_local_scroll_transform_and_metrics(self):
        scope_block, _ = block_with_header(
            self.source,
            "screen opening_oscilloscope():",
        )

        self.assertIn("opening_scope_scroll", scope_block)
        self.assertIn('text "HR', scope_block)
        self.assertIn('text "SpO2', scope_block)
        self.assertIn('text "GAIN', scope_block)

    def test_scope_wave_span_constant_drives_scroll_and_duplicate_segment(self):
        transform_block, _ = block_with_header(
            self.source,
            "transform opening_scope_scroll(distance=opening_scope_wave_span):",
        )
        scope_block, _ = block_with_header(
            self.source,
            "screen opening_oscilloscope():",
        )
        wave_span = parse_define_scalar(self.source, "opening_scope_wave_span")

        self.assertEqual(476, wave_span)
        self.assertIn("linear 4.8 xoffset -distance", transform_block)
        self.assertIn("xpos opening_scope_wave_span", scope_block)
        self.assertIn("xsize opening_scope_wave_span * 2", scope_block)

    def test_scope_geometry_uses_consistent_450_pixel_budget(self):
        scope_block, _ = block_with_header(
            self.source,
            "screen opening_oscilloscope():",
        )

        self.assertIn("xsize 450", scope_block)
        self.assertIn("xpos 18", scope_block)
        self.assertIn("xsize 450 ysize 1", scope_block)
        self.assertIn("xpos 18", scope_block)
        self.assertIn("xsize opening_scope_wave_span * 2", scope_block)
        self.assertNotIn("xsize 452", scope_block)

    def test_opening_shell_does_not_depend_on_legacy_medical_wave_scroll(self):
        self.assertNotIn("medical_wave_scroll", self.source)


class OpeningPreSystemSequenceContractTests(unittest.TestCase):
    def setUp(self):
        self.system_source = OPENING_SYSTEM_PATH.read_text(encoding="utf-8")
        self.sequence_source = (
            OPENING_SEQUENCE_PATH.read_text(encoding="utf-8")
            if OPENING_SEQUENCE_PATH.is_file()
            else ""
        )
        self.inventory_source = INVENTORY_SCREENS_PATH.read_text(encoding="utf-8")
        self.phone_source = PHONE_SCREENS_PATH.read_text(encoding="utf-8")
        self.base_screens_source = BASE_SCREENS_PATH.read_text(encoding="utf-8")

    def test_opening_sequence_file_and_required_labels_exist(self):
        self.assertTrue(
            OPENING_SEQUENCE_PATH.is_file(),
            "game/opening_sequence.rpy must exist",
        )

        for label_name in (
            "complete_opening_sequence",
            "opening_scene_00",
            "opening_scene_01",
            "opening_scene_02",
            "opening_scene_03",
            "opening_scene_04",
            "opening_scene_05",
            "opening_scene_06",
            "opening_scene_07",
            "opening_scene_08",
            "opening_scene_09",
            "opening_scene_10",
            "opening_scene_11",
        ):
            with self.subTest(label_name=label_name):
                self.assertIn(f"label {label_name}:", self.sequence_source)

        for absent_label in (
            "opening_scene_12",
            "opening_scene_13",
            "opening_scene_14",
        ):
            with self.subTest(absent_label=absent_label):
                self.assertNotIn(f"label {absent_label}:", self.sequence_source)

    def test_required_opening_text_is_present_exactly(self):
        expected_fragments = (
            "【免责声明】",
            "本作品为虚构故事。作品中的人物、团体、事件、医疗与心理描写均经过艺术加工；若与现实相似，均属巧合。",
            "本作品涉及精神疾病、创伤记忆、失忆、血腥暴力、自伤意念、死亡及其他可能引起不适的内容。相关描写不构成医学、心理、法律或其他专业建议，也不应在现实中模仿或尝试。",
            "本作品包含闪烁画面、快速转场、画面抖动、强对比图像等视觉刺激。若您曾有癫痫、晕厥、光敏反应或相关病史，请在游玩前咨询专业医师。游玩中如出现头晕、恶心、视物异常、抽搐、意识模糊或其他不适，请立即停止游玩并寻求帮助。",
            "继续游玩即表示您已阅读并理解以上内容。",
            "TAP TO START",
            "弗洛，弗洛——",
            'fro "我听到有人在叫我的名字。"',
            "一阵急促的脚步声。",
            "重物落地的闷响。",
            "“现场安全，患者雄性，意识模糊——”",
        )

        combined = self.system_source + "\n" + self.sequence_source

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, combined)

    def test_opening_scene_00_uses_show_pause_hide_without_crt(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_00:")
        self.assertIn("show screen opening_disclaimer_one", block)
        self.assertRegex(
            block,
            r"(pause\s+3(?:\.0)?\s+hard\b|renpy\.pause\(\s*3(?:\.0)?\s*,\s*hard\s*=\s*True\s*,\s*modal\s*=\s*False\s*\))",
        )
        self.assertIn("modal=False", block)
        self.assertIn("hide screen opening_disclaimer_one", block)
        self.assertNotIn("call screen opening_disclaimer_one", block)
        self.assertNotIn("crt_effect", block)

    def test_opening_scene_01_routes_no_to_main_menu_and_keeps_crt_off(self):
        screen_block, _ = block_with_header(
            self.system_source,
            "screen opening_disclaimer_two():",
        )
        scene_block, _ = block_with_header(self.sequence_source, "label opening_scene_01:")

        self.assertIn('textbutton "是"', screen_block)
        self.assertIn("action Return(True)", screen_block)
        self.assertIn('textbutton "否"', screen_block)
        self.assertIn("MainMenu(confirm=False)", screen_block)
        self.assertIn("call screen opening_disclaimer_two", scene_block)
        self.assertNotIn("crt_effect", screen_block)
        self.assertNotIn("crt_effect", scene_block)

    def test_tap_to_start_supports_keyboard_and_mouse(self):
        screen_block, _ = block_with_header(
            self.system_source,
            "screen opening_tap_to_start():",
        )

        self.assertIn('key "dismiss" action Return()', screen_block)
        self.assertRegex(
            screen_block,
            r'(?m)^\s*(mousearea|button):\s*$',
        )
        self.assertIn("action Return()", screen_block)

    def test_opening_scene_03_waits_once_then_plays_three_drops(self):
        scene_block, _ = block_with_header(self.sequence_source, "label opening_scene_03:")

        self.assertIn("call screen opening_water_wait", scene_block)
        self.assertEqual(
            3,
            scene_block.count("call screen opening_water_drop(auto=True)"),
        )
        self.assertNotIn("call screen opening_water_drop(auto=False)", scene_block)

    def test_scene_05_shows_loading_body_and_subtle_crt(self):
        scene_block, _ = block_with_header(self.sequence_source, "label opening_scene_05:")
        self.assertIn(
            'show screen opening_system_desktop("opening_loading_body")',
            scene_block,
        )
        self.assertIn('show screen crt_effect(mode="subtle")', scene_block)

    def test_required_pre_system_screens_exist(self):
        for header in (
            "screen opening_disclaimer_one():",
            "screen opening_disclaimer_two():",
            "screen opening_tap_to_start():",
            "screen opening_water_wait():",
            "screen opening_water_drop(auto=True):",
            "screen opening_memory_overlay(lines):",
            "screen opening_loading_body():",
        ):
            with self.subTest(header=header):
                self.assertIn(header, self.system_source)

    def test_memory_overlay_uses_half_black_mask_and_accumulates_lines(self):
        overlay_block, _ = block_with_header(
            self.system_source,
            "screen opening_memory_overlay(lines):",
        )
        scene_block, _ = block_with_header(self.sequence_source, "label opening_scene_06:")

        self.assertIn('add Solid("#00000080")', overlay_block)
        self.assertIn("for line in lines:", overlay_block)
        self.assertIn("text line", overlay_block)
        self.assertEqual(3, scene_block.count("lines.append("))
        self.assertGreaterEqual(
            scene_block.count("show screen opening_memory_overlay(lines)"),
            3,
        )

    def test_complete_sequence_temporarily_cleans_up_crt_and_system_screens(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label complete_opening_sequence:",
        )

        self.assertIn("call opening_scene_00", block)
        self.assertIn("hide screen crt_effect", block)
        self.assertIn("hide screen opening_system_desktop", block)

    def test_opening_scene_00_pause_uses_modal_false_to_avoid_modal_deadlock(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_00:")
        self.assertIn("renpy.pause(3.0, hard=True, modal=False)", block)

    def test_opening_system_desktop_uses_negative_zorder_below_dialogue(self):
        block, _ = block_with_header(
            self.system_source,
            "screen opening_system_desktop(body_screen, body_args=None):",
        )
        self.assertRegex(block, r"(?m)^\s*zorder\s+-\d+\s*$")
        self.assertNotIn("zorder 8", block)

    def test_opening_active_has_single_canonical_default(self):
        all_rpy = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(GAME_DIR.glob("*.rpy"))
        )
        declarations = re.findall(
            r"(?m)^\s*default\s+opening_active\s*=\s*(True|False)\s*$",
            all_rpy,
        )
        self.assertEqual(["False"], declarations)

    def test_complete_opening_sequence_sets_and_clears_opening_active(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label complete_opening_sequence:",
        )
        self.assertRegex(block, r"(?m)^\s*\$\s*opening_active\s*=\s*True\s*$")
        self.assertRegex(block, r"(?m)^\s*\$\s*opening_active\s*=\s*False\s*$")

    def test_opening_scene_06_continues_without_cleaning_desktop_or_crt(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_06:",
        )
        self.assertIn("jump opening_scene_07", block)
        self.assertNotIn("opening_active = False", block)
        self.assertNotIn("hide screen crt_effect", block)
        self.assertNotIn("hide screen opening_system_desktop", block)
        self.assertNotRegex(block, r"(?m)^\s*return\s*$")

    def test_scene_01_no_path_clears_opening_active_before_main_menu(self):
        block, _ = block_with_header(
            self.system_source,
            "screen opening_disclaimer_two():",
        )
        self.assertIn('SetVariable("opening_active", False)', block)
        self.assertIn("MainMenu(confirm=False)", block)

    def test_quick_menu_variants_hide_during_opening(self):
        quick_menu_blocks = []
        start_line = 0

        while True:
            try:
                block, index = block_with_header(
                    self.base_screens_source,
                    "screen quick_menu():",
                    start_line=start_line,
                )
            except AssertionError:
                break

            quick_menu_blocks.append(block)
            start_line = index + 1

        self.assertEqual(2, len(quick_menu_blocks))

        for block in quick_menu_blocks:
            with self.subTest(header=block.splitlines()[0]):
                self.assertRegex(
                    block,
                    r"if\s+quick_menu\s+and\s+not\s+opening_active\s*:",
                )

    def test_inventory_and_phone_overlay_buttons_hide_during_opening(self):
        inventory_block, _ = block_with_header(
            self.inventory_source,
            "screen inventory_button():",
        )
        phone_block, _ = block_with_header(
            self.phone_source,
            "screen phone_button():",
        )

        self.assertIn("and not opening_active", inventory_block)
        self.assertIn("and not opening_active", phone_block)


class OpeningMedicalConsentContractTests(unittest.TestCase):
    def setUp(self):
        self.system_source = OPENING_SYSTEM_PATH.read_text(encoding="utf-8")
        self.sequence_source = OPENING_SEQUENCE_PATH.read_text(encoding="utf-8")

    def test_safe_audio_helper_only_plays_loadable_paths_with_requested_options(self):
        block = function_block(self.system_source, "opening_play_sound")

        self.assertIn('def opening_play_sound(path, channel="sound", loop=False):', block)
        self.assertRegex(block, r"if\s+renpy\.loadable\(\s*path\s*\)\s*:")
        self.assertRegex(
            block,
            r"renpy\.music\.play\(\s*path\s*,\s*channel\s*=\s*channel\s*,\s*loop\s*=\s*loop\s*\)",
        )
        self.assertNotRegex(block, r"(?m)^\s*else\s*:")

    def test_opening_audio_readme_lists_stable_targets_and_silent_fallback(self):
        self.assertTrue(OPENING_AUDIO_README_PATH.is_file())
        readme = OPENING_AUDIO_README_PATH.read_text(encoding="utf-8")
        expected_files = (
            "electrical_burst.ogg",
            "water_drop_primary.ogg",
            "water_drop_soft.ogg",
            "footsteps_urgent.ogg",
            "heavy_impact.ogg",
            "emergency_radio.ogg",
            "wind_gap.ogg",
            "stretcher_wheels.ogg",
            "metal_scrape.ogg",
            "handoff_shout.ogg",
            "isolation_door.ogg",
            "keyboard_fast.ogg",
            "paper_flip.ogg",
            "electronic_low.ogg",
        )
        for filename in expected_files:
            with self.subTest(filename=filename):
                self.assertEqual(1, readme.count(filename))
        self.assertRegex(readme.lower(), r"silent fallback|silently")

    def test_medical_flow_screens_have_data_driven_records_notice_and_consent(self):
        for header in (
            "screen opening_loading_body():",
            "screen opening_records_body(progress, status_text):",
            "screen opening_notice_body(message):",
            "screen opening_consent_body():",
            "screen opening_consent_document():",
        ):
            with self.subTest(header=header):
                self.assertIn(header, self.system_source)

        records_block, _ = block_with_header(
            self.system_source,
            "screen opening_records_body(progress, status_text):",
        )
        self.assertIn("status_text", records_block)
        self.assertIn("progress", records_block)
        self.assertRegex(records_block, r"(bar\s+value|xsize\s+int\()[^\n]*progress")

    def test_consent_bottom_helper_uses_range_edge_and_four_pixel_tolerance(self):
        block = function_block(self.system_source, "opening_consent_at_bottom")

        self.assertIn("adjustment.range <= 0", block)
        self.assertIn("adjustment.value >= adjustment.range - 4", block)
        self.assertRegex(block, r"return\s+.*\bor\b")

    def test_consent_screen_binds_local_adjustment_and_gates_return_on_live_position(self):
        block, _ = block_with_header(
            self.system_source,
            "screen opening_consent_document():",
        )
        self.assertIn(
            "default consent_adjustment = ui.adjustment("
            "raw_changed=opening_consent_adjustment_changed)",
            block,
        )

        viewport_block, _ = block_with_header(block, "viewport:")
        for setting in (
            "yadjustment consent_adjustment",
            "mousewheel True",
            "draggable True",
            'scrollbars "vertical"',
        ):
            with self.subTest(setting=setting):
                self.assertIn(setting, viewport_block)

        button_block, _ = block_with_header(block, 'textbutton "下一页":')
        self.assertIn(
            "sensitive opening_consent_at_bottom(consent_adjustment)",
            button_block,
        )
        self.assertIn("action Return()", button_block)
        self.assertNotIn("SetScreenVariable", button_block)

    def test_consent_adjustment_callback_restarts_only_on_bottom_state_boundaries(self):
        block = function_block(
            self.system_source,
            "opening_consent_adjustment_changed",
        )
        self.assertTrue(block)

        class FakeRenpy:
            def __init__(self):
                self.restart_count = 0

            def restart_interaction(self):
                self.restart_count += 1

        class FakeAdjustment:
            range = 100

        fake_renpy = FakeRenpy()
        namespace = {"renpy": fake_renpy}
        exec(textwrap.dedent(block), namespace)
        callback = namespace["opening_consent_adjustment_changed"]
        adjustment = FakeAdjustment()

        self.assertIsNone(callback(adjustment, 95))
        self.assertEqual(0, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 96))
        self.assertEqual(1, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 97))
        self.assertEqual(1, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 100))
        self.assertEqual(1, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 95))
        self.assertEqual(2, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 95))
        self.assertEqual(2, fake_renpy.restart_count)

    def test_consent_adjustment_callback_treats_non_scrollable_document_as_bottom(self):
        block = function_block(
            self.system_source,
            "opening_consent_adjustment_changed",
        )

        class FakeRenpy:
            def __init__(self):
                self.restart_count = 0

            def restart_interaction(self):
                self.restart_count += 1

        class FakeAdjustment:
            range = 0

        fake_renpy = FakeRenpy()
        namespace = {"renpy": fake_renpy}
        exec(textwrap.dedent(block), namespace)
        callback = namespace["opening_consent_adjustment_changed"]
        adjustment = FakeAdjustment()

        self.assertIsNone(callback(adjustment, 0))
        self.assertEqual(1, fake_renpy.restart_count)
        self.assertIsNone(callback(adjustment, 0))
        self.assertEqual(1, fake_renpy.restart_count)

    def test_opening_foley_channel_is_registered_in_init_for_non_looping_sfx(self):
        init_block, _ = block_with_header(self.system_source, "init python:")

        self.assertIn(
            'renpy.music.register_channel('
            '"opening_foley", mixer="sfx", loop=False)',
            init_block,
        )

    def test_consent_document_contains_all_six_sections_and_required_original_text(self):
        required_text = (
            "市立精神卫生中心",
            "特殊治疗知情同意书",
            "姓名：弗洛；性别：男；年龄：24；病历号：████████；诊断：█████████████████；拟行治疗：███████；治疗日期：████年██月██日",
            "一、治疗目的",
            "因患者目前存在████、████、████及████能力下降等情况，拟实施本次治疗，以稳定精神状态、降低风险，并协助患者恢复基本生活与认知功能。",
            "二、治疗方式",
            "治疗过程中可能使用镇静、监测、████、精神状态校准及必要的辅助药物。具体方案将由医师根据患者情况调整。",
            "三、可能风险",
            "短暂████或███障碍；",
            "极少数情况下可能发生严重不良反应，甚至危及生命。",
            "四、替代方案",
            "患者及家属已知悉可选择药物治疗、心理治疗、观察治疗、转院治疗或暂缓治疗。但延误治疗可能导致病情加重或出现其他风险。",
            "五、信息核对",
            "上述信息一经签署，将作为本次治疗及后续系统评估的依据。如有遗漏、错误或隐瞒，患者及家属/监护人已知悉可能产生相应风险。",
            "姓名：弗洛；性别：男；年龄：24；ID：██████████████████",
            "初始属性（剩余可分配点数：x）",
            "力量 敏捷 体质 智力 意志",
            "六、患者声明",
            "本人自愿接受本次治疗。",
            "患者签名：______________；家属/监护人签名：______________；医师签名：______________；日期：████年██月██日",
            "患者已知悉并理解以上信息。",
            "请核对个人信息。",
            "请确认签署。",
        )
        for text in required_text:
            with self.subTest(text=text):
                self.assertIn(text, self.system_source)

        self.assertEqual(
            [f"{number}、" for number in "一二三四五六"],
            re.findall(r"[一二三四五六]、", self.system_source),
        )

    def test_scene_flow_runs_sequentially_from_six_through_eleven(self):
        expected_jumps = {
            "opening_scene_06": "opening_scene_07",
            "opening_scene_07": "opening_scene_08",
            "opening_scene_08": "opening_scene_09",
            "opening_scene_09": "opening_scene_10",
            "opening_scene_10": "opening_scene_11",
        }
        for scene, destination in expected_jumps.items():
            with self.subTest(scene=scene):
                block, _ = block_with_header(self.sequence_source, f"label {scene}:")
                self.assertIn(f"jump {destination}", block)
        self.assertNotIn("label opening_scene_12:", self.sequence_source)

    def test_scene_07_strengthens_crt_plays_burst_and_presents_both_notices(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_07:")

        self.assertIn('show screen crt_effect(mode="interference")', block)
        self.assertIn(
            'opening_play_sound("audio/opening/electrical_burst.ogg")',
            block,
        )
        first = block.index("精神卫生系统已介入。")
        second = block.index("载入中。")
        self.assertLess(first, second)
        self.assertNotIn("opening_active = False", block)

    def test_scene_08_updates_five_statuses_progress_and_safe_record_sounds(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_08:")
        statuses = (
            "正在整理病历……",
            "正在校准心境……",
            "正在归档记忆……",
            "正在写入访谈记录……",
            "正在恢复基础认知……",
        )
        positions = [block.index(status) for status in statuses]
        self.assertEqual(sorted(positions), positions)
        self.assertGreaterEqual(
            block.count('show screen opening_system_desktop("opening_records_body"'),
            5,
        )
        for sound in ("keyboard_fast.ogg", "paper_flip.ogg", "electronic_low.ogg"):
            with self.subTest(sound=sound):
                self.assertIn(f'audio/opening/{sound}', block)
        self.assertIn("show screen opening_flash_once", block)

    def test_scene_09_accumulates_exact_four_lines_and_plays_semantic_sounds(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_09:")
        exact_lines = (
            "风掠过车窗缝隙的尖啸。",
            "金属的滚轮快速摩擦地面的叮铃声，担架床吱呀好像就要散架。",
            "“交接！手术室准备！”",
            "然后是厚实的隔离门缓缓关上。",
        )
        self.assertEqual(4, block.count("lines.append("))
        positions = [block.index(line) for line in exact_lines]
        self.assertEqual(sorted(positions), positions)
        self.assertGreaterEqual(
            block.count("show screen opening_memory_overlay(lines)"),
            4,
        )
        for sound in (
            "wind_gap.ogg",
            "stretcher_wheels.ogg",
            "metal_scrape.ogg",
            "handoff_shout.ogg",
            "isolation_door.ogg",
        ):
            with self.subTest(sound=sound):
                self.assertIn(f'audio/opening/{sound}', block)
        door_position = block.index("isolation_door.ogg")
        self.assertRegex(block[door_position:], r"pause\s+0\.\d+")
        self.assertIn("with Dissolve(", block)

    def test_scene_03_plays_primary_then_two_soft_drops_without_changing_drop_count(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_03:")
        wait_position = block.index("call screen opening_water_wait")
        primary_call = 'opening_play_sound("audio/opening/water_drop_primary.ogg")'
        soft_call = 'opening_play_sound("audio/opening/water_drop_soft.ogg")'
        self.assertIn(primary_call, block)
        self.assertEqual(2, block.count(soft_call))
        primary_position = block.index(primary_call)
        soft_positions = [
            match.start()
            for match in re.finditer(
                re.escape(soft_call),
                block,
            )
        ]
        drop_positions = [
            match.start()
            for match in re.finditer(
                re.escape("call screen opening_water_drop(auto=True)"),
                block,
            )
        ]

        self.assertEqual(2, len(soft_positions))
        self.assertEqual(3, len(drop_positions))
        self.assertLess(wait_position, primary_position)
        self.assertLess(primary_position, drop_positions[0])
        self.assertLess(drop_positions[0], soft_positions[0])
        self.assertLess(soft_positions[0], drop_positions[1])
        self.assertLess(drop_positions[1], soft_positions[1])
        self.assertLess(soft_positions[1], drop_positions[2])

    def test_scene_06_plays_each_memory_sound_before_its_matching_line(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_06:")
        pairs = (
            ("footsteps_urgent.ogg", "一阵急促的脚步声。"),
            ("heavy_impact.ogg", "重物落地的闷响。"),
            ("emergency_radio.ogg", "“现场安全，患者雄性，意识模糊——”"),
        )

        for sound, line in pairs:
            with self.subTest(sound=sound):
                sound_call = f'opening_play_sound("audio/opening/{sound}")'
                self.assertIn(sound_call, block)
                sound_position = block.index(sound_call)
                line_position = block.index(f'lines.append("{line}")')
                self.assertLess(sound_position, line_position)

        self.assertEqual(3, block.count("lines.append("))
        self.assertGreaterEqual(
            block.count("show screen opening_memory_overlay(lines)"),
            3,
        )

    def test_scene_09_overlapping_wheels_and_scrape_use_distinct_channels(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_09:")

        self.assertIn(
            'opening_play_sound("audio/opening/stretcher_wheels.ogg")',
            block,
        )
        self.assertIn(
            'opening_play_sound('
            '"audio/opening/metal_scrape.ogg", channel="opening_foley")',
            block,
        )

    def test_scene_10_returns_to_subtle_crt_and_shows_exact_notice(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_10:")
        self.assertIn('show screen crt_effect(mode="subtle")', block)
        self.assertIn(
            "您好，这里是市立精神卫生中心服务系统，请仔细阅读术前须知。",
            block,
        )

    def test_scene_11_dialogue_calls_consent_then_temporarily_cleans_up(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_11:")
        expected_dialogue = (
            'fro "应该怎么做？"',
            'system "请滑动滚轮以阅读全文。"',
            'fro "然后呢？"',
            'system "点击屏幕下方的‘下一页’按钮。"',
        )
        positions = [block.index(line) for line in expected_dialogue]
        self.assertEqual(sorted(positions), positions)
        self.assertIn(
            'show screen opening_system_desktop("opening_consent_body")',
            block,
        )
        self.assertIn("call screen opening_consent_document", block)
        for cleanup in (
            "hide screen opening_memory_overlay",
            "hide screen crt_effect",
            "hide screen opening_system_desktop",
            "opening_active = False",
            "return",
        ):
            with self.subTest(cleanup=cleanup):
                self.assertIn(cleanup, block)


if __name__ == "__main__":
    unittest.main()
