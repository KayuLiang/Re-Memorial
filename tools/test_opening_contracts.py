import ast
import re
import textwrap
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_DIR / "game"
STORY_DIR = GAME_DIR / "story"
STORY_OPENING_PATH = STORY_DIR / "0-1-0.rpy"
STORY_DREAM_PATH = STORY_DIR / "1-1-1.rpy"
STORY_HOSPITAL_PATH = STORY_DIR / "1-1-2.rpy"
STORY_APARTMENT_PATH = STORY_DIR / "1-1-3.rpy"
OPENING_STATS_PATH = GAME_DIR / "opening_stats.rpy"
CRT_EFFECT_PATH = GAME_DIR / "crt_effect.rpy"
HUE_SEPARATION_EFFECT_PATH = GAME_DIR / "hue_separation_effect.rpy"
CRT_EFFECT_ASSET_PATHS = tuple(
    GAME_DIR / "images" / "effects" / filename
    for filename in (
        "crt_scanlines.png",
        "crt_noise_01.png",
        "crt_noise_02.png",
        "crt_noise_03.png",
    )
)
OPENING_SYSTEM_PATH = GAME_DIR / "screens_opening_system.rpy"
OPENING_SEQUENCE_PATH = STORY_OPENING_PATH
SCRIPT_PATH = GAME_DIR / "script.rpy"
MEDICAL_SCREENS_PATH = GAME_DIR / "screens_medical.rpy"
MEDICAL_SCREENS_COMPILED_PATH = GAME_DIR / "screens_medical.rpyc"
OPENING_AUDIO_README_PATH = GAME_DIR / "audio" / "opening" / "README.md"
CRT_ASSET_GENERATOR_PATH = PROJECT_DIR / "tools" / "generate_crt_assets.py"
INVENTORY_SCREENS_PATH = GAME_DIR / "screens_inventory.rpy"
PHONE_SCREENS_PATH = GAME_DIR / "screens_phone.rpy"
BASE_SCREENS_PATH = GAME_DIR / "screens.rpy"
OPTIONS_PATH = GAME_DIR / "options.rpy"
STORY_FILE_PATHS = {
    "0-1-0": STORY_OPENING_PATH,
    "1-1-1": STORY_DREAM_PATH,
    "1-1-2": STORY_HOSPITAL_PATH,
    "1-1-3": STORY_APARTMENT_PATH,
}


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


class ProjectVersionContractTests(unittest.TestCase):
    def test_project_version_is_initial_stable_baseline(self):
        source = OPTIONS_PATH.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r'(?m)^define config\.version = "0\.0\.0"$',
        )


class StoryFileOrganizationContractTests(unittest.TestCase):
    def test_numbered_story_files_exist(self):
        for story_id, story_path in STORY_FILE_PATHS.items():
            with self.subTest(story_id=story_id):
                self.assertTrue(story_path.is_file(), story_path)

    def test_script_contains_only_shared_declarations_and_entry(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("label start:", source)
        self.assertIn("jump story_0_1_0", source)
        self.assertNotIn("label mountain_memory_start:", source)
        self.assertNotIn('centered "20XX年', source)
        self.assertNotIn("opening_scene_00", source)

    def test_story_segments_use_stable_entry_labels_and_explicit_jumps(self):
        expected = {
            "0-1-0": (
                "label story_0_1_0:",
                "jump story_1_1_1",
            ),
            "1-1-1": (
                "label story_1_1_1:",
                "jump story_1_1_2",
            ),
            "1-1-2": (
                "label story_1_1_2:",
                "jump story_1_1_3",
            ),
            "1-1-3": (
                "label story_1_1_3:",
                "return",
            ),
        }

        for story_id, fragments in expected.items():
            source = STORY_FILE_PATHS[story_id].read_text(encoding="utf-8")
            with self.subTest(story_id=story_id):
                for fragment in fragments:
                    self.assertIn(fragment, source)

class OpeningStatsContractTests(unittest.TestCase):
    def test_legacy_stat_defaults_are_removed(self):
        source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(GAME_DIR.rglob("*.rpy"))
        )

        self.assertNotRegex(source, r"(?m)^\s*default\s+stat_(con|str|dex|int|pow)\s*=")

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
            "rm_opening_attribute_value",
            "rm_opening_adjust_attribute",
            "opening_stats_complete",
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
            "get_attribute_dice",
            "perform_attribute_check",
        ):
            with self.subTest(function_name=function_name):
                block = function_block(source, function_name)
                self.assertIn(
                    "_validate_stat_name(attribute)",
                    block,
                )

    def test_attribute_checks_use_rm_core_backend(self):
        source = OPENING_STATS_PATH.read_text(encoding="utf-8")
        block = function_block(source, "perform_attribute_check")

        self.assertIn("_rm_core.CheckSpec", block)
        self.assertIn("_rm_core.perform_check", block)
        self.assertNotIn("attribute_check_unavailable", source)


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
                "scanline": 0.40,
                "noise": 0.30,
                "flicker": 0.012,
                "jitter": 0,
            },
            "interference": {
                "scanline": 0.62,
                "noise": 0.50,
                "flicker": 0.045,
                "jitter": 11,
            },
            "shutdown": {
                "scanline": 0.82,
                "noise": 0.80,
                "flicker": 0.18,
                "jitter": 29,
            },
        }

        parsed_settings = parse_renpy_dict(self.source, "crt_mode_settings")
        self.assertEqual(expected_settings, parsed_settings)
        for parameter in ("scanline", "noise"):
            self.assertLess(
                parsed_settings["subtle"][parameter],
                parsed_settings["interference"][parameter],
            )
            self.assertLess(
                parsed_settings["interference"][parameter],
                parsed_settings["shutdown"][parameter],
            )

    def test_crt_scanline_generator_uses_four_pixel_lines_and_gaps(self):
        generator_source = CRT_ASSET_GENERATOR_PATH.read_text(encoding="utf-8")

        self.assertRegex(
            generator_source,
            r"(?m)^SCANLINE_SPACING\s*=\s*8\s*$",
        )
        self.assertRegex(
            generator_source,
            r"(?m)^SCANLINE_THICKNESS\s*=\s*4\s*$",
        )
        self.assertIn(
            "y % SCANLINE_SPACING < SCANLINE_THICKNESS",
            generator_source,
        )

    def test_crt_scanlines_scroll_at_one_third_speed(self):
        self.assertRegex(
            self.source,
            r"(?m)^define crt_scroll_speed = 18\.0$",
        )
        self.assertIn(
            "transform crt_scanline_scroll(speed=18.0):",
            self.source,
        )

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
            "transform crt_scanline_scroll(speed=18.0):",
            "transform crt_flicker(strength=0.025):",
            "at crt_scanline_scroll(crt_scroll_speed)",
            'at crt_flicker(settings["flicker"])',
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

    def test_all_crt_assets_referenced_by_the_filter_are_deliverable_files(self):
        for asset_path in CRT_EFFECT_ASSET_PATHS:
            with self.subTest(asset_path=asset_path):
                self.assertTrue(asset_path.is_file(), asset_path)
                self.assertGreater(asset_path.stat().st_size, 0)

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


class HueSeparationEffectContractTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(
            HUE_SEPARATION_EFFECT_PATH.is_file(),
            "game/hue_separation_effect.rpy must exist",
        )
        self.source = HUE_SEPARATION_EFFECT_PATH.read_text(encoding="utf-8")

    def test_public_api_and_modes_exist(self):
        self.assertIn(
            'def hue_separation_start(mode="steady", scope="scene"):',
            self.source,
        )
        self.assertIn("def hue_separation_stop():", self.source)
        self.assertIn('("steady", "glitch")', self.source)
        self.assertIn('("scene", "fullscreen")', self.source)

    def test_shader_and_camera_transform_exist(self):
        self.assertIn(
            'renpy.register_shader("rememorial.hue_separation"',
            self.source,
        )
        self.assertIn(
            "uniform float u_hue_separation_pixels;",
            self.source,
        )
        self.assertIn("uniform vec2 u_model_size;", self.source)
        self.assertIn("transform hue_separation_camera:", self.source)
        self.assertIn('shader "rememorial.hue_separation"', self.source)
        self.assertIn("function hue_separation_camera_update", self.source)

    def test_camera_redraws_only_when_strength_changes(self):
        camera_update = function_block(
            self.source,
            "hue_separation_camera_update",
        )
        begin_peak = function_block(
            self.source,
            "_hue_separation_begin_peak",
        )
        end_peak = function_block(
            self.source,
            "_hue_separation_end_peak",
        )

        self.assertNotIn("return 0", camera_update)
        self.assertIn("_hue_separation_refresh_cameras()", begin_peak)
        self.assertIn("_hue_separation_refresh_cameras()", end_peak)

    def test_strength_and_random_bounds_are_explicit(self):
        expected_fragments = (
            "define hue_separation_baseline_pixels = 4.0",
            "define hue_separation_peak_pixels_min = (32.0 / 3.0)",
            "define hue_separation_peak_pixels_max = 24.0",
            "define hue_separation_wait_min = 6.0",
            "define hue_separation_wait_max = 12.0",
            "define hue_separation_peak_duration_min = 0.1",
            "define hue_separation_peak_duration_max = 0.5",
        )
        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

    def test_start_replaces_controller_and_applies_requested_layers(self):
        start_block = function_block(self.source, "hue_separation_start")

        self.assertIn(
            'renpy.hide_screen("hue_separation_glitch_controller")',
            start_block,
        )
        self.assertIn('_hue_separation_clear_camera("master")', start_block)
        self.assertIn('_hue_separation_clear_camera("screens")', start_block)
        self.assertIn('_hue_separation_apply_camera("master")', start_block)
        self.assertIn('if scope == "fullscreen":', start_block)
        self.assertIn('_hue_separation_apply_camera("screens")', start_block)
        self.assertIn(
            'renpy.show_screen("hue_separation_glitch_controller")',
            start_block,
        )

    def test_stop_clears_all_runtime_state(self):
        stop_block = function_block(self.source, "hue_separation_stop")

        self.assertIn(
            'renpy.hide_screen("hue_separation_glitch_controller")',
            stop_block,
        )
        self.assertIn('_hue_separation_clear_camera("master")', stop_block)
        self.assertIn('_hue_separation_clear_camera("screens")', stop_block)
        self.assertIn("hue_separation_active = False", stop_block)
        self.assertIn("hue_separation_pixels = 0.0", stop_block)

    def test_glitch_controller_uses_one_shared_peak_state(self):
        self.assertIn(
            "screen hue_separation_glitch_controller():",
            self.source,
        )
        self.assertIn("timer hue_separation_next_delay", self.source)
        self.assertIn("timer hue_separation_peak_duration", self.source)
        self.assertIn(
            "Function(_hue_separation_begin_peak)",
            self.source,
        )
        self.assertIn(
            "Function(_hue_separation_end_peak)",
            self.source,
        )


class FilterPreferenceContractTests(unittest.TestCase):
    def setUp(self):
        self.crt_source = CRT_EFFECT_PATH.read_text(encoding="utf-8")
        self.hue_source = HUE_SEPARATION_EFFECT_PATH.read_text(encoding="utf-8")
        self.screens_source = BASE_SCREENS_PATH.read_text(encoding="utf-8")
        self.sequence_source = OPENING_SEQUENCE_PATH.read_text(encoding="utf-8")

    def test_filter_preferences_default_to_enabled(self):
        self.assertIn(
            "default persistent.crt_effect_enabled = True",
            self.crt_source,
        )
        self.assertIn(
            "default persistent.hue_separation_enabled = True",
            self.hue_source,
        )

    def test_crt_screen_keeps_request_but_gates_visual_layers(self):
        self.assertIn("def set_crt_effect_enabled(enabled):", self.crt_source)
        screen_block, _ = block_with_header(
            self.crt_source,
            'screen crt_effect(mode="subtle"):',
        )
        self.assertIn("if persistent.crt_effect_enabled:", screen_block)
        self.assertIn(
            "$ settings = crt_mode_settings.get(",
            screen_block,
        )

    def test_hue_preference_setter_clears_and_restores_active_request(self):
        setter = function_block(
            self.hue_source,
            "set_hue_separation_enabled",
        )

        self.assertIn("persistent.hue_separation_enabled = bool(enabled)", setter)
        self.assertIn('renpy.hide_screen("hue_separation_glitch_controller")', setter)
        self.assertIn('_hue_separation_clear_camera("master")', setter)
        self.assertIn('_hue_separation_clear_camera("screens")', setter)
        self.assertIn("if persistent.hue_separation_enabled", setter)
        self.assertIn("and hue_separation_active", setter)
        self.assertIn("_hue_separation_refresh_cameras()", setter)
        self.assertIn("_hue_separation_schedule_next()", setter)
        self.assertIn(
            'renpy.show_screen("hue_separation_glitch_controller")',
            setter,
        )

    def test_hue_start_records_request_without_rendering_when_disabled(self):
        start = function_block(self.hue_source, "hue_separation_start")

        self.assertIn("if persistent.hue_separation_enabled:", start)
        active_position = start.index("hue_separation_active = True")
        preference_position = start.index(
            "if persistent.hue_separation_enabled:"
        )
        apply_position = start.index(
            '_hue_separation_apply_camera("master")'
        )
        self.assertLess(active_position, preference_position)
        self.assertLess(preference_position, apply_position)
        self.assertIn(
            'renpy.show_screen("hue_separation_glitch_controller")',
            start[preference_position:],
        )

    def test_preferences_display_has_selected_filter_toggles(self):
        preferences, _ = block_with_header(
            self.screens_source,
            "screen preferences():",
        )

        for label_text, helper, state in (
            (
                "CRT 滤镜",
                "set_crt_effect_enabled",
                "persistent.crt_effect_enabled",
            ),
            (
                "色相差滤镜",
                "set_hue_separation_enabled",
                "persistent.hue_separation_enabled",
            ),
        ):
            with self.subTest(label_text=label_text):
                self.assertIn(f'textbutton _("{label_text}"):', preferences)
                self.assertRegex(
                    preferences,
                    rf"(?s)action Function\(\s*{helper},\s*"
                    rf"not {re.escape(state)},?\s*\)",
                )
                self.assertIn(f"selected {state}", preferences)

    def test_medical_system_starts_and_stops_fullscreen_glitch_hue(self):
        scene_05, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_05:",
        )
        scene_13, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_13:",
        )

        self.assertIn(
            '$ hue_separation_start("glitch", scope="fullscreen")',
            scene_05,
        )
        self.assertIn("$ hue_separation_stop()", scene_13)
        self.assertLess(
            scene_13.index("$ hue_separation_stop()"),
            scene_13.index("hide screen opening_system_desktop"),
        )


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
            "transform opening_scope_scroll(distance=opening_scope_wave_span):",
        )

        for fragment in expected_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, self.source)

    def test_opening_medical_desktop_dims_all_child_colors_to_seventy_percent(self):
        transform_block, _ = block_with_header(
            self.source,
            "transform opening_ui_dimmed:",
        )
        desktop_block, _ = block_with_header(
            self.source,
            "screen opening_system_desktop(body_screen, body_args=None):",
        )

        self.assertIn('matrixcolor TintMatrix("#b3b3b3")', transform_block)
        self.assertIn("at opening_ui_dimmed", desktop_block)

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
        self.assertIn(padding, {(5, 5), (5, 5, 5, 5)})
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
            r'(?m)^\s*add Solid\([^)\n]+\)\s+xpos 0 ypos 0 xsize config\.screen_width ysize 3\s*$',
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
        self.assertEqual((59,), parse_style_tuple(taskbar_style_block, "ysize"))
        self.assertEqual((19, 8, 19, 8), parse_style_tuple(taskbar_content_style_block, "padding"))
        time_size = parse_style_tuple(time_style_block, "size")[0]
        status_size = parse_style_tuple(status_style_block, "size")[0]
        self.assertLessEqual(time_size + status_size, 43)

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

        self.assertEqual(635, wave_span)
        self.assertIn("linear 4.8 xoffset -distance", transform_block)
        self.assertIn("xsize opening_scope_wave_span * 2", scope_block)
        self.assertIn("at opening_scope_scroll", scope_block)
        self.assertEqual(
            2,
            scope_block.count("use opening_scope_wave_segment("),
        )
        self.assertIn(
            "use opening_scope_wave_segment(0)",
            scope_block,
        )
        self.assertIn(
            "use opening_scope_wave_segment(opening_scope_wave_span)",
            scope_block,
        )

    def test_scope_wave_is_code_native_solid_trace_without_glyphs(self):
        segment_block, _ = block_with_header(
            self.source,
            "screen opening_scope_wave_segment(segment_x):",
        )

        self.assertGreaterEqual(
            segment_block.count("add Solid(opening_color_phosphor"),
            6,
        )
        self.assertIn("for beat_x in range(", segment_block)
        self.assertRegex(segment_block, r"\bxsize\s+\d+\s+ysize\s+3\b")
        self.assertRegex(segment_block, r"\bxsize\s+3\s+ysize\s+\d+\b")
        self.assertNotIn("opening_shell_scope_wave_text", self.source)
        self.assertNotRegex(self.source, r"[▁▂▃▄▅▆▇]")

    def test_scope_geometry_uses_consistent_600_pixel_budget(self):
        scope_block, _ = block_with_header(
            self.source,
            "screen opening_oscilloscope():",
        )

        self.assertIn("xsize 600", scope_block)
        self.assertIn("xpos 24", scope_block)
        self.assertIn("xsize 600 ysize 1", scope_block)
        self.assertIn("xpos 24", scope_block)
        self.assertIn("xsize opening_scope_wave_span * 2", scope_block)
        self.assertNotIn("xsize 603", scope_block)

    def test_opening_shell_does_not_depend_on_legacy_medical_wave_scroll(self):
        self.assertNotIn("medical_wave_scroll", self.source)

    def test_document_redactions_use_huiwen_with_source_han_fallback(self):
        self.assertIn("define opening_document_font = rememorial_ui_font", self.source)
        self.assertNotIn("DejaVuSans.ttf", self.source)
        self.assertNotIn("ReMemorialLayeredMing.ttf", self.source)

        for style_name in (
            "opening_records_meta_text",
            "opening_consent_preview_text",
            "opening_consent_document_text",
            "opening_identity_field_text",
        ):
            with self.subTest(style_name=style_name):
                style_block, _ = block_with_header(
                    self.source,
                    f"style {style_name} is gui_text:",
                )
                self.assertIn("font opening_document_font", style_block)


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
            "opening_scene_12",
            "opening_scene_13",
            "opening_scene_14",
        ):
            with self.subTest(label_name=label_name):
                self.assertIn(f"label {label_name}:", self.sequence_source)

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

    def test_opening_scene_00_calls_current_disclaimer_without_crt(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_00:")
        self.assertIn("call screen opening_disclaimer_one", block)
        self.assertIn("jump opening_scene_02", block)
        self.assertNotIn("crt_effect", block)

    def test_opening_scene_01_is_a_compatibility_alias(self):
        scene_block, _ = block_with_header(self.sequence_source, "label opening_scene_01:")

        self.assertEqual(["jump opening_scene_00"], direct_child_lines(scene_block))

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

    def test_tap_to_start_blinks_at_half_speed(self):
        transform_block, _ = block_with_header(
            self.system_source,
            "transform opening_prompt_blink:",
        )

        self.assertEqual(2, transform_block.count("linear 0.56"))
        self.assertNotIn("linear 0.28", transform_block)

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

    def test_complete_sequence_sets_active_and_jumps_to_scene_zero(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label story_0_1_0:",
        )

        self.assertEqual(
            ["$ opening_active = True", "jump opening_scene_00"],
            direct_child_lines(block),
        )

        compatibility_block, _ = block_with_header(
            self.sequence_source,
            "label complete_opening_sequence:",
        )
        self.assertEqual(
            ["jump story_0_1_0"],
            direct_child_lines(compatibility_block),
        )

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
            for path in sorted(GAME_DIR.rglob("*.rpy"))
        )
        declarations = re.findall(
            r"(?m)^\s*default\s+opening_active\s*=\s*(True|False)\s*$",
            all_rpy,
        )
        self.assertEqual(["False"], declarations)

    def test_complete_opening_sequence_does_not_call_return_or_clear_active(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label story_0_1_0:",
        )
        self.assertRegex(block, r"(?m)^\s*\$\s*opening_active\s*=\s*True\s*$")
        self.assertNotIn("opening_active = False", block)
        self.assertNotRegex(block, r"(?m)^\s*(call|return)\b")

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

        # The approved notebook uses one shared desktop/touch tab row.
        self.assertEqual(1, len(quick_menu_blocks))

        for block in quick_menu_blocks:
            with self.subTest(header=block.splitlines()[0]):
                self.assertRegex(
                    block,
                    r"if\s+quick_menu\s+and\s+not\s+opening_active\s+and\s+rm_hud_visible\(\)",
                )

    def test_legacy_inventory_and_phone_overlay_buttons_are_removed(self):
        self.assertNotIn("screen inventory_button():", self.inventory_source)
        self.assertNotIn("screen phone_button():", self.phone_source)


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

    def test_consent_bottom_helper_requires_measured_range_and_uses_four_pixel_tolerance(self):
        block = function_block(self.system_source, "opening_consent_at_bottom")

        self.assertIn('getattr(adjustment, "_opening_range_measured", False)', block)
        self.assertIn("adjustment.range <= 0", block)
        self.assertIn("adjustment.value >= adjustment.range - 4", block)
        self.assertRegex(block, r"(?s)return\s+\(.*\band\b")

    def test_consent_screen_binds_local_adjustment_and_gates_return_on_live_position(self):
        block, _ = block_with_header(
            self.system_source,
            "screen opening_consent_document():",
        )
        self.assertIn('style_prefix "opening_consent"', block)
        self.assertIn(
            "default consent_adjustment = ui.adjustment("
            "raw_changed=opening_consent_adjustment_changed, "
            "ranged=opening_consent_adjustment_ranged)",
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

    def test_consent_range_callback_unlocks_only_after_viewport_measurement(self):
        block = function_block(
            self.system_source,
            "opening_consent_adjustment_ranged",
        )
        self.assertIn('getattr(adjustment, "_opening_range_measured", False)', block)
        self.assertIn("adjustment._opening_range_measured = True", block)
        self.assertIn("renpy.restart_interaction()", block)

    def test_consent_vertical_scrollbar_uses_muted_medical_palette(self):
        style_block, _ = block_with_header(
            self.system_source,
            "style opening_consent_vscrollbar is vscrollbar:",
        )

        width = parse_style_tuple(style_block, "xsize")[0]
        self.assertGreaterEqual(width, 24)
        self.assertLessEqual(width, 27)
        self.assertIn('base_bar Solid("#4d5a52")', style_block)
        self.assertIn('thumb Solid("#617e6d")', style_block)
        self.assertNotRegex(style_block.lower(), r"(cyan|#00ffff|#00b8ff)")

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

    def test_scene_flow_runs_sequentially_from_six_through_fourteen(self):
        expected_jumps = {
            "opening_scene_06": "opening_scene_07",
            "opening_scene_07": "opening_scene_08",
            "opening_scene_08": "opening_scene_09",
            "opening_scene_09": "opening_scene_10",
            "opening_scene_10": "opening_scene_11",
            "opening_scene_11": "opening_scene_12",
            "opening_scene_12": "opening_scene_13",
            "opening_scene_13": "opening_scene_14",
        }
        for scene, destination in expected_jumps.items():
            with self.subTest(scene=scene):
                block, _ = block_with_header(self.sequence_source, f"label {scene}:")
                self.assertIn(f"jump {destination}", block)
        scene_14, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_14:",
        )
        self.assertIn("jump story_1_1_1", scene_14)

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
        self.assertEqual(
            4,
            len(re.findall(r"(?m)^\s*pause\s*$", block)),
        )
        self.assertNotRegex(block, r"(?m)^\s*pause\s+\d")
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
        self.assertEqual(
            3,
            len(re.findall(r"(?m)^\s*pause\s*$", block)),
        )
        self.assertNotRegex(block, r"(?m)^\s*pause\s+\d")

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

    def test_scene_11_dialogue_calls_consent_then_jumps_without_cleanup(self):
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
        self.assertIn("jump opening_scene_12", block)
        for cleanup in (
            "hide screen opening_memory_overlay",
            "hide screen crt_effect",
            "hide screen opening_system_desktop",
            "opening_active = False",
            "return",
        ):
            with self.subTest(cleanup=cleanup):
                self.assertNotIn(cleanup, block)

    def test_scene_12_presents_exact_dialogue_and_inserts_in_order(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_12:")
        ordered_lines = (
            'show screen opening_system_desktop("opening_identity_preview_body")',
            'system "请核对个人信息。"',
            'fro "姓名——"',
            "call screen opening_name_insert",
            'show screen opening_system_desktop("opening_identity_preview_body")',
            'fro "日期——"',
            "call screen opening_date_insert",
            'show screen opening_system_desktop("opening_identity_preview_body")',
            'fro "上面的初始属性——这是什么？"',
            'system "关于你在这场手术中物质的使用，一经确认无法更改，请保证你充分利用它们的价值。"',
            'system "个人信息确认无误后，请长按‘确认’按钮完成签名。"',
            "call screen opening_identity_document",
        )
        positions = []
        cursor = 0
        for line in ordered_lines:
            position = block.index(line, cursor)
            positions.append(position)
            cursor = position + len(line)
        self.assertEqual(sorted(positions), positions)
        self.assertNotIn("show screen opening_name_insert", block)
        self.assertNotIn("show screen opening_date_insert", block)
        self.assertNotIn("pause 0.8", block)

    def test_scene_12_identity_inserts_allow_mouse_keyboard_and_timeout_progression(self):
        scene_block, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_12:",
        )
        self.assertIn("call screen opening_name_insert", scene_block)
        self.assertIn("call screen opening_date_insert", scene_block)

        for screen_header in (
            "screen opening_name_insert():",
            "screen opening_date_insert():",
        ):
            with self.subTest(screen_header=screen_header):
                screen_block, _ = block_with_header(
                    self.system_source,
                    screen_header,
                )
                self.assertIn("timer 0.8 action Return()", screen_block)
                self.assertIn('key "dismiss" action Return()', screen_block)
                self.assertIn('style "opening_clear_fullscreen_button"', screen_block)
                self.assertIn("action Return()", screen_block)

    def test_scene_12_jumps_to_verification_without_cleanup_or_return(self):
        block, _ = block_with_header(self.sequence_source, "label opening_scene_12:")
        signature_position = block.index("call screen opening_identity_document")
        cleanup_lines = (
            "hide screen opening_memory_overlay",
            "hide screen opening_flash_once",
            "hide screen crt_effect",
            "hide screen opening_system_desktop",
            "opening_active = False",
            "return",
        )
        for cleanup in cleanup_lines:
            with self.subTest(cleanup=cleanup):
                self.assertNotIn(cleanup, block)
        self.assertGreater(block.index("jump opening_scene_13"), signature_position)

    def test_identity_screens_use_native_inserts_and_required_personal_fields(self):
        for header in (
            "screen opening_identity_preview_body():",
            "screen opening_identity_body(signature_hovered, signature_progress):",
            "screen opening_identity_document():",
            "screen opening_name_insert():",
            "screen opening_date_insert():",
        ):
            with self.subTest(header=header):
                self.assertIn(header, self.system_source)

        preview_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_preview_body():",
        )
        identity_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )
        combined = preview_block + identity_block
        for text in ("姓名：弗洛", "性别：男", "年龄：24", "ID：████████"):
            with self.subTest(text=text):
                self.assertIn(text, combined)

        name_block, _ = block_with_header(
            self.system_source,
            "screen opening_name_insert():",
        )
        date_block, _ = block_with_header(
            self.system_source,
            "screen opening_date_insert():",
        )
        self.assertIn('add Solid("#000000")', name_block)
        self.assertIn('text "弗洛"', name_block)
        self.assertIn('color "#ffffff"', name_block)
        self.assertIn('add Solid("#000000")', date_block)
        self.assertGreaterEqual(date_block.count("Solid("), 3)
        self.assertNotRegex(date_block, r"(?m)^\s*text\s+")

    def test_stat_rows_lock_constitution_and_use_existing_adjustment_actions(self):
        row_block, _ = block_with_header(
            self.system_source,
            "screen opening_stat_row(label_text, stat_name, value, locked=False):",
        )
        identity_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )

        self.assertIn('text "固定"', row_block)
        self.assertIn("if locked:", row_block)
        self.assertIn("opening_can_adjust_stat(stat_name, -1)", row_block)
        self.assertIn("opening_can_adjust_stat(stat_name, 1)", row_block)
        self.assertIn("Function(opening_adjust_stat, stat_name, -1)", row_block)
        self.assertIn("Function(opening_adjust_stat, stat_name, 1)", row_block)

        required_rows = (
            'use opening_stat_row("体质", "con", rm_opening_attribute_value("con"), locked=True)',
            'use opening_stat_row("力量", "str", rm_opening_attribute_value("str"))',
            'use opening_stat_row("灵巧", "dex", rm_opening_attribute_value("dex"))',
            'use opening_stat_row("智识", "int", rm_opening_attribute_value("int"))',
            'use opening_stat_row("意志", "pow", rm_opening_attribute_value("pow"), locked=True)',
        )
        for row in required_rows:
            with self.subTest(row=row):
                self.assertIn(row, identity_block)
        self.assertNotRegex(identity_block, r"\bstat_(con|str|dex|int|pow)\b")

    def test_identity_ui_binds_existing_remaining_and_completion_rules(self):
        identity_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )
        document_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_document():",
        )
        self.assertIn(
            'text "剩余可分配点数：[opening_stat_points_remaining()]"',
            identity_block,
        )
        self.assertGreaterEqual(
            identity_block.count("opening_stats_complete()")
            + document_block.count("opening_stats_complete()"),
            2,
        )
        self.assertNotRegex(identity_block, r"\b17\s*-")
        self.assertNotRegex(identity_block, r"stat_(str|dex|int|pow)\s*[<>]=?\s*(1|20)")

    def test_signature_state_machine_is_owned_by_outer_document_scope(self):
        body_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )
        document_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_document():",
        )
        for state in (
            "signature_hovered",
            "signature_holding",
            "signature_progress",
            "signature_complete",
            "signature_started_at",
        ):
            with self.subTest(state=state):
                self.assertIn(f"default {state} =", document_block)
                self.assertNotIn(f"default {state} =", body_block)

        self.assertIn('key "mousedown_1"', document_block)
        self.assertIn('key "mouseup_1"', document_block)
        self.assertIn("timer 0.05 repeat True", document_block)
        self.assertRegex(
            document_block,
            r"(?m)^    if signature_holding:\s*\n"
            r"        timer 0\.05 repeat True",
        )
        self.assertNotIn('key "mousedown_1"', body_block)
        self.assertNotIn('key "mouseup_1"', body_block)
        self.assertNotIn("timer 0.05", body_block)
        self.assertIn(
            "use opening_identity_body(signature_hovered, signature_progress)",
            document_block,
        )
        self.assertIn("hovered SetScreenVariable", body_block)
        self.assertIn("unhovered [", body_block)

    def test_signature_hover_area_does_not_consume_mouse_button_events(self):
        body_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )
        signature_match = re.search(
            r'(?m)^\s*frame:\s*\n\s*style "opening_signature_frame"',
            body_block,
        )
        self.assertIsNotNone(signature_match)
        signature_region = body_block[signature_match.start():]
        document_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_document():",
        )

        self.assertRegex(signature_region, r"(?m)^\s*frame:\s*$")
        self.assertIn('style "opening_signature_frame"', signature_region)
        self.assertIn("mousearea:", signature_region)
        self.assertRegex(
            signature_region,
            r"(?s)mousearea:\s+area\s+\(0,\s*0,\s*1\.0,\s*1\.0\)"
            r".*?hovered SetScreenVariable.*?unhovered \[",
        )
        self.assertNotRegex(signature_region, r"(?m)^\s*button:\s*$")
        self.assertNotIn("action NullAction()", signature_region)
        style_block, _ = block_with_header(
            self.system_source,
            "style opening_signature_frame is frame:",
        )
        self.assertIn("padding (0, 0, 0, 0)", style_block)
        self.assertIn('key "mousedown_1"', document_block)
        self.assertIn('key "mouseup_1"', document_block)

    def test_signature_uses_runtime_elapsed_with_gate_and_early_reset(self):
        body_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_body(signature_hovered, signature_progress):",
        )
        document_block, _ = block_with_header(
            self.system_source,
            "screen opening_identity_document():",
        )
        start_helper = function_block(
            self.system_source,
            "opening_start_signature_hold",
        )
        self.assertRegex(
            document_block,
            r"(?s)key\s+\"mousedown_1\".*?signature_hovered.*?"
            r"opening_stats_complete\(\).*?"
            r"Function\(opening_start_signature_hold\)",
        )
        self.assertIn("renpy.current_screen()", start_helper)
        self.assertIn('scope["signature_started_at"] = renpy.get_game_runtime()', start_helper)
        self.assertIn('scope["signature_holding"] = True', start_helper)
        self.assertIn('scope["signature_progress"] = 0.0', start_helper)
        self.assertIn("renpy.restart_interaction()", start_helper)
        self.assertRegex(
            document_block,
            r"(?s)key\s+\"mouseup_1\".*?signature_holding.*?"
            r"signature_progress.*?0\.0.*?signature_started_at.*?None",
        )
        self.assertRegex(
            body_block,
            r"(?s)unhovered\s+\[.*?signature_holding.*?False.*?"
            r"signature_progress.*?0\.0.*?signature_started_at.*?None",
        )
        self.assertRegex(
            document_block,
            r"renpy\.get_game_runtime\(\)\s*-\s*signature_started_at",
        )
        self.assertRegex(
            document_block,
            r"(?s)max\(\s*0\.0\s*,\s*min\(\s*1\.5\s*,\s*"
            r"renpy\.get_game_runtime\(\)\s*-\s*signature_started_at",
        )
        self.assertIn(">= 1.5", document_block)
        self.assertRegex(
            document_block,
            r'(?s)key "mouseup_1".*?'
            r"renpy\.get_game_runtime\(\) - signature_started_at >= 1\.5.*?"
            r'SetScreenVariable\("signature_complete", True\).*?Return\(\)',
        )
        self.assertNotIn("signature_progress + 0.05", self.system_source)
        self.assertIn("StaticValue(signature_progress, 1.5)", body_block)
        self.assertEqual(2, document_block.count("Return()"))

    def test_opening_identity_styles_exist(self):
        for style_name in (
            "opening_identity_preview_frame",
            "opening_identity_document_frame",
            "opening_identity_field_text",
            "opening_stat_row_frame",
            "opening_stat_button",
            "opening_signature_frame",
            "opening_signature_progress_bar",
        ):
            with self.subTest(style_name=style_name):
                self.assertRegex(
                    self.system_source,
                    rf"(?m)^style\s+{re.escape(style_name)}\b",
                )

    def test_signature_frame_has_fixed_compact_height(self):
        style_block, _ = block_with_header(
            self.system_source,
            "style opening_signature_frame is frame:",
        )

        self.assertEqual((131,), parse_style_tuple(style_block, "ysize"))
        self.assertNotRegex(style_block, r"(?m)^\s*yfill\b")
        self.assertNotRegex(style_block, r"(?m)^\s*yminimum\b")

    def test_identity_document_stays_inside_window_with_body_height_budget(self):
        document_style, _ = block_with_header(
            self.system_source,
            "style opening_identity_document_frame is frame:",
        )
        row_style, _ = block_with_header(
            self.system_source,
            "style opening_stat_row_frame is frame:",
        )
        signature_style, _ = block_with_header(
            self.system_source,
            "style opening_signature_frame is frame:",
        )
        section_style, _ = block_with_header(
            self.system_source,
            "style opening_consent_section_text is gui_text:",
        )
        remaining_style, _ = block_with_header(
            self.system_source,
            "style opening_identity_remaining_text is gui_text:",
        )

        xpos = parse_style_tuple(document_style, "xpos")[0]
        ypos = parse_style_tuple(document_style, "ypos")[0]
        xsize = parse_style_tuple(document_style, "xsize")[0]
        ysize = parse_style_tuple(document_style, "ysize")[0]
        padding = parse_style_tuple(document_style, "padding")
        self.assertEqual((204, 2072), (xpos, xsize))
        self.assertEqual((237, 907), (ypos, ysize))
        self.assertLessEqual(ypos + ysize, 1167)

        top_padding = padding[1]
        bottom_padding = padding[3]
        available_body_height = ysize - top_padding - bottom_padding
        right_column_budget = (
            parse_style_tuple(section_style, "size")[0]
            + 5 * parse_style_tuple(row_style, "ysize")[0]
            + parse_style_tuple(remaining_style, "size")[0]
            + parse_style_tuple(signature_style, "ysize")[0]
            + 7 * 12
        )
        self.assertGreaterEqual(available_body_height, right_column_budget)


class OpeningHandoffContractTests(unittest.TestCase):
    def setUp(self):
        self.system_source = OPENING_SYSTEM_PATH.read_text(encoding="utf-8")
        self.sequence_source = OPENING_SEQUENCE_PATH.read_text(encoding="utf-8")
        self.script_source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.dream_source = STORY_DREAM_PATH.read_text(encoding="utf-8")

    def test_start_only_jumps_to_numbered_opening_segment(self):
        block, _ = block_with_header(self.script_source, "label start:")
        self.assertEqual(
            ["jump story_0_1_0"],
            direct_child_lines(block),
        )

    def test_verification_and_countdown_screens_exist(self):
        verification, _ = block_with_header(
            self.system_source,
            "screen opening_verification_body(status_text, progress):",
        )
        countdown, _ = block_with_header(
            self.system_source,
            "screen opening_countdown(number):",
        )

        self.assertIn("text status_text", verification)
        self.assertIn("StaticValue(progress, 100.0)", verification)
        self.assertIn("use opening_oscilloscope", verification)
        self.assertNotIn("opening_system_desktop", verification)
        self.assertIn('add Solid("#000000")', countdown)
        self.assertIn('text "[number]"', countdown)
        self.assertNotRegex(countdown, r"(?m)^\s*text\s+number\s*:")
        self.assertRegex(countdown, r"(?m)^\s*size\s+(?:[7-9]\d|1\d\d)\s*$")
        self.assertRegex(countdown, r'(?m)^\s*color\s+"#(?:fff|ffffff)"\s*$')

    def test_scene_13_runs_exact_verification_progress_and_crt_transition(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_13:",
        )
        ordered = (
            'show screen crt_effect(mode="interference")',
            '"核验通过。", 35',
            '"医疗单元已就位。", 72',
            '"意识将在 3 秒内重启。", 100',
            "hide screen crt_effect",
            'show screen crt_effect(mode="shutdown")',
            "hide screen opening_system_desktop",
            "hide screen crt_effect",
            "scene black",
            "jump opening_scene_14",
        )
        cursor = 0
        for fragment in ordered:
            with self.subTest(fragment=fragment):
                position = block.index(fragment, cursor)
                cursor = position + len(fragment)

        self.assertEqual(
            3,
            block.count(
                'show screen opening_system_desktop("opening_verification_body"'
            ),
        )
        self.assertRegex(block, r"pause\s+0\.45\b")
        self.assertNotIn("opening_active = False", block)
        self.assertNotIn("hide screen opening_verification_body", block)
        self.assertNotRegex(block, r"(?m)^\s*return\s*$")
        for screen_name in (
            "opening_memory_overlay",
            "opening_flash_once",
            "opening_countdown",
        ):
            with self.subTest(screen_name=screen_name):
                self.assertIn(f"hide screen {screen_name}", block)

    def test_scene_14_is_black_numeric_countdown_then_hard_silent_handoff(self):
        block, _ = block_with_header(
            self.sequence_source,
            "label opening_scene_14:",
        )
        ordered = (
            "scene black",
            "show screen opening_countdown(3)",
            "hide screen opening_countdown",
            "show screen opening_countdown(2)",
            "hide screen opening_countdown",
            "show screen opening_countdown(1)",
            "hide screen opening_countdown",
            "scene black",
            "renpy.pause(2.5, hard=True, modal=False)",
            "opening_active = False",
            "jump story_1_1_1",
        )
        cursor = 0
        for fragment in ordered:
            with self.subTest(fragment=fragment):
                position = block.index(fragment, cursor)
                cursor = position + len(fragment)

        for number in (3, 2, 1):
            with self.subTest(number=number):
                self.assertEqual(
                    1,
                    block.count(f"show screen opening_countdown({number})"),
                )
        self.assertEqual(3, len(re.findall(r"(?m)^\s*pause\s+0\.8\s*$", block)))
        scene_lines = re.findall(r"(?m)^\s*scene\s+.*$", block)
        self.assertGreaterEqual(len(scene_lines), 2)
        self.assertTrue(
            all(line.strip() == "scene black" for line in scene_lines),
            scene_lines,
        )
        self.assertNotRegex(block, r"(?m)^\s*(show|image)\s+(?!screen opening_countdown)")
        self.assertNotIn("opening_play_sound", block)
        self.assertIn('renpy.music.stop(channel="sound")', block)
        self.assertIn('renpy.music.stop(channel="opening_foley")', block)
        self.assertNotIn("renpy.restart_interaction()", block)
        self.assertNotIn("hide screen opening_verification_body", block)
        self.assertNotRegex(block, r"(?m)^\s*(play|queue|voice)\b")
        self.assertNotRegex(block, r"(?m)^\s*return\s*$")
        for screen_name in (
            "opening_disclaimer_one",
            "opening_disclaimer_two",
            "opening_tap_to_start",
            "opening_water_wait",
            "opening_water_drop",
            "opening_countdown",
            "opening_memory_overlay",
            "opening_flash_once",
            "opening_consent_document",
            "opening_name_insert",
            "opening_date_insert",
            "opening_identity_document",
            "opening_system_desktop",
            "crt_effect",
        ):
            with self.subTest(screen_name=screen_name):
                self.assertIn(f"hide screen {screen_name}", block)

    def test_mountain_compatibility_label_and_story_entry_are_wired(self):
        labels = re.findall(
            r"(?m)^\s*label\s+mountain_memory_start\s*:\s*$",
            self.dream_source,
        )
        self.assertEqual(1, len(labels))
        compatibility_block, _ = block_with_header(
            self.dream_source,
            "label mountain_memory_start:",
        )
        self.assertEqual(
            ["jump story_1_1_1"],
            direct_child_lines(compatibility_block),
        )

        story_block, _ = block_with_header(
            self.dream_source,
            "label story_1_1_1:",
        )
        self.assertIn("scene black", story_block)
        self.assertIn('mystery "3——2——1——呼——"', story_block)

    def test_legacy_medical_screen_file_and_all_rpy_references_are_gone(self):
        self.assertFalse(MEDICAL_SCREENS_PATH.exists())
        self.assertFalse(MEDICAL_SCREENS_COMPILED_PATH.exists())
        all_rpy = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(GAME_DIR.rglob("*.rpy"))
        )
        self.assertNotIn("medical_system_panel", all_rpy)
        self.assertNotIn("medical_confirm", all_rpy)


if __name__ == "__main__":
    unittest.main()
