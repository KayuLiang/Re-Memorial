# Global Sprite Framing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adjust global character sprite transforms so existing scenes use a reference-style mid-shot crop without editing individual story `show` statements.

**Architecture:** Keep the existing transform names in `game/images.rpy` as the global control points. Add static tests that lock the approved transform values and verify story files still use named transforms instead of per-scene hard-coded sprite placement.

**Tech Stack:** Ren'Py transforms in `.rpy`, Python `unittest` static source tests, Ren'Py lint.

---

## File Structure

- Create `E:\RenpyProject\ReMemorial\tests\test_global_sprite_framing.py`: focused static tests for sprite transform values and story transform usage.
- Modify `E:\RenpyProject\ReMemorial\game\images.rpy`: update only the existing sprite transforms.
- Sync changed files and this plan to `E:\Re-Memorial` after verification.

## Framing Values

Use these implementation values:

- Official 2160x3840 Fro/Ami sprites: `zoom 0.42`, `yoffset 600`.
- Pal placeholder composite: `zoom 1.85`, `yoffset 490`.
- Keep existing horizontal anchors: Fro left `xalign 0.08`, Ami/Pal right `xalign 0.92`.
- Keep `yalign 1.0` for all sprite transforms.

These values are based on the measured non-transparent sprite bounds. Fro's figure bounds are roughly 3340px tall, and `zoom 0.42` makes the figure about 1400px tall. With `yoffset 600`, the lower body is pushed below the 1080px stage by about 35% of the rendered figure height while keeping the head visible.

## Task 1: Add Failing Sprite Framing Tests

**Files:**
- Create: `E:\RenpyProject\ReMemorial\tests\test_global_sprite_framing.py`
- Test: `E:\RenpyProject\ReMemorial\tests\test_global_sprite_framing.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_global_sprite_framing.py` with:

```python
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = PROJECT_ROOT / "game"
IMAGES_PATH = GAME_DIR / "images.rpy"
STORY_DIR = GAME_DIR / "story"


def block_with_header(source, stripped_header):
    lines = source.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != stripped_header:
            continue

        indent = len(line) - len(line.lstrip(" "))
        block = [line]
        for nested in lines[index + 1:]:
            if nested.strip():
                nested_indent = len(nested) - len(nested.lstrip(" "))
                if nested_indent <= indent:
                    break
            block.append(nested)
        return "\n".join(block)

    raise AssertionError(f"{stripped_header!r} not found")


class GlobalSpriteFramingTests(unittest.TestCase):
    def test_official_sprites_use_shared_reference_midshot_framing(self):
        source = IMAGES_PATH.read_text(encoding="utf-8")

        for transform_name in (
            "fro_left",
            "fro_underwear_left",
            "fro_casual_left",
            "ami_casual_right",
        ):
            with self.subTest(transform_name=transform_name):
                block = block_with_header(source, f"transform {transform_name}:")
                self.assertIn("yalign 1.0", block)
                self.assertIn("yoffset 600", block)
                self.assertIn("zoom 0.42", block)

        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_left:"))
        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_underwear_left:"))
        self.assertIn("xalign 0.08", block_with_header(source, "transform fro_casual_left:"))
        self.assertIn("xalign 0.92", block_with_header(source, "transform ami_casual_right:"))

    def test_pal_placeholder_uses_matching_midshot_intent(self):
        source = IMAGES_PATH.read_text(encoding="utf-8")
        block = block_with_header(source, "transform pal_casual_right:")

        self.assertIn("xalign 0.92", block)
        self.assertIn("yalign 1.0", block)
        self.assertIn("yoffset 490", block)
        self.assertIn("zoom 1.85", block)

    def test_story_scenes_continue_to_use_named_sprite_transforms(self):
        story_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in STORY_DIR.glob("*.rpy")
        )

        for show_line in (
            "show fro hospital_pajamas default at fro_left",
            "show fro underwear default at fro_underwear_left",
            "show fro casual default at fro_casual_left",
            "show ami casual default at ami_casual_right",
            "show pal casual default at pal_casual_right",
        ):
            with self.subTest(show_line=show_line):
                self.assertIn(show_line, story_source)

        self.assertNotIn("show fro hospital_pajamas default xpos", story_source)
        self.assertNotIn("show fro casual default xpos", story_source)
        self.assertNotIn("show ami casual default xpos", story_source)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
py -3.10 -m unittest -v tests.test_global_sprite_framing
```

Expected: FAIL because current official sprite transforms still use `zoom 0.351` and `yoffset 350`, and Pal still uses `zoom 1.3` and `yoffset 180`.

## Task 2: Update Global Sprite Transforms

**Files:**
- Modify: `E:\RenpyProject\ReMemorial\game\images.rpy`
- Test: `E:\RenpyProject\ReMemorial\tests\test_global_sprite_framing.py`

- [ ] **Step 1: Update official sprite transforms**

In `game/images.rpy`, update `fro_left`, `fro_underwear_left`, `fro_casual_left`, and `ami_casual_right` to:

```renpy
transform fro_left:
    xalign 0.08
    yalign 1.0
    yoffset 600
    zoom 0.42

transform fro_underwear_left:
    xalign 0.08
    yalign 1.0
    yoffset 600
    zoom 0.42

transform fro_casual_left:
    xalign 0.08
    yalign 1.0
    yoffset 600
    zoom 0.42

transform ami_casual_right:
    xalign 0.92
    yalign 1.0
    yoffset 600
    zoom 0.42
```

- [ ] **Step 2: Update Pal placeholder transform**

In `game/images.rpy`, update `pal_casual_right` to:

```renpy
transform pal_casual_right:
    xalign 0.92
    yalign 1.0
    yoffset 490
    zoom 1.85
```

- [ ] **Step 3: Run the focused test to verify it passes**

Run:

```powershell
py -3.10 -m unittest -v tests.test_global_sprite_framing
```

Expected: PASS.

## Task 3: Verify, Sync, and Commit

**Files:**
- Sync: `E:\RenpyProject\ReMemorial\game\images.rpy`
- Sync: `E:\RenpyProject\ReMemorial\tests\test_global_sprite_framing.py`
- Sync: `E:\RenpyProject\ReMemorial\docs\superpowers\plans\2026-07-09-global-sprite-framing.md`

- [ ] **Step 1: Run all Python tests**

Run:

```powershell
py -3.10 -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run Ren'Py lint**

Run:

```powershell
& 'E:\renpy-8.5.3-sdk\renpy.exe' 'E:\RenpyProject\ReMemorial' lint
```

Expected: exit code 0.

- [ ] **Step 3: Sync changed files to backup repository**

Copy only these files to `E:\Re-Memorial`:

```text
game/images.rpy
tests/test_global_sprite_framing.py
docs/superpowers/plans/2026-07-09-global-sprite-framing.md
```

- [ ] **Step 4: Commit from backup repository**

Run:

```powershell
git -C E:\Re-Memorial add -- game/images.rpy tests/test_global_sprite_framing.py docs/superpowers/plans/2026-07-09-global-sprite-framing.md
git -C E:\Re-Memorial commit -m "feat: adjust global sprite framing"
```

Expected: one commit containing only the transform update, focused tests, and implementation plan.

## Self-Review

- Spec coverage: global transform-only implementation, reference-style crop, Fro/Ami shared values, Pal placeholder adjustment, no story rewrites, tests, lint, and backup rules are covered.
- Placeholder scan: no TBD/TODO/fill-in-later instructions remain.
- Type consistency: transform names match `game/images.rpy` and story `show` lines.
