# UI Test Menu Design

## Goal

Add a main menu entry for testing UI surfaces with the new UI assets. The entry opens a small test selector asking:

`接下来要测试什么呢？`

The selector offers:

- `检定界面`: start from schedule selection and continue into an interactive check through the existing test schedule flow.
- `奖励选择`: directly trigger one pending growth reward selection and resolve it through the existing reward card flow.

## User-Facing Flow

The title menu keeps the existing `开始游戏` and `开始测试` entries. A new `UI测试` entry appears alongside them.

Selecting `UI测试` starts a dedicated label, `rm_ui_test_menu`, instead of entering story content. That label shows the two-option Ren'Py menu and routes to the chosen test flow.

For `检定界面`, the flow initializes the same test character/state as `rm_test_flow_start`, then jumps into `rm_test_flow_loop`. The first interactive UI is `rm_test_schedule_select`, so the user can choose a schedule and then exercise the dice check screens.

For `奖励选择`, the flow initializes the test character/state, grants one pending growth reward to a known attribute, calls `rm_test_resolve_pending_cards`, shows the result text, and then returns to `rm_ui_test_menu` so another UI can be tested without restarting the game.

## Architecture

Reuse the current test system instead of adding a parallel UI test framework.

Planned code locations:

- `game/screens.rpy`: add one main-menu navigation button with `Start("rm_ui_test_menu")`.
- `game/story/9-9-9-test-flow.rpy`: add `rm_ui_test_menu` and a direct reward-test label near the existing test flow labels.
- `game/systems/rm_test_schedules.rpy`: add a small helper that prepares one pending growth reward for the reward-selection path if the current helpers do not already expose a direct setup function.

The new helper should reuse `rm_test_start_flow()` and `rm_core.add_growth_reward_pending(...)` rather than mutating dice or reward cards manually.

## Data Flow

`UI测试` starts a fresh test state. Both branches use the same temporary test character created by `rm_test_start_flow()`, so they do not depend on save data or story progress.

The check branch uses the existing schedule and attribute check data path:

`rm_test_schedule_select` -> `rm_test_schedule_check_flow` -> `attribute_dice_select` -> `attribute_check_roll_animation` -> `attribute_check_result`

The reward branch uses the existing pending card data path:

`rm_test_prepare_growth_reward_test` -> `rm_test_pending_card_request` -> `rm_test_pending_card_choice` -> optional die/face selection screens -> `rm_test_apply_pending_card`

## Error Handling

The direct reward branch must create a pending reward before calling `rm_test_resolve_pending_cards`. If no pending request exists after setup, it should display a short diagnostic line and return to the UI test menu rather than falling through silently.

The menu includes a `返回标题菜单` option so testers can leave the loop cleanly.

## Testing

Automated coverage should focus on any new pure helper in `rm_test_schedules.rpy`, if practical in the existing test harness.

Manual verification should include:

- Launch from the main menu and confirm `UI测试` appears.
- Select `检定界面` and confirm the first UI is schedule selection.
- Choose a check schedule and confirm dice selection, roll animation, and result screens appear.
- Relaunch `UI测试`, select `奖励选择`, and confirm reward card selection appears immediately.
- Run Ren'Py lint before considering the implementation complete.
