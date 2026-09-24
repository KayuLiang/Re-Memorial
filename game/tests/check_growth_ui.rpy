# Explicit fixtures; never entered by the story. All screenshots use the task temp directory.
init python:
    def rm_check_ui_shot(name, width, height):
        return "E:/ChatGPT/Temp/rememorial-check-dice-upgrade-ui/%dx%d/%s.png" % (width, height, name)

label rm_check_ui_preview:
    $ _autosave = False
    $ opening_active = False
    $ story_hud_hidden = False
    $ story_hud_status_unlocked = True
    $ story_hud_character_panel_unlocked = True
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.energy = 20
    $ rm_player.mood = -70
    $ rm_player.dice_pool = [rm_core.RMDice("ui_str", "str", [1,2,3,4,5,6]), rm_core.RMDice("ui_dex", "dex", [1,2,3,4,5,6]), rm_core.RMDice("ui_extra", "str", [1,2,3,4,5,6]), rm_core.RMDice("ui_sealed", "str", [1,2,3,4], rm_core.ENCHANT_SEAL)]
    scene bg doctor_office
    show fro casual default at fro_casual_left
    call screen attribute_dice_select("str", requirement=6, allowed_stats=("str","dex"), required_die_stats=("str","dex"), thought="逃窜的小偷似乎正打算从我们这节车厢前面的车门逃走。\n我是不是应该做些什么？")
    if _return == "__rm_check_cancel__":
        return
    $ ui_check_ids = _return
    $ ui_check_core = rm_core.perform_check(rm_player, rm_core.CheckSpec("str", 6, ui_check_ids, action_type=rm_core.ACTION_INSTANT, allowed_dice_attributes=("str","dex"), required_dice_attributes=("str","dex")), rng=renpy.random)
    $ ui_check_result = rm_test_result_dict_for_schedule(ui_check_core, rm_player, ui_check_ids, "test_strength_training")
    call screen attribute_check_roll_animation(ui_check_result)
    call screen attribute_check_result(ui_check_result)
    "界面测试已返回当前场景。"
    return

label rm_growth_ui_cards:
    $ _autosave = False
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.growth_reward_pending['str'] = 1
    $ ui_request = dict(mode="growth", attr="str", cards=[dict(type="add_new_die", die_sides=6, face_total=18), dict(type="upgrade_chosen_die_type"), dict(type="increase_chosen_face", increase_amount=2)])
    call screen rm_test_pending_card_choice(ui_request)
    $ ui_reward = _return
    $ ui_reward_result = rm_core.apply_pending_growth_reward(rm_player, 'str', ui_reward, rng=renpy.random)
    "界面测试：奖励已结算。"
    return

label rm_check_ui_wake:
    $ _autosave = False
    $ opening_active = False
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.disease_state = rm_core.DISEASE_DEPRESSION
    $ rm_player.energy = 0
    $ rm_player.dice_pool = [rm_core.RMDice("wake_%d" % i, "pow", list(range(1,21))) for i in range(3)]
    $ ui_wake_limit = rm_core.max_dice_for_check(rm_core.CheckSpec("pow", 10), rm_core.mood_check_profile(rm_core.mood_state(rm_player)))
    call screen attribute_dice_select("pow", max_dice=ui_wake_limit, requirement=10, check_kind="起床", action_type=rm_core.ACTION_WAKE, thought="该起床了。")
    if _return == "__rm_check_cancel__":
        return
    $ ui_check_ids = _return
    $ ui_check_core = rm_core.perform_wake_check(rm_player, 10, ui_check_ids, rng=renpy.random)
    $ ui_check_result = rm_test_result_dict_for_schedule(ui_check_core, rm_player, ui_check_ids, "test_strength_training")
    call screen attribute_check_result(ui_check_result)
    "起床检定已完成。"
    return

testsuite check_growth_ui:
    parameter (ui_width,ui_height) = [(1280,720),(1920,1080),(2560,1440)]
    parameter ui_saved_preferences = [None]
    parameter ui_saved_window = [None]
    before testcase:
        python:
            ui_saved_preferences = (_preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions)
            _preferences.afm_enable = False
            _preferences.transitions = 0 if ui_width == 1280 else 2
            ui_saved_window = renpy.display.draw.info['max_window_size']
            renpy.display.draw.info['max_window_size'] = (max(ui_width,ui_saved_window[0]),max(ui_height,ui_saved_window[1]))
            renpy.set_physical_size((ui_width,ui_height))
    after testcase:
        python:
            _preferences.afm_enable,_preferences.fullscreen,_preferences.physical_size,_preferences.transitions = ui_saved_preferences
            renpy.display.draw.info['max_window_size'] = ui_saved_window
            renpy.display.draw.resize()
        run MainMenu(confirm=False)

testcase check_growth_ui.check:
    run Start("rm_check_ui_preview")
    run Function(renpy.set_physical_size,(ui_width,ui_height))
    pause .25
    assert eval renpy.get_physical_size() == (ui_width,ui_height)
    assert not eval rm_hud_visible()
    screenshot (rm_check_ui_shot("check-empty",ui_width,ui_height))
    click id "check_die_ui_str"
    click id "check_die_ui_dex"
    click id "check_die_ui_extra"
    screenshot (rm_check_ui_shot("check-selected",ui_width,ui_height))
    python:
        ui_rng_before = renpy.random.getstate()
        ui_energy_before = rm_player.energy
    run Function(renpy.restart_interaction)
    assert eval renpy.random.getstate() == ui_rng_before
    click id "check_review"
    assert eval rm_player.energy == ui_energy_before
    screenshot (rm_check_ui_shot("check-confirm",ui_width,ui_height))
    keysym "K_ESCAPE"
    assert eval not renpy.get_screen_variable("confirm_open","attribute_dice_select")
    run Function(renpy.set_focus,"attribute_dice_select","check_review")
    keysym "K_RETURN"
    run Function(renpy.set_focus,"attribute_dice_select","check_confirm")
    keysym "K_RETURN"
    pause until screen "attribute_check_roll_animation" timeout 5
    screenshot (rm_check_ui_shot("check-roll",ui_width,ui_height))
    click id "check_roll_action"
    pause until eval renpy.get_screen_variable('roll_finished','attribute_check_roll_animation') timeout 6
    click id "check_roll_action"
    pause until screen "attribute_check_result" timeout 5
    assert id "check_result_die_2"
    assert eval len(rm_check_rows(ui_check_result)) == 3
    assert eval ui_check_core.dice_multiplier == .75
    screenshot (rm_check_ui_shot("check-result",ui_width,ui_height))
    click id "check_continue"
    assert eval rm_hud_visible()
    screenshot (rm_check_ui_shot("check-return",ui_width,ui_height))

testcase check_growth_ui.rewards:
    run Start("rm_growth_ui_cards")
    run Function(renpy.set_physical_size,(ui_width,ui_height))
    click id "growth_card_0"
    assert eval rm_player.growth_reward_pending['str'] == 1
    screenshot (rm_check_ui_shot("growth-cards",ui_width,ui_height))
    click id "growth_clear"
    assert eval renpy.get_screen_variable("selected_card","rm_test_pending_card_choice") is None
    click id "growth_card_0"
    click id "growth_confirm"
    assert eval rm_player.growth_reward_pending['str'] == 0
    pause .5
    run Jump("rm_test_dice_growth_choice")
    click id "growth_die_str_1"
    assert eval len(rm_player.find_die('str_1').faces) == 6
    screenshot (rm_check_ui_shot("growth-die",ui_width,ui_height))
    keysym "K_ESCAPE"
    assert eval renpy.get_screen_variable("selected_die","rm_test_pending_die_choice") is None
    click id "growth_die_str_1"
    run Function(renpy.set_focus,"rm_test_pending_die_choice","growth_confirm")
    keysym "K_RETURN"
    assert eval len(rm_player.find_die('str_1').faces) == 8
    pause .5
    run Jump("rm_test_dice_growth_increase")
    click id "growth_die_str_1"
    click id "growth_confirm"
    click id "growth_face_2"
    assert eval rm_player.find_die('str_1').faces[2] == 5
    assert eval rm_player.growth_reward_pending['str'] == 1
    move id "growth_confirm"
    screenshot (rm_check_ui_shot("growth-face",ui_width,ui_height))
    click id "growth_confirm"
    assert eval rm_player.find_die('str_1').faces == [6]*6
    assert eval rm_player.growth_reward_pending['str'] == 0


testcase check_growth_ui.wake_limit_and_save:
    run Start("rm_check_ui_wake")
    run Function(renpy.set_physical_size,(ui_width,ui_height))
    assert eval ui_wake_limit == 2
    click id "check_die_wake_0"
    click id "check_die_wake_1"
    assert eval not renpy.get_displayable('attribute_dice_select','check_die_wake_2').is_sensitive()
    # Disabled children of a vpgrid have no focus rectangle; this SDK's id
    # fallback can target the tab bar. Click the visible third card's centre.
    click pos (1580,1030)
    assert eval renpy.get_screen_variable('selected_tab','attribute_dice_select') == 'usable'
    assert eval len(renpy.get_screen_variable('selected_die_ids','attribute_dice_select')) == 2
    assert eval renpy.get_screen_variable('preview','attribute_dice_select')['cost'] == 0
    screenshot (rm_check_ui_shot("check-wake-limit",ui_width,ui_height))
    run Function(renpy.save,"check-ui-selection",include_screenshot=False)
    click id "check_die_wake_0"
    run Function(renpy.load,"check-ui-selection")
    pause .3
    screenshot (rm_check_ui_shot("check-wake-loaded",ui_width,ui_height))
    # Native call-screen load restarts its unconfirmed selection, without settling.
    assert eval renpy.get_screen_variable('selected_die_ids','attribute_dice_select') == []
    assert eval rm_player.energy == 0 and len(rm_player.dice_pool) == 3
    click id "check_die_wake_0"
    click id "check_die_wake_1"
    click id "check_review"
    click id "check_confirm"
    assert eval len(ui_check_core.dice_ids) == 2
    assert eval ui_check_core.energy_cost == 0
    screenshot (rm_check_ui_shot("check-wake-result",ui_width,ui_height))
    click id "check_continue"

testcase check_growth_ui.unavailable_and_long_pool:
    run Start("rm_check_ui_preview")
    run Function(renpy.set_physical_size,(ui_width,ui_height))
    python:
        rm_player.energy = 0
        rm_player.dice_pool.extend(rm_core.RMDice("long_%d" % i, "str", [12]*20) for i in range(8))
    run Function(renpy.restart_interaction)
    click id "check_tab_all"
    assert id "check_die_ui_sealed"
    screenshot (rm_check_ui_shot("check-pool",ui_width,ui_height))
    scroll amount 6 pos (980,970)
    screenshot (rm_check_ui_shot("check-long-faces",ui_width,ui_height))
    scroll amount -10 pos (980,970)
    click id "check_die_ui_str"
    click id "check_die_ui_dex"
    python:
        shortage_before = (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot)
    click id "check_review"
    assert not id "check_confirm"
    assert screen "attribute_dice_select"
    assert eval not renpy.get_screen_variable('can_confirm','attribute_dice_select')
    assert eval '精力不足' in renpy.get_screen_variable('preview','attribute_dice_select')['reason']
    assert eval (renpy.random.getstate(),rm_player.energy,rm_player.day,rm_player.current_time_slot) == shortage_before
    screenshot (rm_check_ui_shot("check-unavailable",ui_width,ui_height))
