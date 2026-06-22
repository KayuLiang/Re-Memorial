# Opening Interaction Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Slow the TAP TO START blink to half speed and make the centered identity inserts dismissible without blocking story progression.

**Architecture:** Keep the blink as the existing ATL transform with doubled transition durations. Move insert timing and dismissal into the modal insert screens, then call those screens from the scene so mouse, keyboard, and automatic timeout all return through one interaction boundary.

**Tech Stack:** Ren'Py screen language and ATL; Python `unittest` source-contract tests.

---

### Task 1: Add regression contracts

**Files:**
- Modify: `tools/test_opening_contracts.py`

- [x] **Step 1: Add a test requiring `opening_prompt_blink` to use two `0.56`-second transitions.**
- [x] **Step 2: Add a test requiring both identity inserts to be called screens with fullscreen mouse, dismiss-key, and `0.8`-second timer return actions.**
- [x] **Step 3: Run the two tests and verify they fail against the current implementation.**

### Task 2: Implement the interaction fixes

**Files:**
- Modify: `game/screens_opening_system.rpy`
- Modify: `game/opening_sequence.rpy`

- [x] **Step 1: Change both `opening_prompt_blink` transitions from `0.28` to `0.56`.**
- [x] **Step 2: Add a fullscreen clear button, dismiss key, and `timer 0.8 action Return()` to both identity insert screens.**
- [x] **Step 3: Replace each `show`/`pause`/`hide` insert sequence with `call screen`.**
- [x] **Step 4: Re-run the two focused tests and verify they pass.**

### Task 3: Verify the opening

**Files:**
- Test: `tools/test_opening_contracts.py`
- Test: `tools/test_opening_stats.py`

- [x] **Step 1: Run all opening tests: 101 tests passed.**
- [x] **Step 2: Run Ren'Py lint: exit code 0.**
