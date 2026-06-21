# Filter Preferences and Opening Hue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent immediate CRT/hue display toggles and request fullscreen glitch hue separation throughout the opening medical-system sequence.

**Architecture:** Each effect file owns its persistent default and runtime toggle helper. The preferences screen only renders selected toggle buttons; story APIs continue recording requested state while player preferences determine whether visual layers/cameras render.

**Tech Stack:** Ren'Py screen language, persistent defaults, `Function`/`SelectedIf` actions, GLSL camera effect, Python unittest contracts.

---

### Task 1: Add failing contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [ ] Add contracts requiring persistent defaults, effect gates, settings controls, and opening calls.
- [ ] Run focused classes and verify failures are caused by missing preference integration.

### Task 2: Implement effect preference gates

**Files:**
- Modify: `game/crt_effect.rpy`
- Modify: `game/hue_separation_effect.rpy`

- [ ] Add persistent defaults and effect-specific setter functions.
- [ ] Gate CRT rendering while retaining the screen request.
- [ ] Preserve hue request state while disabled and restore active requests when enabled.
- [ ] Run focused tests and verify GREEN.

### Task 3: Add settings controls and opening calls

**Files:**
- Modify: `game/screens.rpy`
- Modify: `game/opening_sequence.rpy`

- [ ] Add selected CRT and hue filter toggles under display settings.
- [ ] Start fullscreen glitch hue in opening scene 05.
- [ ] Stop hue during scene 13 cleanup.
- [ ] Run focused tests and verify GREEN.

### Task 4: Verify, sync, and commit

- [ ] Run the complete unittest suite.
- [ ] Run Ren'Py compile and lint.
- [ ] Stage only feature-related hunks in dirty shared files.
- [ ] Commit from `E:\Re-Memorial`.
- [ ] Push `main`; preserve the local commit if the network is unavailable.
