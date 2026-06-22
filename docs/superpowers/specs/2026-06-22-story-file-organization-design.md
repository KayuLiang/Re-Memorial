# Story File Organization Design

## Goal

Move playable narrative out of `game/script.rpy` and
`game/opening_sequence.rpy` into numbered files under `game/story/` without
changing story text, choices, state changes, screen calls, or play order.

## File Layout

- `game/script.rpy`: shared characters, global defaults, and `label start`.
- `game/story/0-1-0.rpy`: complete opening medical-system sequence.
- `game/story/1-1-1.rpy`: mountain-god dream.
- `game/story/1-1-2.rpy`: hospital and discharge sequence beginning with the
  `20XX年8月18日 星期一 下午 13:30` timestamp.
- `game/story/1-1-3.rpy`: trip home and apartment sequence beginning with the
  `20XX年8月18日 星期一 下午 15：30` timestamp.

## Entry Labels and Flow

Use stable labels matching the story identifiers:

```renpy
label story_0_1_0:
label story_1_1_1:
label story_1_1_2:
label story_1_1_3:
```

`label start` jumps to `story_0_1_0`. Each file explicitly jumps to the next
story segment. The existing `mountain_memory_start` label remains as a
compatibility alias that jumps to `story_1_1_1`.

Internal opening labels remain in `0-1-0.rpy`. The final opening scene jumps to
`story_1_1_1`.

## Segment Boundaries

The mountain dream ends immediately before the 13:30 timestamp. The hospital
segment ends after `RECOVERY.`. The scene reset and character setup preceding
the 15:30 timestamp move into `1-1-3.rpy`, so the first displayed line of that
segment remains its timestamp.

## Verification

Contract tests require the four files, their labels, explicit jumps, and a
minimal `script.rpy`. They also ensure the three known segment-opening lines
remain in their assigned files. The complete Python test suite and Ren'Py lint
must pass before the Git backup commit.

