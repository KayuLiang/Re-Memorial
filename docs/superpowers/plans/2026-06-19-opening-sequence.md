# Complete Opening Sequence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete Scene 00–14 opening, reusable three-level CRT effects, interactive consent/stat-signing screens, and a clean transition into the existing mountain-memory story.

**Architecture:** Keep narrative orchestration, screen UI, stat rules, and CRT effects in separate focused files. Put deterministic stat-allocation logic in a small pure-Python module so it can be unit tested outside Ren’Py; use Ren’Py-native labels, screens, adjustments, timers, ATL, and actions for presentation and interaction.

**Tech Stack:** Ren’Py 8.5.3, Python 3, Ren’Py Screen Language, ATL, `unittest`, existing PNG CRT assets.

---

## File Map

- Create `game/opening_stats_logic.py`: pure stat-allocation validation and future dice/check fallback contracts.
- Create `game/opening_stats.rpy`: Ren’Py store variables and wrappers around the pure stat functions.
- Create `game/screens_opening_system.rpy`: disclaimers, start prompt, water-drop scene, system desktop, document viewport, stat allocation, signature, countdown.
- Create `game/opening_sequence.rpy`: Scene 00–14 labels and transitions.
- Create `tools/test_opening_stats.py`: executable unit tests for stat rules.
- Create `tools/test_opening_contracts.py`: static regression checks for labels, screens, CRT modes, text, and cleanup.
- Modify `game/crt_effect.rpy`: add `subtle`, `interference`, and `shutdown` presets.
- Modify `game/script.rpy`: remove obsolete opening and duplicate stat defaults; call the new opening and preserve the mountain-memory continuation.
- Retire `game/screens_medical.rpy`: remove obsolete screens after the replacement opening is wired.
- Optionally create `game/images/opening/`: only for small generated water/texture/icon assets that cannot be expressed cleanly with native displayables.
- Create `game/audio/opening/README.md`: stable target filenames and silent-fallback behavior for missing sound assets.

## Commands Used Throughout

Run pure Python tests:

```powershell
& 'C:\Users\19512\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tools -p 'test_opening_*.py' -v
```

Run Ren’Py lint without console encoding corruption:

```powershell
$env:PYTHONIOENCODING='utf-8'
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' lint
```

All implementation happens in `E:\RenpyProject\ReMemorial`. Before each commit, sync only source/assets/docs/tools into `E:\Re-Memorial`, excluding cache, saves, compiled files, logs, errors, and tracebacks. Commit only from `E:\Re-Memorial`.

### Task 1: Add deterministic stat-allocation logic

**Files:**
- Create: `game/opening_stats_logic.py`
- Create: `tools/test_opening_stats.py`

- [ ] **Step 1: Write failing unit tests**

Create `tools/test_opening_stats.py`:

```python
import sys
import unittest
from pathlib import Path

GAME_DIR = Path(__file__).resolve().parents[1] / "game"
sys.path.insert(0, str(GAME_DIR))

from opening_stats_logic import (
    ADJUSTABLE_STATS,
    STAT_MAX,
    STAT_MIN,
    TOTAL_ALLOCATABLE_POINTS,
    adjust_stat,
    attribute_check_unavailable,
    remaining_points,
    stats_complete,
)


class OpeningStatsTests(unittest.TestCase):
    def setUp(self):
        self.base = {"str": 1, "dex": 1, "int": 1, "pow": 1}

    def test_initial_pool_is_seventeen(self):
        self.assertEqual(17, remaining_points(self.base))

    def test_adjustment_spends_and_refunds_points(self):
        raised = adjust_stat(self.base, "str", 1)
        self.assertEqual(2, raised["str"])
        self.assertEqual(16, remaining_points(raised))
        lowered = adjust_stat(raised, "str", -1)
        self.assertEqual(self.base, lowered)

    def test_cannot_drop_below_one(self):
        self.assertEqual(self.base, adjust_stat(self.base, "str", -1))

    def test_cannot_exceed_twenty(self):
        values = dict(self.base, str=20)
        self.assertEqual(values, adjust_stat(values, "str", 1))

    def test_cannot_spend_more_than_pool(self):
        values = {"str": 18, "dex": 1, "int": 1, "pow": 1}
        self.assertEqual(values, adjust_stat(values, "dex", 1))

    def test_unknown_and_constitution_are_rejected(self):
        self.assertEqual(self.base, adjust_stat(self.base, "con", 1))
        self.assertEqual(self.base, adjust_stat(self.base, "luck", 1))

    def test_complete_requires_exactly_seventeen_spent(self):
        self.assertFalse(stats_complete(self.base))
        self.assertTrue(stats_complete({"str": 18, "dex": 1, "int": 1, "pow": 1}))

    def test_constants_match_design(self):
        self.assertEqual(("str", "dex", "int", "pow"), ADJUSTABLE_STATS)
        self.assertEqual(1, STAT_MIN)
        self.assertEqual(20, STAT_MAX)
        self.assertEqual(17, TOTAL_ALLOCATABLE_POINTS)

    def test_unavailable_check_is_structured_and_non_random(self):
        result = attribute_check_unavailable("int")
        self.assertEqual(
            {
                "available": False,
                "stat": "int",
                "reason": "attribute_dice_not_configured",
                "rolls": (),
            },
            result,
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Run the pure Python test command.

Expected: `ModuleNotFoundError: No module named 'opening_stats_logic'`.

- [ ] **Step 3: Implement the pure stat module**

Create `game/opening_stats_logic.py`:

```python
ADJUSTABLE_STATS = ("str", "dex", "int", "pow")
STAT_MIN = 1
STAT_MAX = 20
TOTAL_ALLOCATABLE_POINTS = 17


def _normalized(values):
    return {name: int(values.get(name, STAT_MIN)) for name in ADJUSTABLE_STATS}


def points_spent(values):
    current = _normalized(values)
    return sum(current[name] - STAT_MIN for name in ADJUSTABLE_STATS)


def remaining_points(values):
    return TOTAL_ALLOCATABLE_POINTS - points_spent(values)


def can_adjust_stat(values, stat_name, delta):
    if stat_name not in ADJUSTABLE_STATS or delta not in (-1, 1):
        return False
    current = _normalized(values)
    next_value = current[stat_name] + delta
    if next_value < STAT_MIN or next_value > STAT_MAX:
        return False
    if delta > 0 and remaining_points(current) <= 0:
        return False
    return True


def adjust_stat(values, stat_name, delta):
    current = _normalized(values)
    if not can_adjust_stat(current, stat_name, delta):
        return current
    current[stat_name] += delta
    return current


def stats_complete(values):
    return remaining_points(values) == 0


def get_attribute_dice(_stat_name):
    return ()


def attribute_check_unavailable(stat_name):
    return {
        "available": False,
        "stat": stat_name,
        "reason": "attribute_dice_not_configured",
        "rolls": (),
    }
```

- [ ] **Step 4: Run tests and verify pass**

Expected: 9 tests pass.

- [ ] **Step 5: Sync and commit**

Sync `game/opening_stats_logic.py` and `tools/test_opening_stats.py` to `E:\Re-Memorial`.

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_stats_logic.py tools/test_opening_stats.py
git -C 'E:\Re-Memorial' commit -m "feat: add opening stat allocation rules"
```

### Task 2: Add Ren’Py stat store integration

**Files:**
- Create: `game/opening_stats.rpy`
- Modify: `game/script.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Write a failing static contract test**

Create `tools/test_opening_contracts.py`:

```python
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "game"


def read(name):
    return (GAME / name).read_text(encoding="utf-8-sig")


class OpeningContracts(unittest.TestCase):
    def test_stats_have_one_canonical_definition(self):
        all_rpy = "\n".join(path.read_text(encoding="utf-8-sig") for path in GAME.glob("*.rpy"))
        self.assertEqual(1, all_rpy.count("default stat_con = 3"))
        self.assertEqual(1, all_rpy.count("default stat_str = 1"))
        self.assertNotIn("default stat_con = 30", all_rpy)

    def test_stat_wrappers_exist(self):
        source = read("opening_stats.rpy")
        for name in (
            "opening_stat_points_remaining",
            "opening_can_adjust_stat",
            "opening_adjust_stat",
            "opening_stats_complete",
            "get_base_stat",
            "get_effective_stat",
            "get_attribute_dice",
            "perform_attribute_check",
        ):
            self.assertIn("def " + name, source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests and verify failure**

Expected: failure because `opening_stats.rpy` does not exist and old `30` defaults remain.

- [ ] **Step 3: Add store defaults and wrappers**

Create `game/opening_stats.rpy`:

```renpy
default stat_con = 3
default stat_str = 1
default stat_dex = 1
default stat_int = 1
default stat_pow = 1

init python:
    from opening_stats_logic import (
        adjust_stat,
        can_adjust_stat,
        get_attribute_dice as _get_attribute_dice,
        remaining_points,
        stats_complete,
        attribute_check_unavailable,
    )

    def _opening_stat_values():
        return {
            "str": store.stat_str,
            "dex": store.stat_dex,
            "int": store.stat_int,
            "pow": store.stat_pow,
        }

    def opening_stat_points_remaining():
        return remaining_points(_opening_stat_values())

    def opening_can_adjust_stat(stat_name, delta):
        return can_adjust_stat(_opening_stat_values(), stat_name, delta)

    def opening_adjust_stat(stat_name, delta):
        values = adjust_stat(_opening_stat_values(), stat_name, delta)
        store.stat_str = values["str"]
        store.stat_dex = values["dex"]
        store.stat_int = values["int"]
        store.stat_pow = values["pow"]

    def opening_stats_complete():
        return stats_complete(_opening_stat_values())

    def get_base_stat(stat_name):
        return getattr(store, "stat_" + stat_name)

    def get_effective_stat(stat_name):
        return get_base_stat(stat_name)

    def get_attribute_dice(stat_name):
        return _get_attribute_dice(stat_name)

    def perform_attribute_check(stat_name, energy=1):
        dice = get_attribute_dice(stat_name)
        if not dice:
            return attribute_check_unavailable(stat_name)
        return {
            "available": True,
            "stat": stat_name,
            "energy": energy,
            "rolls": tuple(),
        }
```

Remove the five old `default stat_* = 30` lines from `game/script.rpy`.

- [ ] **Step 4: Run unit and contract tests**

Expected: all tests pass.

- [ ] **Step 5: Run Ren’Py lint**

Expected: no new error in `opening_stats.rpy`.

- [ ] **Step 6: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_stats.rpy game/script.rpy tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: connect opening stats to Ren'Py store"
```

### Task 3: Extend the CRT effect into three presets

**Files:**
- Modify: `game/crt_effect.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing CRT contract tests**

Add:

```python
    def test_crt_has_three_modes(self):
        source = read("crt_effect.rpy")
        self.assertIn('screen crt_effect(mode="subtle")', source)
        for mode in ("subtle", "interference", "shutdown"):
            self.assertIn('"' + mode + '"', source)
        self.assertIn("crt_mode_settings", source)
        self.assertIn("crt_horizontal_jitter", source)
```

- [ ] **Step 2: Run contract tests and verify failure**

Expected: current CRT screen has no mode argument or settings map.

- [ ] **Step 3: Replace global strengths with mode settings**

Modify `game/crt_effect.rpy` to retain existing images and add:

```renpy
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
}

transform crt_horizontal_jitter(amount=0):
    xoffset 0
    choice:
        pause 0.08
        linear 0.02 xoffset amount
        linear 0.03 xoffset -amount
        linear 0.02 xoffset 0
    choice:
        pause 0.18
    repeat

screen crt_effect(mode="subtle"):
    modal False
    zorder 1000

    $ settings = crt_mode_settings.get(mode, crt_mode_settings["subtle"])

    fixed:
        xsize config.screen_width
        ysize config.screen_height
        clipping True
        at crt_horizontal_jitter(settings["jitter"])

        add "images/effects/crt_scanlines.png":
            alpha settings["scanline"]
            at crt_scanline_scroll(crt_scroll_speed)

        add "crt_noise_cycle":
            xsize config.screen_width
            ysize config.screen_height
            alpha settings["noise"]

        add Solid("#ffffff"):
            at crt_flicker(settings["flicker"])
```

- [ ] **Step 4: Run contract tests and lint**

Expected: contract passes; lint reports no new CRT error.

- [ ] **Step 5: Manually preview each mode**

Temporarily call each mode from the Ren’Py developer console or a temporary test label:

```renpy
show screen crt_effect(mode="subtle")
show screen crt_effect(mode="interference")
show screen crt_effect(mode="shutdown")
```

Verify:

- `subtle` keeps small text readable;
- `interference` is visibly stronger;
- `shutdown` is brief and strong enough for Scene 13.

Remove any temporary test label.

- [ ] **Step 6: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/crt_effect.rpy tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: add CRT intensity presets"
```

### Task 4: Build the reusable Win7 medical-system visual shell

**Files:**
- Create: `game/screens_opening_system.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing visual-shell contracts**

Add:

```python
    def test_opening_system_visual_tokens_exist(self):
        source = read("screens_opening_system.rpy")
        for token in (
            'define opening_color_desktop = "#6f8078"',
            'define opening_color_border = "#5b8db8"',
            'define opening_color_paper = "#e7e4d9"',
            'define opening_color_phosphor = "#a8c7aa"',
            "screen opening_system_desktop",
            "screen opening_window_frame",
            "screen opening_oscilloscope",
        ):
            self.assertIn(token, source)
```

- [ ] **Step 2: Run contract tests and verify failure**

Expected: `screens_opening_system.rpy` does not exist.

- [ ] **Step 3: Implement visual constants and reusable components**

Start `game/screens_opening_system.rpy` with:

```renpy
define opening_color_desktop = "#6f8078"
define opening_color_desktop_dark = "#46534f"
define opening_color_border = "#5b8db8"
define opening_color_border_dark = "#315f88"
define opening_color_paper = "#e7e4d9"
define opening_color_phosphor = "#a8c7aa"

screen opening_window_frame(title, body_screen, body_args={}):
    frame:
        style "opening_window_outer"
        vbox:
            spacing 0
            frame:
                style "opening_titlebar"
                hbox:
                    xfill True
                    text title style "opening_titlebar_text"
                    text "—  □  ×" style "opening_window_controls"
            frame:
                style "opening_menu_bar"
                text "文件(F)    患者(P)    治疗记录(T)    帮助(H)" style "opening_menu_text"
            use expression body_screen pass (body_args)

screen opening_system_desktop(body_screen, body_args={}):
    add Solid(opening_color_desktop_dark)
    frame:
        style "opening_ghost_window"
        xpos 1290
        ypos 60
        text "INTERVIEW_RECORD_04\n患者陈述：████████\n时间标记：--/--/--\n归档状态：不完整"
    use opening_window_frame(
        "市立精神卫生中心 - 特殊治疗管理系统",
        body_screen,
        body_args,
    )
    frame:
        style "opening_taskbar"
        text "⊕    特殊治疗管理系统                                      13:30"

screen opening_oscilloscope():
    frame:
        style "opening_scope_frame"
        vbox:
            text "OSC / CH-01                     SYNC" style "opening_scope_small"
            frame:
                style "opening_scope_grid"
                text "____╱╲________╱╲___╱╲______" at medical_wave_scroll style "opening_scope_trace"
            text "HR  072       SpO2  98%       GAIN 1.0" style "opening_scope_small"
```

Define explicit styles with 4-pixel equal borders, clipped content, darkened surroundings, a 2-pixel taskbar highlight, and no gradient backgrounds. Use nested frames/Solids so all four window edges are visually identical.

- [ ] **Step 4: Add a visual test body**

Add a temporary `screen opening_shell_preview_body()` containing paper and oscilloscope columns, and a temporary `label opening_shell_preview` that calls the desktop. Use it only for visual QA.

- [ ] **Step 5: Run contracts and lint**

Expected: contracts pass; lint has no new screen/style errors.

- [ ] **Step 6: Launch the preview and compare at 1920×1080**

Verify:

- all four blue borders are equal;
- internal content remains inside the border;
- desktop and ghost window are darker than the main window;
- taskbar has one 2-pixel pale-blue top line;
- paper and oscilloscope match the approved palette.

Remove the temporary preview label after validation.

- [ ] **Step 7: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/screens_opening_system.rpy tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: build Win7 medical system shell"
```

### Task 5: Implement pre-system scenes and memory overlays

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Create: `game/opening_sequence.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing scene contracts**

Add:

```python
    def test_all_opening_scene_labels_exist(self):
        source = read("opening_sequence.rpy")
        for number in range(15):
            self.assertIn("label opening_scene_{:02d}:".format(number), source)

    def test_pre_system_screens_exist(self):
        source = read("screens_opening_system.rpy")
        for name in (
            "opening_disclaimer_one",
            "opening_disclaimer_two",
            "opening_tap_to_start",
            "opening_water_drop",
            "opening_memory_overlay",
        ):
            self.assertIn("screen " + name, source)
```

- [ ] **Step 2: Run contracts and verify failure**

Expected: scene labels and screens are missing.

- [ ] **Step 3: Implement disclaimer and start screens**

Add:

```renpy
transform opening_blink:
    alpha 0.35
    linear 0.55 alpha 1.0
    linear 0.55 alpha 0.35
    repeat

screen opening_disclaimer_one():
    modal True
    add Solid("#000000")
    text "【免责声明】\n\n本作品为虚构故事。作品中的人物、团体、事件、医疗与心理描写均经过艺术加工；若与现实相似，均属巧合。\n\n本作品涉及精神疾病、创伤记忆、失忆、血腥暴力、自伤意念、死亡及其他可能引起不适的内容。相关描写不构成医学、心理、法律或其他专业建议，也不应在现实中模仿或尝试。":
        style "opening_disclaimer_text"

screen opening_disclaimer_two():
    modal True
    add Solid("#000000")
    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1320
        spacing 44
        text "本作品包含闪烁画面、快速转场、画面抖动、强对比图像等视觉刺激。若您曾有癫痫、晕厥、光敏反应或相关病史，请在游玩前咨询专业医师。游玩中如出现头晕、恶心、视物异常、抽搐、意识模糊或其他不适，请立即停止游玩并寻求帮助。\n\n继续游玩即表示您已阅读并理解以上内容。":
            style "opening_disclaimer_text"
        hbox:
            xalign 0.5
            spacing 36
            textbutton "是" action Return(True)
            textbutton "否" action MainMenu(confirm=False)

screen opening_tap_to_start():
    modal True
    add Solid("#000000")
    text "TAP TO START" at opening_blink:
        xalign 0.5
        yalign 0.5
        style "opening_pixel_prompt"
    key "dismiss" action Return()
```

- [ ] **Step 4: Implement water and memory screens**

Use ATL circles or small generated PNGs. The screen contract is:

```renpy
screen opening_water_drop(auto=False):
    modal True
    add Solid("#000000")
    if not auto:
        key "dismiss" action Return()
    else:
        timer 1.2 action Return()
        add "opening water drop" at opening_drop_fall
        add "opening ripple" at opening_ripple_expand

screen opening_memory_overlay(lines):
    add Solid("#00000080")
    vbox:
        xalign 0.5
        yalign 0.5
        xsize 1350
        spacing 18
        for line in lines:
            text line style "opening_memory_text"
```

If assets are used, create them under `game/images/opening/` and define stable tags:

```renpy
image opening water drop = "images/opening/water_drop.png"
image opening ripple = "images/opening/water_ripple.png"
```

- [ ] **Step 5: Create Scene 00–06 labels**

Create `game/opening_sequence.rpy` with exact document text and:

```renpy
label opening_scene_00:
    show screen opening_disclaimer_one
    pause 3.0 hard True
    hide screen opening_disclaimer_one
    jump opening_scene_01

label opening_scene_01:
    call screen opening_disclaimer_two
    jump opening_scene_02

label opening_scene_02:
    call screen opening_tap_to_start
    jump opening_scene_03

label opening_scene_03:
    call screen opening_water_drop(auto=False)
    call screen opening_water_drop(auto=True)
    call screen opening_water_drop(auto=True)
    call screen opening_water_drop(auto=True)
    jump opening_scene_04

label opening_scene_04:
    scene black
    centered "弗洛，弗洛——"
    pause 0.8
    jump opening_scene_05
```

Scene 05 shows the loading desktop and `subtle` CRT. Scene 06 appends each emergency line to a local list and re-shows `opening_memory_overlay(lines)` after each pause.

- [ ] **Step 6: Run tests and lint**

Expected: contracts pass; all labels/screens parse.

- [ ] **Step 7: Manually play Scene 00–06**

Verify timer, “否” path, keyboard/mouse dismissal, first manual drop, two automatic drops, and accumulated memory lines.

- [ ] **Step 8: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_sequence.rpy game/screens_opening_system.rpy game/images/opening tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: add opening disclaimers and memory scenes"
```

### Task 6: Implement loading, consent scrolling, and medical document content

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Modify: `game/opening_sequence.rpy`
- Create: `game/audio/opening/README.md`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing system-flow contracts**

Add:

```python
    def test_medical_system_screens_exist(self):
        source = read("screens_opening_system.rpy")
        for name in (
            "opening_loading_body",
            "opening_records_body",
            "opening_notice_body",
            "opening_consent_body",
        ):
            self.assertIn("screen " + name, source)
        self.assertIn("consent_adjustment", source)
        self.assertIn("opening_consent_at_bottom", source)

    def test_document_contains_required_sections(self):
        source = read("screens_opening_system.rpy")
        for heading in ("一、治疗目的", "二、治疗方式", "三、可能风险", "四、替代方案", "五、信息核对", "六、患者声明"):
            self.assertIn(heading, source)
```

- [ ] **Step 2: Run tests and verify failure**

Expected: loading/record/consent screens and document sections are missing.

- [ ] **Step 3: Add safe audio helper and manifest**

In `game/opening_sequence.rpy`:

```renpy
init python:
    def opening_play_sound(path, channel="sound", loop=False):
        if renpy.loadable(path):
            renpy.music.play(path, channel=channel, loop=loop)
```

Create `game/audio/opening/README.md` listing:

```text
electrical_burst.ogg
water_drop_primary.ogg
water_drop_soft.ogg
footsteps_urgent.ogg
heavy_impact.ogg
emergency_radio.ogg
wind_gap.ogg
stretcher_wheels.ogg
metal_scrape.ogg
handoff_shout.ogg
isolation_door.ogg
keyboard_fast.ogg
paper_flip.ogg
electronic_low.ogg
```

State that missing files are intentionally silent through `opening_play_sound()`.

- [ ] **Step 4: Implement loading and records screens**

Use:

```renpy
screen opening_loading_body():
    hbox:
        spacing 30
        frame:
            style "opening_paper_frame"
            text "正在建立安全连接……" style "opening_document_text"
        use opening_oscilloscope

screen opening_records_body(progress, status_text):
    fixed:
        use opening_record_windows(progress)
        vbox:
            xalign 0.5
            yalign 0.82
            bar value StaticValue(progress, 100.0) style "opening_progress_bar"
            text status_text style "opening_loading_status"
```

Animate progress and status text from Scene 08 using short pauses and repeated screen updates.

- [ ] **Step 5: Implement consent viewport and bottom detection**

Use a screen-local adjustment:

```renpy
init python:
    def opening_consent_at_bottom(adjustment):
        return adjustment.range <= 0 or adjustment.value >= adjustment.range - 4

screen opening_consent_body():
    modal True
    default consent_adjustment = ui.adjustment()

    use opening_system_desktop(
        "opening_consent_document",
        {"consent_adjustment": consent_adjustment},
    )

    if opening_consent_at_bottom(consent_adjustment):
        textbutton "下一页":
            style "opening_primary_button"
            action Return(True)
    else:
        textbutton "下一页":
            style "opening_disabled_button"
            action NullAction()
```

The document viewport must pass:

```renpy
viewport:
    yadjustment consent_adjustment
    mousewheel True
    draggable True
    scrollbars "vertical"
```

Populate all six document sections from `系统背景界面.docx`, preserving black redaction blocks with `Solid("#252927")` or block glyphs inside fixed-width text runs.

- [ ] **Step 6: Implement Scene 07–11**

Use `interference` for system intervention and records loading, return to `subtle` for the notice and consent document, and reproduce the two memory overlays exactly.

- [ ] **Step 7: Run tests and lint**

Expected: contracts pass; no new undefined screen, action, or adjustment errors.

- [ ] **Step 8: Manually test document scrolling**

Verify:

- wheel and scrollbar drag work;
- “下一页” remains disabled until the actual bottom;
- returning from a save/load does not bypass the requirement;
- `subtle` CRT leaves the smallest document text readable.

- [ ] **Step 9: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_sequence.rpy game/screens_opening_system.rpy game/audio/opening/README.md tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: add medical loading and consent flow"
```

### Task 7: Implement stat allocation and hold-to-sign

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Modify: `game/opening_sequence.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing interaction contracts**

Add:

```python
    def test_stat_and_signature_contracts_exist(self):
        source = read("screens_opening_system.rpy")
        self.assertIn("screen opening_identity_body", source)
        self.assertIn("opening_adjust_stat", source)
        self.assertIn("opening_stat_points_remaining", source)
        self.assertIn("opening_stats_complete", source)
        self.assertIn("signature_progress", source)
        self.assertIn("1.5", source)
        self.assertIn('key "mousedown_1"', source)
        self.assertIn('key "mouseup_1"', source)
```

- [ ] **Step 2: Run contracts and verify failure**

Expected: identity and signature controls are missing.

- [ ] **Step 3: Implement stat rows**

Use:

```renpy
screen opening_stat_row(label_text, stat_name, value, locked=False):
    hbox:
        xfill True
        text label_text style "opening_stat_label"
        if locked:
            text "[value]" style "opening_stat_value"
            text "固定" style "opening_stat_locked"
        else:
            textbutton "−":
                sensitive opening_can_adjust_stat(stat_name, -1)
                action Function(opening_adjust_stat, stat_name, -1)
            text "[value]" style "opening_stat_value"
            textbutton "+":
                sensitive opening_can_adjust_stat(stat_name, 1)
                action Function(opening_adjust_stat, stat_name, 1)
```

The identity screen calls rows for CON, STR, DEX, INT, and POW, and shows:

```renpy
text "剩余可分配点数：[opening_stat_points_remaining()]"
```

- [ ] **Step 4: Implement hold-to-sign state machine**

Use screen-local state:

```renpy
screen opening_identity_body():
    modal True
    default signature_hovered = False
    default signature_holding = False
    default signature_progress = 0.0
    default signature_complete = False

    if signature_holding and not signature_complete:
        timer 0.05 repeat True action SetScreenVariable(
            "signature_progress",
            min(1.5, signature_progress + 0.05),
        )

    if signature_progress >= 1.5 and not signature_complete:
        timer 0.01 action [
            SetScreenVariable("signature_complete", True),
            Return(True),
        ]

    key "mousedown_1" action If(
        signature_hovered and opening_stats_complete(),
        SetScreenVariable("signature_holding", True),
        NullAction(),
    )

    key "mouseup_1" action [
        SetScreenVariable("signature_holding", False),
        If(
            signature_progress < 1.5,
            SetScreenVariable("signature_progress", 0.0),
            NullAction(),
        ),
    ]

    button:
        sensitive opening_stats_complete()
        hovered SetScreenVariable("signature_hovered", True)
        unhovered [
            SetScreenVariable("signature_hovered", False),
            SetScreenVariable("signature_holding", False),
            If(
                signature_progress < 1.5,
                SetScreenVariable("signature_progress", 0.0),
                NullAction(),
            ),
        ]
        vbox:
            text "长按确认并签名"
            bar value StaticValue(signature_progress, 1.5)
```

If Ren’Py does not deliver mouse key events while the button is hovered, use the smallest supported alternative: an invisible full-button `mousearea` to set hover state plus screen-level `mousedown_1`/`mouseup_1`. Do not replace the requirement with a normal click.

- [ ] **Step 5: Implement Scene 12 identity inserts**

Before the final interactive screen:

- show the identity page;
- cut to black and show `弗洛`;
- return;
- cut to black and show an empty white date box;
- return;
- display the material-use warning;
- call `opening_identity_body`.

- [ ] **Step 6: Run unit tests, contracts, and lint**

Expected: all pass.

- [ ] **Step 7: Manually test boundary and hold behavior**

Test:

- every adjustable stat stops at 1 and 20;
- CON is locked at 3;
- exactly 17 points can be spent;
- signing cannot start with points remaining;
- releasing at 1.45 seconds resets to zero;
- holding through 1.5 seconds returns once.

- [ ] **Step 8: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_sequence.rpy game/screens_opening_system.rpy tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' commit -m "feat: add opening stat allocation and signature"
```

### Task 8: Add verification, shutdown, countdown, and story handoff

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Modify: `game/opening_sequence.rpy`
- Modify: `game/script.rpy`
- Delete: `game/screens_medical.rpy`
- Modify: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add failing end-to-end contracts**

Add:

```python
    def test_opening_handoff_and_cleanup(self):
        opening = read("opening_sequence.rpy")
        script = read("script.rpy")
        self.assertIn("label complete_opening_sequence:", opening)
        self.assertIn("jump complete_opening_sequence", script)
        self.assertIn("label mountain_memory_start:", script)
        self.assertIn("jump mountain_memory_start", opening)
        self.assertIn("hide screen crt_effect", opening)
        self.assertIn("label opening_scene_14:", opening)
        for number in ("3", "2", "1"):
            self.assertIn('"' + number + '"', opening)

    def test_obsolete_medical_opening_is_removed(self):
        self.assertFalse((GAME / "screens_medical.rpy").exists())
        script = read("script.rpy")
        self.assertNotIn("medical_system_panel", script)
        self.assertNotIn("medical_confirm", script)
```

- [ ] **Step 2: Run contracts and verify failure**

Expected: handoff labels and cleanup are absent; obsolete medical screen still exists.

- [ ] **Step 3: Implement verification and countdown screens**

Add:

```renpy
screen opening_verification_body(status_text, progress):
    use opening_system_desktop(
        "opening_verification_panel",
        {"status_text": status_text, "progress": progress},
    )

screen opening_countdown(number):
    add Solid("#000000")
    text number:
        xalign 0.5
        yalign 0.5
        size 220
        color "#ffffff"
```

- [ ] **Step 4: Implement Scene 13 and 14**

Use:

```renpy
label opening_scene_13:
    show screen crt_effect(mode="interference")
    show screen opening_verification_body(status_text="核验通过。", progress=35)
    pause 0.7
    show screen opening_verification_body(status_text="医疗单元已就位。", progress=72)
    pause 0.7
    show screen opening_verification_body(status_text="意识将在 3 秒内重启。", progress=100)
    pause 0.8
    hide screen crt_effect
    show screen crt_effect(mode="shutdown")
    pause 0.45
    hide screen opening_verification_body
    hide screen crt_effect
    scene black
    jump opening_scene_14

label opening_scene_14:
    scene black
    show screen opening_countdown("3")
    pause 0.8
    show screen opening_countdown("2")
    pause 0.8
    show screen opening_countdown("1")
    pause 0.8
    hide screen opening_countdown
    scene black
    pause 2.5 hard True
    jump mountain_memory_start

label complete_opening_sequence:
    jump opening_scene_00
```

Because each scene jumps to the next, `complete_opening_sequence` is the public entry and Scene 14 jumps directly into the story continuation.

- [ ] **Step 5: Rewire `script.rpy`**

Replace the current opening block with:

```renpy
label start:
    jump complete_opening_sequence

label mountain_memory_start:
    wind "听北地的牧民说，如果在日出的时候在神山顶上向山神许愿，山神就会实现信徒的全部愿望。弗洛，等我们放假了，也去神山玩吧！"
```

Keep every existing line after that first `wind` line in its current order.

Delete `game/screens_medical.rpy` because its screens are no longer referenced.

- [ ] **Step 6: Run all automated checks**

Expected:

- stat unit tests pass;
- contract tests pass;
- Ren’Py lint has no new opening errors;
- no `medical_system_panel` reference remains.

- [ ] **Step 7: Play the complete opening**

Verify every Scene 00–14 transition and that the first mountain-memory line appears immediately after the final silence.

- [ ] **Step 8: Sync and commit**

Commit:

```powershell
git -C 'E:\Re-Memorial' add game/opening_sequence.rpy game/screens_opening_system.rpy game/script.rpy tools/test_opening_contracts.py
git -C 'E:\Re-Memorial' rm game/screens_medical.rpy
git -C 'E:\Re-Memorial' commit -m "feat: complete opening sequence and story handoff"
```

### Task 9: Final visual QA and regression verification

**Files:**
- Modify as needed: `game/screens_opening_system.rpy`
- Modify as needed: `game/opening_sequence.rpy`
- Modify as needed: `game/crt_effect.rpy`
- Modify: `docs/superpowers/plans/2026-06-19-opening-sequence.md` only to check completed boxes during execution

- [ ] **Step 1: Run the full automated verification suite**

Run unit tests, contract tests, and Ren’Py lint.

Expected: all tests pass and no new lint errors.

- [ ] **Step 2: Capture 1920×1080 screenshots**

Capture at least:

- Scene 05 loading;
- Scene 08 records loading;
- Scene 11 consent at top and bottom;
- Scene 12 stat allocation;
- Scene 13 verification;
- Scene 14 countdown.

- [ ] **Step 3: Inspect every screenshot**

Check:

- equal four-sided blue border;
- no content escapes the border;
- one thin pale-blue taskbar line;
- darkened non-primary background;
- readable document text under `subtle`;
- no clipped controls or Chinese glyphs;
- oscilloscope is muted, not fluorescent;
- stat values and remaining points align;
- signature progress stays inside its button.

- [ ] **Step 4: Run complete interaction regression**

Test:

- disclaimer “否” returns to menu;
- disclaimer “是” reaches Scene 02;
- save/load during consent does not unlock early;
- save/load during stat allocation preserves values;
- CRT is absent after Scene 14;
- existing mountain memory, hospital scene, phone, inventory, and character sprites still work.

- [ ] **Step 5: Fix only verified defects**

For each defect, add or tighten a contract test where practical, reproduce the failure, make the smallest correction, and rerun the relevant checks.

- [ ] **Step 6: Perform final sync**

Sync changed source/assets/docs/tools to `E:\Re-Memorial`, excluding:

```text
game/cache/
game/saves/
*.rpyc
*.rpymc
log.txt
errors.txt
traceback.txt
```

- [ ] **Step 7: Run final verification from active project**

Run all tests and lint one final time after sync comparison.

Expected: fresh passing output.

- [ ] **Step 8: Commit final QA adjustments**

```powershell
git -C 'E:\Re-Memorial' add game tools docs
git -C 'E:\Re-Memorial' commit -m "fix: polish opening sequence presentation"
```

Skip this commit only if Task 9 produced no changes.
