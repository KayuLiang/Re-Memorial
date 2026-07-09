# UI Test Menu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a main-menu `UI测试` entry that lets testers launch either the check UI from schedule selection or the reward-selection UI directly.

**Architecture:** Reuse the existing `rm_test_flow_start`, `rm_test_flow_loop`, `rm_test_resolve_pending_cards`, and pending reward machinery. Add only a small menu label, a direct reward-test label, and one helper that prepares a pending growth reward for the reward UI path.

**Tech Stack:** Ren'Py `.rpy` screens/labels, Python helpers inside Ren'Py init blocks, Python `unittest` static tests, Ren'Py lint.

---

## File Structure

- Modify `E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py`: add static tests for the main-menu button, the UI test label, and the reward setup helper.
- Modify `E:\RenpyProject\ReMemorial\game\screens.rpy`: add `UI测试` to `screen navigation()` when `main_menu` is true.
- Modify `E:\RenpyProject\ReMemorial\game\story\9-9-9-test-flow.rpy`: add `rm_ui_test_menu` and `rm_ui_test_reward_choice` labels.
- Modify `E:\RenpyProject\ReMemorial\game\systems\rm_test_schedules.rpy`: add `rm_test_prepare_growth_reward_test(attr="str")`.
- Sync the modified source/test/plan files to `E:\Re-Memorial` before backup commit.

## Task 1: Add Static Tests

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py`
- Test: `E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py`

- [ ] **Step 1: Write the failing tests**

Add these methods to `RMTestFlowRenpyTests`:

```python
    def test_main_menu_exposes_ui_test_entry(self):
        source = (ROOT / "game" / "screens.rpy").read_text(encoding="utf-8")
        self.assertIn('textbutton _("UI测试") action Start("rm_ui_test_menu")', source)

    def test_ui_test_menu_routes_to_check_and_reward_flows(self):
        source = TEST_FLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("label rm_ui_test_menu:", source)
        self.assertIn('"接下来要测试什么呢？"', source)
        self.assertIn('"检定界面":', source)
        self.assertIn("jump rm_test_flow_loop", source)
        self.assertIn('"奖励选择":', source)
        self.assertIn("call rm_ui_test_reward_choice", source)
        self.assertIn('"返回标题菜单":', source)
        self.assertIn("return", source)

    def test_reward_ui_test_flow_prepares_pending_growth_reward(self):
        source = TEST_FLOW_PATH.read_text(encoding="utf-8")
        helper_source = TEST_SCHEDULES_PATH.read_text(encoding="utf-8")
        self.assertIn("label rm_ui_test_reward_choice:", source)
        self.assertIn("$ rm_test_prepare_growth_reward_test()", source)
        self.assertIn("call rm_test_resolve_pending_cards", source)
        self.assertIn("def rm_test_prepare_growth_reward_test(attr=\"str\"):", helper_source)
        self.assertIn("rm_core.add_growth_reward_pending(character, attr, 1)", helper_source)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py
```

Expected: FAIL because `UI测试`, `rm_ui_test_menu`, and `rm_test_prepare_growth_reward_test` do not exist yet.

## Task 2: Implement the UI Test Entry

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\game\screens.rpy`
- Modify: `E:\RenpyProject\ReMemorial\game\story\9-9-9-test-flow.rpy`
- Modify: `E:\RenpyProject\ReMemorial\game\systems\rm_test_schedules.rpy`
- Test: `E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py`

- [ ] **Step 1: Add the main-menu button**

In `screen navigation()`, add the button inside the `if main_menu:` block:

```renpy
            textbutton _("开始游戏") action Start()
            textbutton _("开始测试") action Start("rm_test_flow_start")
            textbutton _("UI测试") action Start("rm_ui_test_menu")
```

- [ ] **Step 2: Add the reward setup helper**

Inside `init -9 python:` in `rm_test_schedules.rpy`, add:

```python
    def rm_test_prepare_growth_reward_test(attr="str"):
        character = rm_ensure_player()
        rm_core.add_growth_reward_pending(character, attr, 1)
        return rm_test_pending_card_request(character)
```

- [ ] **Step 3: Add the UI test labels**

In `9-9-9-test-flow.rpy`, add labels near the existing `rm_test_flow_start` label:

```renpy
label rm_ui_test_menu:
    menu:
        "接下来要测试什么呢？"

        "检定界面":
            $ rm_test_start_flow()
            jump rm_test_flow_loop

        "奖励选择":
            call rm_ui_test_reward_choice
            jump rm_ui_test_menu

        "返回标题菜单":
            return


label rm_ui_test_reward_choice:
    $ rm_test_start_flow()
    $ rm_test_reward_request = rm_test_prepare_growth_reward_test()
    if rm_test_reward_request:
        call rm_test_resolve_pending_cards
        "[rm_test_pending_result_text]"
    else:
        "奖励选择测试无法启动：没有可用的成长奖励。"
    return
```

- [ ] **Step 4: Run the focused test to verify it passes**

Run:

```powershell
python -m unittest E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py
```

Expected: PASS.

## Task 3: Verify and Back Up

**Files:**
- Sync: `E:\RenpyProject\ReMemorial\game\screens.rpy`
- Sync: `E:\RenpyProject\ReMemorial\game\story\9-9-9-test-flow.rpy`
- Sync: `E:\RenpyProject\ReMemorial\game\systems\rm_test_schedules.rpy`
- Sync: `E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py`
- Sync: `E:\RenpyProject\ReMemorial\docs\superpowers\plans\2026-07-09-ui-test-menu.md`

- [ ] **Step 1: Run the focused Python test**

Run:

```powershell
python -m unittest E:\RenpyProject\ReMemorial\tests\test_rm_test_flow.py
```

Expected: PASS.

- [ ] **Step 2: Run Ren'Py lint**

Run the local Ren'Py lint command used for this project. If the executable is not on PATH, locate it from the installed Ren'Py SDK and lint `E:\RenpyProject\ReMemorial`.

Expected: lint completes without new errors from `screens.rpy`, `9-9-9-test-flow.rpy`, or `rm_test_schedules.rpy`.

- [ ] **Step 3: Sync to backup repository**

Copy only these changed files to `E:\Re-Memorial`:

```text
game/screens.rpy
game/story/9-9-9-test-flow.rpy
game/systems/rm_test_schedules.rpy
tests/test_rm_test_flow.py
docs/superpowers/plans/2026-07-09-ui-test-menu.md
```

- [ ] **Step 4: Commit from backup repository**

Run:

```powershell
git -C E:\Re-Memorial add -- game/screens.rpy game/story/9-9-9-test-flow.rpy game/systems/rm_test_schedules.rpy tests/test_rm_test_flow.py docs/superpowers/plans/2026-07-09-ui-test-menu.md
git -C E:\Re-Memorial commit -m "feat: add ui test menu"
```

Expected: one commit containing only the UI test menu implementation, tests, and implementation plan.

## Self-Review

- Spec coverage: `UI测试` main-menu entry, `接下来要测试什么呢？` selector, `检定界面`, `奖励选择`, direct pending growth reward, return to title menu, and lint verification are all covered.
- Placeholder scan: no TBD/TODO/fill-in-later instructions remain.
- Type consistency: labels and helper names are consistent across tests, plan, and intended implementation.
