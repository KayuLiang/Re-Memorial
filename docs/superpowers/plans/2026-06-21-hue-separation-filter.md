# Hue Separation Filter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable red/cyan hue-separation shader with steady and randomized glitch modes, selectable for scene-only or fullscreen scope.

**Architecture:** A single `hue_separation_effect.rpy` owns the shader, layer-camera transforms, public start/stop API, and one timer-only controller screen. Shared store state drives both layer cameras so fullscreen peaks remain synchronized; contract tests verify the API, bounds, layer cleanup, and non-stacking behavior.

**Tech Stack:** Ren'Py 8.5.3 model-based rendering, GLSL, camera transforms, screen timers, rollback-safe `renpy.random`, Python `unittest`.

---

### Task 1: Add failing filter contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`
- Test: `tools/test_opening_contracts.py`

- [ ] **Step 1: Declare the effect path**

Add beside `CRT_EFFECT_PATH`:

```python
HUE_SEPARATION_EFFECT_PATH = GAME_DIR / "hue_separation_effect.rpy"
```

- [ ] **Step 2: Add focused contract tests**

Add `HueSeparationEffectContractTests` before `OpeningSystemShellContractTests`. The class must read the new file in `setUp` and assert:

```python
class HueSeparationEffectContractTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(HUE_SEPARATION_EFFECT_PATH.is_file())
        self.source = HUE_SEPARATION_EFFECT_PATH.read_text(encoding="utf-8")

    def test_public_api_and_modes_exist(self):
        self.assertIn("def hue_separation_start(mode=\"steady\", scope=\"scene\"):", self.source)
        self.assertIn("def hue_separation_stop():", self.source)
        self.assertIn('("steady", "glitch")', self.source)
        self.assertIn('("scene", "fullscreen")', self.source)

    def test_shader_and_camera_transform_exist(self):
        self.assertIn('renpy.register_shader("rememorial.hue_separation"', self.source)
        self.assertIn("uniform float u_hue_separation_pixels;", self.source)
        self.assertIn("transform hue_separation_camera:", self.source)
        self.assertIn('shader "rememorial.hue_separation"', self.source)
        self.assertIn("function hue_separation_camera_update", self.source)

    def test_strength_and_random_bounds_are_explicit(self):
        for fragment in (
            "define hue_separation_baseline_pixels = 3.0",
            "define hue_separation_peak_pixels_min = 8.0",
            "define hue_separation_peak_pixels_max = 18.0",
            "define hue_separation_wait_min = 6.0",
            "define hue_separation_wait_max = 12.0",
            "define hue_separation_peak_duration_min = 0.1",
            "define hue_separation_peak_duration_max = 0.5",
        ):
            self.assertIn(fragment, self.source)

    def test_start_replaces_controller_and_applies_requested_layers(self):
        start_block = function_block(self.source, "hue_separation_start")
        self.assertIn('renpy.hide_screen("hue_separation_glitch_controller")', start_block)
        self.assertIn('_hue_separation_clear_camera("master")', start_block)
        self.assertIn('_hue_separation_clear_camera("screens")', start_block)
        self.assertIn('_hue_separation_apply_camera("master")', start_block)
        self.assertIn('if scope == "fullscreen":', start_block)
        self.assertIn('_hue_separation_apply_camera("screens")', start_block)
        self.assertIn('renpy.show_screen("hue_separation_glitch_controller")', start_block)

    def test_stop_clears_all_runtime_state(self):
        stop_block = function_block(self.source, "hue_separation_stop")
        self.assertIn('renpy.hide_screen("hue_separation_glitch_controller")', stop_block)
        self.assertIn('_hue_separation_clear_camera("master")', stop_block)
        self.assertIn('_hue_separation_clear_camera("screens")', stop_block)
        self.assertIn("hue_separation_active = False", stop_block)
        self.assertIn("hue_separation_pixels = 0.0", stop_block)

    def test_glitch_controller_uses_one_shared_peak_state(self):
        self.assertIn("screen hue_separation_glitch_controller():", self.source)
        self.assertIn("timer hue_separation_next_delay", self.source)
        self.assertIn("timer hue_separation_peak_duration", self.source)
        self.assertIn("Function(_hue_separation_begin_peak)", self.source)
        self.assertIn("Function(_hue_separation_end_peak)", self.source)
```

- [ ] **Step 3: Run the focused class and verify RED**

Run:

```powershell
python -m unittest tools.test_opening_contracts.HueSeparationEffectContractTests -v
```

Expected: FAIL because `game/hue_separation_effect.rpy` does not exist.

### Task 2: Implement shader, cameras, and runtime controller

**Files:**
- Create: `game/hue_separation_effect.rpy`
- Test: `tools/test_opening_contracts.py`

- [ ] **Step 1: Add constants, state, and shader**

Create the file with the approved numeric bounds, `default` runtime state, and:

```renpy
init python:
    renpy.register_shader(
        "rememorial.hue_separation",
        variables="""
            uniform sampler2D tex0;
            uniform vec2 u_model_size;
            uniform float u_hue_separation_pixels;
            varying vec2 v_tex_coord;
            attribute vec2 a_tex_coord;
        """,
        vertex_300="""
            v_tex_coord = a_tex_coord;
        """,
        fragment_300="""
            vec2 offset = vec2(u_hue_separation_pixels / u_model_size.x, 0.0);
            vec4 red_sample = texture2D(tex0, v_tex_coord - offset);
            vec4 center_sample = texture2D(tex0, v_tex_coord);
            vec4 cyan_sample = texture2D(tex0, v_tex_coord + offset);
            gl_FragColor = vec4(
                red_sample.r,
                center_sample.g,
                cyan_sample.b,
                max(center_sample.a, max(red_sample.a, cyan_sample.a))
            );
        """,
    )
```

- [ ] **Step 2: Add the dynamic camera transform**

Add a transform callback that updates the uniform from shared store state and continuously redraws:

```renpy
init python:
    def hue_separation_camera_update(trans, st, at):
        trans.u_hue_separation_pixels = hue_separation_pixels
        return 0

transform hue_separation_camera:
    mesh True
    shader "rememorial.hue_separation"
    function hue_separation_camera_update
```

- [ ] **Step 3: Add layer and glitch helpers**

Implement `_hue_separation_apply_camera`, `_hue_separation_clear_camera`, `_hue_separation_schedule_next`, `_hue_separation_begin_peak`, and `_hue_separation_end_peak`. Use:

```python
renpy.show_layer_at([hue_separation_camera], layer=layer_name, camera=True)
renpy.show_layer_at([], layer=layer_name, reset=True, camera=True)
renpy.random.uniform(minimum, maximum)
```

Beginning a peak sets one shared randomized pixel strength and randomized duration. Ending it restores the baseline and schedules the next 6–12 second delay.

- [ ] **Step 4: Add the public API**

`hue_separation_start` must:

1. Validate and warn/fallback invalid mode and scope.
2. Hide the existing controller and clear both cameras.
3. Set active mode/scope and the 3-pixel baseline.
4. Apply `master`, plus `screens` only for fullscreen.
5. Schedule/show exactly one controller only for glitch mode.
6. Restart interaction.

`hue_separation_stop` must hide the controller, clear both cameras, reset every runtime value, and restart interaction.

- [ ] **Step 5: Add the timer-only controller**

```renpy
screen hue_separation_glitch_controller():
    modal False

    if hue_separation_active and hue_separation_mode == "glitch":
        if hue_separation_peak_active:
            timer hue_separation_peak_duration action Function(_hue_separation_end_peak)
        else:
            timer hue_separation_next_delay action Function(_hue_separation_begin_peak)
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:

```powershell
python -m unittest tools.test_opening_contracts.HueSeparationEffectContractTests -v
```

Expected: all hue-separation tests PASS.

### Task 3: Compile, lint, and synchronize deliverables

**Files:**
- Modify if required by compile/lint findings: `game/hue_separation_effect.rpy`
- Sync: `game/hue_separation_effect.rpy`
- Sync: `tools/test_opening_contracts.py`
- Sync: `docs/superpowers/plans/2026-06-21-hue-separation-filter.md`

- [ ] **Step 1: Run the complete contract suite**

```powershell
python -m unittest tools.test_opening_contracts -v
```

Expected: all tests PASS.

- [ ] **Step 2: Compile Ren'Py scripts**

```powershell
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' compile
```

Expected: exit code 0 and no script errors.

- [ ] **Step 3: Run Ren'Py lint**

```powershell
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' lint
```

Expected: exit code 0 with no hue-separation errors.

- [ ] **Step 4: Sync only this feature's files to the backup repository**

Copy the three files listed above into matching paths under `E:\Re-Memorial`. Do not overwrite or stage unrelated dirty files.

- [ ] **Step 5: Verify the backup diff and commit only feature files**

```powershell
git diff --check -- game/hue_separation_effect.rpy tools/test_opening_contracts.py docs/superpowers/plans/2026-06-21-hue-separation-filter.md
git add -- game/hue_separation_effect.rpy tools/test_opening_contracts.py docs/superpowers/plans/2026-06-21-hue-separation-filter.md
git diff --cached --check
git commit -m "feat: add reusable hue separation filter"
```

Expected: one commit containing only the filter, its tests, and its implementation plan.
