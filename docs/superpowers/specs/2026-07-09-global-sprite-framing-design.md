# Global Sprite Framing Design

## Goal

Adjust the global character sprite scale and vertical framing to match the provided reference: a mid-shot composition where roughly the lower 35% of the full standing figure is cropped below the screen, leaving the visible body as the dominant character presence.

The implementation should affect existing story scenes globally without rewriting individual `show` statements.

## Reference Interpretation

The approved interpretation is option A from the visual comparison: reference-style cropping.

- Treat the sprite as a standing full-body figure.
- Anchor the figure below the bottom of the 1920x1080 stage so the lower-leg area is outside the frame.
- Keep the visible figure as a mid-shot, not a distant full-body shot.
- Preserve the current left/right composition pattern unless a later scene needs a specific override.

This does not mean the visible sprite height should be exactly one third of the screen. It means the visible portion should read like the reference image: knees and lower legs cropped while the upper body remains large enough to carry the scene.

## Current State

Sprite placement is centralized in `game/images.rpy`:

- `fro_left`
- `fro_underwear_left`
- `fro_casual_left`
- `ami_casual_right`
- `pal_casual_right`

Most story files use these transforms directly:

- `show fro hospital_pajamas default at fro_left`
- `show fro underwear default at fro_underwear_left`
- `show fro casual default at fro_casual_left`
- `show ami casual default at ami_casual_right`
- `show pal casual default at pal_casual_right`

Fro and Ami source sprites use 2160x3840 canvases. Their non-transparent figure bounds are approximately:

- Fro: about 3340px tall within the canvas.
- Ami: about 2850px tall within the canvas.

The current Fro/Ami transforms use `zoom 0.351` and `yoffset 350`, which makes the sprites smaller and heavily lowered. The adjustment should replace those values with a consistent mid-shot rule.

## Architecture

Use the existing transform names as the global control points. Do not introduce new show labels or rewrite story scene files.

Planned implementation file:

- `game/images.rpy`

No story files should need edits for this change.

## Framing Rule

For official 2160x3840 sprites, the transform should:

- align to the bottom of the stage with `yalign 1.0`;
- use a larger zoom than the current `0.351` so the visible body reads as a mid-shot;
- use a positive `yoffset` to place the lower body below the bottom edge;
- apply the same scale and vertical rule to Fro and Ami so they feel like they occupy the same scene space.

Initial target for implementation planning:

- Fro/Ami transforms should use one shared value set, with roughly `zoom 0.46` and `yoffset 440` as the first candidate.
- This candidate places a 3840px canvas at about 1766px rendered height and pushes about 440px below the 1080px frame, creating a strong lower-body crop while keeping the upper figure large.
- Exact values may be adjusted during implementation if screenshot verification shows the crop is too high or too low.

For `pal_casual_right`, preserve its placeholder nature. It is a 420x760 composite rather than a 2160x3840 official sprite, so it should be adjusted visually to match the same mid-shot intent without pretending it has the same source dimensions.

## Scope

In scope:

- Global placement transforms in `game/images.rpy`.
- Static tests that guard the chosen transform values and prevent story-wide rewrites.
- Screenshot or lint verification if practical.

Out of scope:

- Cropping or editing PNG source assets.
- Replacing Pal's placeholder art.
- Per-scene composition tweaks.
- Changing dialogue UI, HUD, or background framing.

## Testing

Automated tests should verify:

- the relevant transforms still exist in `game/images.rpy`;
- Fro and Ami transforms use the approved shared zoom and vertical offset;
- story files continue to use the transform names rather than hard-coded per-scene positions.

Manual or engine verification should include:

- Run Python tests.
- Run Ren'Py lint.
- Launch or screenshot at least one scene with Fro alone and one scene with Fro/Ami together if practical.

## Backup

After implementation and verification, sync the changed source and tests to `E:\Re-Memorial`, excluding cache, saves, compiled files, logs, errors, and traceback files. Commit only the files related to this change from `E:\Re-Memorial`.
