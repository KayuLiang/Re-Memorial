# CRT Scanline Clarity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make CRT scanlines clearer by doubling their scale and reducing movement speed to one third.

**Architecture:** Keep the existing generated texture and ATL scroll design. Change only the generator constants and the shared scroll duration, then regenerate the deliverable PNG.

**Tech Stack:** Ren'Py ATL, Python PNG generator, Python unittest contracts.

---

### Task 1: Add failing contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [x] Require `SCANLINE_SPACING = 8` and `SCANLINE_THICKNESS = 4`.
- [x] Require `crt_scroll_speed = 18.0` and `crt_scanline_scroll(speed=18.0)`.
- [x] Run focused tests and verify failure.

### Task 2: Implement and regenerate

**Files:**
- Modify: `game/crt_effect.rpy`
- Modify: `tools/generate_crt_assets.py`
- Regenerate: `game/images/effects/crt_scanlines.png`

- [x] Set the approved constants.
- [x] Regenerate the scanline texture.
- [x] Run focused tests and verify success.

### Task 3: Verify and sync

- [x] Run all opening tests: 104 tests passed.
- [x] Run Ren'Py compile and lint: both exited with code 0.
- [x] Sync source, tests, specification, plan, and regenerated texture to `E:\Re-Memorial`.
