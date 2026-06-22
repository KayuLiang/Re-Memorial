# Story File Organization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the existing playable narrative into four numbered `game/story/` files while preserving behavior.

**Architecture:** Keep only shared declarations and the entry point in `game/script.rpy`. Give each numbered segment a stable entry label and connect segments with explicit jumps so Ren'Py source-file ordering cannot affect play order.

**Tech Stack:** Ren'Py script language, Python `unittest`

---

### Task 1: Add Story Layout Contracts

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\tools\test_opening_contracts.py`

- [ ] Add `STORY_DIR`, expected file paths, and a `StoryFileOrganizationContractTests` class.
- [ ] Require `0-1-0.rpy`, `1-1-1.rpy`, `1-1-2.rpy`, and `1-1-3.rpy`.
- [ ] Require stable entry labels, explicit jumps, timestamp ownership, and a minimal `script.rpy`.
- [ ] Run `py -m unittest tools.test_opening_contracts.StoryFileOrganizationContractTests -v`.
- [ ] Verify RED because `game/story/` does not exist.

### Task 2: Split the Story Files

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\game\script.rpy`
- Delete: `E:\RenpyProject\ReMemorial\game\opening_sequence.rpy`
- Create: `E:\RenpyProject\ReMemorial\game\story\0-1-0.rpy`
- Create: `E:\RenpyProject\ReMemorial\game\story\1-1-1.rpy`
- Create: `E:\RenpyProject\ReMemorial\game\story\1-1-2.rpy`
- Create: `E:\RenpyProject\ReMemorial\game\story\1-1-3.rpy`

- [ ] Move all opening labels into `0-1-0.rpy` and make `start` jump to `story_0_1_0`.
- [ ] Move the mountain dream into `1-1-1.rpy`, retaining `mountain_memory_start` as an alias.
- [ ] Move the 13:30 hospital segment into `1-1-2.rpy`.
- [ ] Move the scene reset, 15:30 timestamp, and apartment sequence into `1-1-3.rpy`.
- [ ] Add explicit jumps between all four segments.
- [ ] Run the focused story layout contracts and verify GREEN.

### Task 3: Update Existing Contracts

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\tools\test_opening_contracts.py`

- [ ] Point opening-sequence checks to `game/story/0-1-0.rpy`.
- [ ] Point mountain handoff checks to `game/story/1-1-1.rpy`.
- [ ] Run `py -m unittest discover -s tools -p "test_*.py" -v`.
- [ ] Fix only path and label assumptions caused by the file split.

### Task 4: Verify and Back Up

**Files:**
- Sync the changed story, test, spec, and plan files to `E:\Re-Memorial`.

- [ ] Run `E:\renpy-8.5.3-sdk\renpy.exe E:\RenpyProject\ReMemorial lint`.
- [ ] Confirm no story text was added, removed, or reordered across the moved ranges.
- [ ] Sync source files while excluding generated artifacts.
- [ ] Re-run all tests and lint against `E:\Re-Memorial`.
- [ ] Commit locally from `E:\Re-Memorial` without pushing or tagging.

