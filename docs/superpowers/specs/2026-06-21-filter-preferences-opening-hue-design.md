# Filter Preferences and Opening Hue Design

## Goal

Add persistent display preferences for CRT and hue-separation effects, and enable fullscreen glitch hue separation during the opening medical-system sequence.

## Preference Behavior

- Add two global persistent preferences:
  - `persistent.crt_effect_enabled`
  - `persistent.hue_separation_enabled`
- Both default to `True`.
- Both appear in Settings → Display as independent toggle buttons.
- Changes take effect immediately.
- Values persist globally and are not tied to an individual save.
- A disabled preference overrides every story-script request: scripts may continue requesting an effect, but the effect must not render.

## Requested State vs. Rendered State

Keep story intent separate from player display preferences.

### CRT

- The existing `show screen crt_effect(mode=...)` call remains the story-facing API.
- The screen retains its current mode while disabled.
- When CRT is disabled, the screen renders no scanlines, noise, flicker, or jitter.
- Re-enabling CRT immediately reveals the currently requested mode without requiring the story to call it again.

### Hue Separation

- The existing `hue_separation_start(mode, scope)` and `hue_separation_stop()` calls remain the story-facing API.
- `hue_separation_active`, mode, scope, and current request state remain intact while the preference is disabled.
- Disabling hue separation immediately:
  - clears shader cameras from `master` and `screens`;
  - hides the glitch controller;
  - resets any active peak to the baseline request state.
- Re-enabling hue separation while a request is active:
  - restores the requested layer scope;
  - restores steady baseline separation;
  - restarts a glitch request from a newly randomized 6–12 second wait.
- Re-enabling while no request is active does nothing.

## Settings UI

In the existing `screen preferences()` Display section, add:

- `CRT 滤镜`
- `色相差滤镜`

Use Ren'Py-native actions/functions so selecting either button updates the persistent value and applies the runtime change in the same interaction. The selected state must visually reflect whether the preference is enabled.

## Opening Medical-System Integration

- Start hue separation in `opening_scene_05`, when the medical-system desktop first appears:

```renpy
$ hue_separation_start("glitch", scope="fullscreen")
```

- This request remains active throughout the medical desktop, records, consent, identity, and verification flow.
- Stop hue separation in `opening_scene_13` during final medical-system cleanup, before the black countdown handoff:

```renpy
$ hue_separation_stop()
```

- The preference still controls visibility. If hue separation is disabled, these calls update request state without rendering the effect.

## Architecture

### Shared Preference Helpers

Create small helper functions in the relevant effect files:

- CRT preference helper toggles `persistent.crt_effect_enabled` and restarts the interaction.
- Hue preference helper toggles `persistent.hue_separation_enabled`, clears or restores cameras/controller as required, and restarts the interaction.

Keep effect-specific behavior inside each effect file. `screens.rpy` should only present buttons and call the public preference helpers.

### Initialization

Use `default persistent.<name> = True` so existing players without these fields receive enabled defaults.

## Edge Cases

- Repeatedly selecting the same preference value is safe.
- Disabling an already hidden or inactive effect is safe.
- Switching hue modes/scopes while disabled updates the stored request without displaying cameras or starting timers.
- Stopping hue separation while disabled clears the request so re-enabling later does not resurrect it.
- Opening the settings menu must not itself alter the active effect state.

## Testing and Verification

Add contract tests before implementation for:

- Both persistent defaults are `True`.
- Both Display-section controls exist and bind to the correct helper/state.
- CRT emits no visual layers when disabled and restores the requested mode when enabled.
- Hue start preserves request state while disabled.
- Hue disable clears both cameras and hides the controller.
- Hue re-enable restores active steady/glitch requests and reschedules glitch timing.
- Opening scene 05 starts `glitch + fullscreen`.
- Opening scene 13 stops hue separation before the black countdown handoff.

Run:

1. Focused contract tests.
2. Full contract suite.
3. Ren'Py compile.
4. Ren'Py lint.

