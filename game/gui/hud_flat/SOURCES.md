# HUD icon sources

Retrieved 2026-09-19. Library icons are adapted to one shared HUD treatment.

- Phosphor Icons, fill weight: pill, device-mobile, backpack, dice-five,
  user-square, heart, star, lightning, play, clock-counter-clockwise.
  https://github.com/phosphor-icons/core/tree/main/assets/fill
  MIT, copyright (c) 2023 Phosphor Icons. Full license: source/PHOSPHOR-LICENSE.txt.
- Dialogue controls, Phosphor Icons regular weight: article, eye-slash,
  arrows-clockwise, fast-forward, sliders-horizontal. Same MIT license; retained
  under source/. Restored as clean placeholders pending user-supplied artwork.
  https://github.com/phosphor-icons/core/tree/main/assets/regular
- The custom pencil centerlines/roughening were rejected and removed. The user
  will make the hand-drawn treatment with PS effects/plugins/brushes. Do not
  recreate this effect procedurally. Keep the shared 48px icon grid.
  Long 72x88px tab stems are drawn behind the paper, with 24px native hover travel.
  Ren'Py supplies the Chinese hover/accessibility labels.
- Previous neuron source (retained, no longer displayed): Fabian Mikulasch,
  Pyramidal Neuron, Bioicons CC0 collection.
  https://github.com/duerrsimon/bioicons/blob/main/static/icons/cc-0/Human_physiology/Fabian-Mikulasch/Pyramidal_Neuron.svg
  https://creativecommons.org/publicdomain/zero/1.0/

Original SVGs and the MIT license are retained under source/. Navigation icons
share ivory fill, dark contour, size and baseline; the lightning is joined to
the energy track. Heart and star appear in unfilled reserved life/magic circles.

The current neuron is custom vector geometry following the user-supplied HUD
reference: ivory soma, short rounded branches and a blue nucleus. On 2026-09-19
the user explicitly permitted redrawing assets when library silhouettes differ
too much, and required style consistency even when using library assets.
Clock segments, meter tracks and the two-tone diamond are custom UI geometry.

Notebook page, functional paper tabs, photo mount and paperclip
are custom flat vector geometry based on the user's reference and Fro's notebook.
The photo mount is a labelled placeholder, not a crop of a standing sprite.
The user will supply the separate portrait illustrations; no portrait art is
generated here. Current mount has a -3 degree layout tilt which can be removed
if the supplied artwork already includes its own angle and paper treatment.
The user rejected the side spiral binding; it has been removed. The current
revision uses the user's selected SEASON paper layers and Dordogne functional
tabs as visual references, not copied game assets. See DIALOGUE_DESIGN.md for
the grid, restrained wear placement, pencil treatment and design rationale.
