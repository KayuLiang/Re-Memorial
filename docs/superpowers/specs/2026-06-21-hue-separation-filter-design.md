# Hue Separation Filter Design

## Goal

Add a reusable chromatic hue-separation filter for later story scenes. The default look is a restrained red/cyan edge separation that remains readable during sustained use.

## Public Story API

```renpy
$ hue_separation_start("steady", scope="scene")
$ hue_separation_start("glitch", scope="fullscreen")
$ hue_separation_stop()
```

- `mode` accepts `"steady"` or `"glitch"`.
- `scope` accepts `"scene"` or `"fullscreen"`.
- Calling `hue_separation_start` again replaces the active mode and scope instead of stacking another controller.
- Calling `hue_separation_stop` when the filter is already inactive is safe.
- Invalid mode or scope values log a warning and fall back to `"steady"` and `"scene"` so a story typo cannot leave duplicate cameras or screens active.

## Visual Modes

### Steady

- Apply a constant 3-pixel horizontal red/cyan channel offset at the project's 1920-pixel reference width, scaled with the rendered texture size.
- Keep the displacement subtle enough for dialogue-length use.
- Do not add slicing, scanlines, noise, or camera shake; those remain separate effects.

### Glitch

- Keep the same subtle baseline separation as `steady`.
- After each peak ends, wait a random 6–12 seconds before the next peak begins.
- Each peak lasts a random 0.1–0.5 seconds.
- Randomize peak displacement from 8–18 reference pixels so successive flashes do not look mechanically identical.
- Switch abruptly to the peak strength, hold it for the randomized duration, then return abruptly to the 3-pixel baseline.
- Use Ren'Py rollback-safe random generation for visible timing and strength choices.

## Scope and Layer Behavior

### Scene Scope

- Apply the shader camera to the `master` layer only.
- Backgrounds, character sprites, and other story displayables receive the effect.
- Dialogue text, choice screens, and UI on the `screens` layer remain clear.

### Fullscreen Scope

- Apply equivalent shader cameras to both `master` and `screens`.
- Story art and UI receive the same current separation strength.
- Keep one shared controller state so both layers peak and recover at the same time.

The filter must not move displayables between layers or change their z-order. Existing CRT screens and story screens remain independently callable.

## Architecture

Create `game/hue_separation_effect.rpy` containing:

1. A custom Ren'Py model-based GLSL shader that samples the current layer texture with small red and cyan horizontal UV offsets while retaining the green/base channel.
2. Camera transforms for the `master` and `screens` layers that pass the current displacement uniform to the shader.
3. Small store-level start/stop helpers that validate arguments and own the active mode, scope, and strength.
4. One non-modal controller screen for glitch scheduling. It updates the shared strength, waits randomized intervals, runs randomized peaks, and reschedules itself while glitch mode remains active.

`steady` mode does not run the random peak loop. `glitch` mode owns exactly one loop regardless of scope.

## State and Cleanup

- Keep runtime state non-persistent; saves record the current store values normally, but no `persistent` data is added.
- Stopping resets strength to zero, hides the controller screen, and clears the shader cameras from every layer the filter may have touched.
- Switching from `fullscreen` to `scene` explicitly clears the `screens` camera.
- Switching from `glitch` to `steady` hides the glitch controller before applying steady strength.
- The implementation must leave no timers or peak state running after stop.

## Testing and Verification

Add focused contract tests before implementation to require:

- The public start/stop helpers and accepted mode/scope values.
- The custom shader and both layer camera transforms.
- Scene scope targeting only `master`.
- Fullscreen scope targeting both `master` and `screens`.
- Random wait bounds of 6–12 seconds.
- Random peak-duration bounds of 0.1–0.5 seconds.
- Baseline displacement of 3 reference pixels and peak displacement of 8–18 reference pixels.
- Replacement rather than stacking on repeated start calls.
- Complete cleanup on stop and scope changes.

Then run:

1. Focused contract tests.
2. The complete project contract suite.
3. Ren'Py compile.
4. Ren'Py lint.

Manual verification should exercise steady and glitch modes in both scopes, confirm synchronized fullscreen peaks, verify readable scene-scope UI, and confirm compatibility with the existing CRT overlay.
