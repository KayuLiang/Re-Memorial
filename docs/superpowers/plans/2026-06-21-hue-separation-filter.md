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

- [ ] Declare the effect path beside `CRT_EFFECT_PATH`.
- [ ] Add focused contracts for the public API, shader, transforms, numeric bounds, layer cleanup, and non-stacking behavior.
- [ ] Run `py -m unittest tools.test_opening_contracts.HueSeparationEffectContractTests -v` and verify RED because the effect file does not exist.

### Task 2: Implement shader, cameras, and runtime controller

**Files:**
- Create: `game/hue_separation_effect.rpy`
- Test: `tools/test_opening_contracts.py`

- [ ] Add approved constants, runtime state, and the `rememorial.hue_separation` shader.
- [ ] Add a dynamic camera transform driven by shared pixel-separation state.
- [ ] Implement camera application and cleanup, randomized scheduling, peak start, and peak end helpers.
- [ ] Implement validated `hue_separation_start` and complete `hue_separation_stop` APIs.
- [ ] Add one timer-only glitch controller.
- [ ] Run `py -m unittest tools.test_opening_contracts.HueSeparationEffectContractTests -v` and verify GREEN.

### Task 3: Compile, lint, and synchronize deliverables

**Files:**
- Verify: `game/hue_separation_effect.rpy`
- Sync: `game/hue_separation_effect.rpy`
- Sync: `tools/test_opening_contracts.py`
- Sync: `docs/superpowers/plans/2026-06-21-hue-separation-filter.md`

- [ ] Run `py -m unittest tools.test_opening_contracts -v`.
- [ ] Compile with `E:\renpy-8.5.3-sdk\renpy.exe E:\RenpyProject\ReMemorial compile`.
- [ ] Lint with `E:\renpy-8.5.3-sdk\renpy.exe E:\RenpyProject\ReMemorial lint`.
- [ ] Sync only the feature files into `E:\Re-Memorial`.
- [ ] Verify and commit the feature files as `feat: add reusable hue separation filter`.
