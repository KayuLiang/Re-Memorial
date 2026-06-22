# Opening Dimming, CRT, and Paced Audio Design

## Scope

Adjust only the custom opening sequence. Do not alter the later mountain story UI.

## Visual treatment

- Apply a uniform RGB multiplier of 70% to the complete medical-system desktop, including backgrounds, borders, icons, and white text.
- Keep the CRT overlay outside that dimming transform so its strengthened scanlines and noise remain visible.
- Set subtle CRT opacity to `scanline = 0.40` and `noise = 0.30`.
- Preserve clear mode hierarchy by setting interference above subtle and shutdown above interference, without exceeding alpha `1.0`.
- Double scanline thickness from one generated pixel row to two pixel rows while keeping the existing four-pixel spacing.

## Sound-description pacing

- Scene06 and Scene09 retain their current cumulative `lines` lists.
- Each sound-description line is appended and displayed in its existing order.
- Replace timed pauses after each displayed line with untimed player-dismiss pauses.
- Each click advances to and appends the next line; prior lines remain visible.
- Existing sound playback calls remain paired with their matching text.

## Verification

- Contract tests require the 70% desktop tint, exact subtle CRT values, increasing mode hierarchy, two-pixel scanline generation, and click-driven cumulative sound lines.
- Regenerate CRT assets.
- Run all opening tests, Ren'Py compile, and Ren'Py lint.
