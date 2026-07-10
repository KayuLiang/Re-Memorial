# UI Test Skin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a UI-test-only skin layer for the new dialogue, HUD, and dice-check assets.

**Architecture:** Keep the production `say` screen and formal story HUD visually unchanged. Add `rm_ui_test_*` screens and a `rm_ui_test_skin_active` gate so UI-test flows can show the processed assets while normal story/test entry points keep their current UI.

**Tech Stack:** Ren'Py screen language, Ren'Py displayables/styles, Python `unittest` static tests, PowerShell/.NET `System.Drawing` asset processing, Ren'Py lint.

---

## File Structure

- Create `E:\RenpyProject\ReMemorial\tests\test_ui_test_skin.py`: static tests for UI-test skin assets, menu routes, gated screens/styles, and production UI isolation.
- Create `E:\RenpyProject\ReMemorial\game\screens_ui_test_skin.rpy`: UI-test dialogue preview, HUD preview, HUD overlay, transforms, and helper functions.
- Modify `E:\RenpyProject\ReMemorial\game\story\9-9-9-test-flow.rpy`: add UI-test menu choices and set/reset `rm_ui_test_skin_active`.
- Modify `E:\RenpyProject\ReMemorial\game\screens_story_hud.rpy`: suppress the formal HUD while the UI-test skin HUD is active.
- Modify `E:\RenpyProject\ReMemorial\game\screens_attribute_checks.rpy`: gate dice-check panel/stage/card/button style backgrounds through `rm_ui_test_skin_active`.
- Modify `E:\RenpyProject\ReMemorial\game\systems\rm_test_schedules.rpy`: gate schedule and reward test panel/card styles through `rm_ui_test_skin_active`.
- Create processed PNGs in `E:\RenpyProject\ReMemorial\game\gui\ui_test_skin`.
- Sync the changed files and processed PNGs to `E:\Re-Memorial` before backup commit.

## Task 1: Add Static Tests

**Files:**
- Create: `E:\RenpyProject\ReMemorial\tests\test_ui_test_skin.py`

- [ ] **Step 1: Write the failing tests**

Create tests that assert:

```python
expected_assets = (
    "dialogue_photo_avatar.png",
    "dialogue_paper.png",
    "name_tape.png",
    "clock_face.png",
    "clock_hand.png",
    "mood_bar.png",
    "mood_cursor.png",
    "dice_check_panel.png",
    "check_stage.png",
    "dice_list.png",
    "dice_card.png",
    "option_button.png",
)
```

The tests must also assert `screen rm_ui_test_dialogue_preview`, `screen rm_ui_test_hud_preview`, `screen rm_ui_test_skin_hud`, `default rm_ui_test_skin_active = False`, UI-test menu choices `对话框UI` and `时钟与心境条`, and no `gui/ui_test_skin` asset paths inside the production `screen say(who, what):` or `screen top_status():` blocks.

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
py -3.10 -m unittest tests.test_ui_test_skin -v
```

Expected: FAIL because the new test file references assets and screens that do not exist yet.

## Task 2: Process UI-Test Assets

**Files:**
- Create PNGs under `E:\RenpyProject\ReMemorial\game\gui\ui_test_skin`

- [ ] **Step 1: Generate transparent assets**

Use PowerShell with `.NET System.Drawing` to load each selected source PNG, convert near-white background pixels to transparent alpha, trim transparent margins with padding, and save transparent PNG output.

- [ ] **Step 2: Inspect representative output**

Use `view_image` on at least `dialogue_photo_avatar.png`, `mood_bar.png`, and `dice_check_panel.png` to confirm transparency/cropping keeps paper edges and shadows.

## Task 3: Add UI-Test Screens and Routes

**Files:**
- Create: `E:\RenpyProject\ReMemorial\game\screens_ui_test_skin.rpy`
- Modify: `E:\RenpyProject\ReMemorial\game\story\9-9-9-test-flow.rpy`
- Modify: `E:\RenpyProject\ReMemorial\game\screens_story_hud.rpy`

- [ ] **Step 1: Add `screens_ui_test_skin.rpy`**

Define `default rm_ui_test_skin_active = False`, append `rm_ui_test_skin_hud` to overlays, and add the dialogue preview, HUD preview, and UI-test HUD overlay screens.

- [ ] **Step 2: Update UI-test menu routes**

Add menu choices for `对话框UI` and `时钟与心境条`. Set `rm_ui_test_skin_active = True` for UI-test skin paths and reset it before returning to the title menu.

- [ ] **Step 3: Keep production HUD isolated**

Update `top_status` so the formal HUD does not render while `rm_ui_test_skin_active` is true.

## Task 4: Gate Dice and Test-Panel Styles

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\game\screens_attribute_checks.rpy`
- Modify: `E:\RenpyProject\ReMemorial\game\systems\rm_test_schedules.rpy`

- [ ] **Step 1: Add conditional displayables to dice-check styles**

Use `ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/...", ...), "True", Solid(...))` for the major panel/stage/button/card surfaces.

- [ ] **Step 2: Add conditional displayables to schedule/reward styles**

Use the same gate for schedule frames, schedule buttons, and reward card buttons.

## Task 5: Verify, Sync, and Commit

**Files:**
- Sync all changed files and generated PNGs to `E:\Re-Memorial`.

- [ ] **Step 1: Run focused tests**

Run:

```powershell
py -3.10 -m unittest tests.test_ui_test_skin -v
```

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run:

```powershell
py -3.10 -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 3: Run Ren'Py lint**

Run:

```powershell
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' lint
```

Expected: exit code 0.

- [ ] **Step 4: Commit only related files from backup repo**

Stage only the plan, test, changed `.rpy` files, and `game/gui/ui_test_skin/*.png` in `E:\Re-Memorial`. Leave unrelated existing dirty files untouched.
