# RM Numeric Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first-stage backend for Re: Memorial's numeric system without formal UI or formal schedule content.

**Architecture:** Put deterministic, testable mechanics in `game/systems/rm_core.py`. Add focused `.rpy` modules that expose constants, models, initialization, attributes, energy, dice, Mood/disease, check engine, growth placeholders, fog-card helpers, schedule abstraction, turn settlement, and debug labels.

**Tech Stack:** Ren'Py `.rpy` files with shallow Python, plain Python 3 tests with `unittest`, no external runtime dependencies.

---

### Task 1: Core Tests

**Files:**
- Create: `E:/RenpyProject/ReMemorial/tests/test_rm_core.py`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_core.py`

- [ ] Write tests for initial character generation, attribute values, energy cap, dice enchantments, Mood check modifiers, `CheckResult`, and turn-end settlement.
- [ ] Run `python -m unittest tests.test_rm_core -v` and verify import failures before implementation.

### Task 2: Core Implementation

**Files:**
- Modify: `E:/RenpyProject/ReMemorial/game/systems/rm_core.py`

- [ ] Implement small classes: `RMDice`, `RMCharacterState`, `CheckSpec`, `CheckResult`, `ScheduleSpec`.
- [ ] Implement small rule functions for attributes, energy, dice rolling, Mood/disease probabilities, check execution, mock schedules, and turn-end settlement.
- [ ] Run `python -m unittest tests.test_rm_core -v` and verify the tests pass.

### Task 3: Ren'Py Module Wrappers

**Files:**
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_constants.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_models.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_init.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_attributes.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_energy.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_dice.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_mood_disease.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_check_engine.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_growth.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_fog_cards.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_schedule_core.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_turn_engine.rpy`
- Create: `E:/RenpyProject/ReMemorial/game/systems/rm_debug.rpy`

- [ ] Expose store-level helper functions with concise comments.
- [ ] Add manual debug labels for character creation, mock check, Mood check, and turn-end settlement.

### Task 4: Verification

**Files:**
- All created files above.

- [ ] Run `python -m unittest tests.test_rm_core -v`.
- [ ] Run a Python compile pass over `game/systems/rm_core.py`.
- [ ] If a Ren'Py executable is discoverable, run lint; otherwise report that Ren'Py lint could not be run in this environment.
