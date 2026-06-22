# Opening Dimming, CRT, and Paced Audio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dim the medical opening UI by 30%, strengthen CRT presentation, and make sound descriptions advance one cumulative line per click.

**Architecture:** Apply one tint transform at the medical desktop root so all child colors, including white text, are reduced consistently. Strengthen CRT through mode settings and the existing generated scanline texture. Preserve the cumulative overlay data flow while replacing timed waits with dismiss waits.

**Tech Stack:** Ren'Py screen language, ATL matrix color, Python PNG generator, Python unittest contracts.

---

### Task 1: Add visual regression contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [x] Add a contract requiring `TintMatrix("#b3b3b3")` on the root medical desktop frame.
- [x] Add contracts requiring subtle scanline `0.40`, subtle noise `0.30`, strict mode hierarchy, and `SCANLINE_THICKNESS = 2`.
- [x] Run the focused tests and verify they fail against current code.

### Task 2: Implement dimming and CRT strengthening

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Modify: `game/crt_effect.rpy`
- Modify: `tools/generate_crt_assets.py`
- Regenerate: `game/images/effects/crt_scanlines.png`

- [x] Add `opening_ui_dimmed` with `matrixcolor TintMatrix("#b3b3b3")` and apply it to the desktop root.
- [x] Set subtle to `0.40/0.30`, interference to `0.62/0.50`, and shutdown to `0.82/0.80`.
- [x] Generate two scanline rows per four-row period.
- [x] Regenerate assets and run focused visual contracts.

### Task 3: Add click-pacing regression contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [x] Require Scene06 and Scene09 to retain ordered cumulative appends and use one bare `pause` after each displayed line.
- [x] Reject timed pauses inside the cumulative sound-description sections.
- [x] Run focused tests and verify they fail against current code.

### Task 4: Implement click-paced descriptions

**Files:**
- Modify: `game/opening_sequence.rpy`

- [x] Replace the three timed Scene06 pauses and four timed Scene09 pauses with bare `pause` statements.
- [x] Run focused tests and verify they pass.

### Task 5: Full verification and backup sync

**Files:**
- Sync changed source, tests, generated CRT texture, spec, and plan to `E:\Re-Memorial`.

- [x] Run `py -m unittest discover -s tools -p 'test_opening_*.py' -v`: 103 tests passed.
- [x] Run Ren'Py compile: exit code 0.
- [x] Run Ren'Py lint: exit code 0.
- [x] Sync only source and deliverable assets, excluding caches, logs, compiled files, errors, saves, and tracebacks.
