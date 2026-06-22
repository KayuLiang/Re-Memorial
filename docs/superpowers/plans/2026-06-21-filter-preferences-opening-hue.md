# Filter Preferences and Opening Hue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent immediate CRT/hue display toggles and request fullscreen glitch hue separation throughout the opening medical-system sequence.

**Architecture:** Each effect file owns its persistent default and runtime toggle helper. The preferences screen only renders selected toggle buttons; story APIs continue recording requested state while player preferences determine whether visual layers/cameras render.

**Tech Stack:** Ren'Py screen language, persistent defaults, `Function`/`SelectedIf` actions, GLSL camera effect, Python unittest contracts.

---

### Task 1: Add failing contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [ ] Add contracts requiring:
  - `default persistent.crt_effect_enabled = True`
  - `default persistent.hue_separation_enabled = True`
  - CRT screen conditional rendering and `set_crt_effect_enabled`
  - hue preference setter, disable cleanup, active-request restoration, and disabled start behavior
  - two selected Display controls in `screen preferences()`
  - opening scene 05 starts `glitch + fullscreen`
  - opening scene 13 stops hue before final cleanup
- [ ] Run focused classes and verify failures are caused by missing preference integration.

### Task 2: Implement effect preference gates

**Files:**
- Modify: `game/crt_effect.rpy`
- Modify: `game/hue_separation_effect.rpy`

- [ ] Add both persistent defaults.
- [ ] Add `set_crt_effect_enabled(enabled)` and gate CRT visual children with `if persistent.crt_effect_enabled`.
- [ ] Add `set_hue_separation_enabled(enabled)`:
  - disabling clears both cameras, hides controller, and restores baseline state without clearing the request;
  - enabling restores active cameras and reschedules/restarts glitch;
  - inactive requests remain hidden.
- [ ] Make `hue_separation_start` record request state but skip cameras/controller while disabled.
- [ ] Run focused tests and verify GREEN.

### Task 3: Add settings controls and opening calls

**Files:**
- Modify: `game/screens.rpy`
- Modify: `game/opening_sequence.rpy`

- [ ] Add `CRT 滤镜` and `色相差滤镜` buttons under Display using:

```renpy
action Function(set_crt_effect_enabled, not persistent.crt_effect_enabled)
selected persistent.crt_effect_enabled
```

and the equivalent hue helper.

- [ ] Start hue separation after the medical desktop appears in `opening_scene_05`.
- [ ] Stop hue separation in `opening_scene_13` before the desktop/effect cleanup and black handoff.
- [ ] Run focused tests and verify GREEN.

### Task 4: Verify, sync, and commit

**Files:**
- Sync feature patches to matching paths under `E:\Re-Memorial`.

- [ ] Run the complete unittest suite.
- [ ] Run Ren'Py compile and lint.
- [ ] Sync only the four runtime files, relevant test hunks, and this plan.
- [ ] Stage only feature-related hunks in dirty shared files.
- [ ] Commit from `E:\Re-Memorial` with `feat: add filter display preferences`.
- [ ] Push `main`; if the network is unavailable, preserve and report the local commit.
