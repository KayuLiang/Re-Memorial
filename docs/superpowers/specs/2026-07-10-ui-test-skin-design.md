# UI Test Skin Design

Date: 2026-07-10

## Goal

Add a UI-test-only skin preview for the new hand-drawn UI assets. The preview lets the project test the new dialogue, HUD, and dice-check surfaces without replacing the formal story UI.

## Confirmed Scope

The new skin applies only inside the `UI测试` flow. It must not change the formal `say` screen, the formal story HUD, or default Ren'Py window styles.

Included test surfaces:

- Dialogue UI: paper dialogue area, character photo/avatar module, name tape, and text placement.
- HUD UI: clock face, clock hand, and the mood value bar that looks like a thermometer.
- Dice-check UI: dice selection panel, check stage, dice list/cards, roll animation screen, and result screen.

Not included:

- Global replacement of the production dialogue UI.
- Global replacement of the production top status HUD.
- New gameplay meaning for body temperature or energy. The thermometer-like bar is the existing mood value display.
- Reward-card redesign beyond what is needed by dice-check UI tests.

## Asset Handling

Source assets are in `C:/Users/19512/Desktop/UI素材/` and have non-transparent backgrounds. The implementation will copy only the selected assets into a project-owned UI-test asset folder before processing.

The first cutout pass should use local image processing:

- Detect near-white background and convert it to alpha.
- Preserve paper edge shadows and hand-drawn outlines.
- Keep output PNGs transparent and stable for Ren'Py.
- Reprocess individual assets manually if automatic cutout damages the edge.

Expected source mapping:

- `对话框组件/新_照片与头像.png`: character photo/avatar module.
- `对话框组件/新_背景纸张.png` or `通用UI组件/任何横着的界面.png`: dialogue paper area.
- `通用UI组件/任何标题.png` or paper-strip material: name tape/title strip.
- `功能UI组件/新_钟表.png`: clock face.
- `功能UI组件/新_钟表指针.png`: clock hand.
- `功能UI组件/新_状态栏.png`, `新_状态栏标签（宽）.png`, `新_状态栏标签（窄）.png`, and `新_游标.png`: mood thermometer bar.
- `骰子选择组件/骰子选择界面底图.png`: dice-check main panel.
- `骰子选择组件/检定区域底图.png`: check stage.
- `骰子选择组件/选择列表底图.png`: dice list area.
- `骰子组件/空白骰卡.png` and dice icon/card references: dice cards.

## Architecture

Create a UI-test skin layer instead of modifying production screens in place.

Planned pieces:

- A project asset directory for processed UI-test PNGs.
- UI-test-only screens and styles named with an `rm_ui_test_` prefix.
- A UI-test dialogue preview screen that composes the paper text area, photo/avatar module, name tape, and sample text.
- A UI-test HUD preview that displays the clock and mood thermometer bar using current test mood/time values.
- Dice-check test screens or style branches that can be enabled only while inside the UI-test flow.

The implementation should prefer new screens/styles over conditional changes to production screens. If an existing dice-check screen must be reused for behavior, the skin selection must be gated by an explicit UI-test flag and remain inactive in formal story flow.

## Data Flow

The UI-test HUD reads existing test values:

- `current_time_minutes` for clock-hand rotation.
- `rm_status_mood_value()` for the mood thermometer position.

The dice-check test continues to use the existing UI-test schedule/check flow. Skin changes should not alter check rules, dice selection rules, random results, or reward application logic.

The dialogue preview can use fixed sample content and a sample character/photo placeholder. It should verify layout and text fit rather than introduce new story canon.

## User Flow

From the main menu:

1. Select `UI测试`.
2. Choose a test target.
3. Dialogue UI preview shows the new dialogue/photo composition.
4. HUD preview shows the clock and mood thermometer bar.
5. Dice-check test starts from schedule selection and enters the skinned dice-check flow.

The existing `检定界面` option should remain the path for testing the full dice-check interaction.

## Testing

Automated tests should cover the non-visual contract:

- Processed UI-test asset paths exist.
- UI-test screens/styles are registered or referenced from the expected files.
- Production `say`, `top_status`, and default styles are not switched to the UI-test assets.
- Dice-check gameplay code paths remain unchanged by the skin.

Manual verification:

- Run Python tests.
- Run Ren'Py lint.
- Open the UI-test flow and verify the dialogue preview, HUD preview, and dice-check flow render without missing images or text overflow.

## Risks

- White-background cutout may remove pale paper texture or leave halos. Mitigation: tune threshold per asset and inspect representative output.
- Large hand-drawn assets may need scaling/cropping to avoid blurry or oversized UI. Mitigation: keep processed source resolution high and scale in Ren'Py transforms.
- Dice-check screens are behavior-heavy. Mitigation: keep logic untouched and isolate skin changes to screen/style layers.

## Acceptance Criteria

- The UI-test menu can show the new dialogue UI with character photo/avatar module.
- The UI-test menu can show the clock plus mood thermometer bar, with the mood indicator driven by current mood.
- The existing UI-test dice-check flow uses the new skinned surfaces.
- Formal story dialogue and formal story HUD remain visually unchanged.
- Automated tests and Ren'Py lint pass.
