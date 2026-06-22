# CRT Scanline Clarity Design

- Increase generated scanline thickness from 2 to 4 pixels.
- Increase the repeating period from 4 to 8 pixels, preserving an equal 4-pixel line and 4-pixel clear gap.
- Increase the vertical scroll duration from 6 seconds to 18 seconds, reducing movement speed to one third.
- Keep all CRT opacity and mode hierarchy values unchanged.
- Regenerate the 1920×2160 scanline texture and verify through contracts, Ren'Py compile, and lint.
