# Regression coverage for shared growth rules and the real die-choice screen.
testsuite dice_growth:
    parameter saved_afm = [None]
    before testcase:
        $ saved_afm = _preferences.afm_enable
        $ _preferences.afm_enable = False
    after testcase:
        $ _preferences.afm_enable = saved_afm
        run MainMenu(confirm=False)

testcase dice_growth.training_penalty_before_next_round:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_player.mood = 0
        rm_player.degradation_progress["str"] = 5
        rm_player.find_die("str_1").faces = [1] * 6
        rm_player.dice_pool.append(rm_core.RMDice("str_regression", "str", [1] * 6))
        rm_player.energy = rm_core.energy_max(rm_player)
    click "不吃"
    click "继续"
    click "继续"
    pause until screen "rm_test_schedule_select" timeout 5
    click "力量训练（测试）"
    pause until screen "attribute_dice_select" timeout 5
    $ renpy.set_screen_variable("selected_die_ids", renpy.python.RevertableList(("str_1", "str_regression")), screen="attribute_dice_select")
    run Function(renpy.restart_interaction)
    pause .2
    click "确认骰子"
    pause .2
    click "确认"
    pause until screen "attribute_check_result" timeout 5
    assert eval rm_test_check_result["_result"].dice_ids == ["str_1", "str_regression"]
    assert eval rm_test_check_result["_result"].rank == rm_core.RESULT_BIG_FAILURE
    click "继续"
    assert eval rm_player.degradation_penalty_pending["str"] == 1
    assert eval rm_player.degradation_progress["str"] == 0
    assert eval rm_player.current_time_slot == "morning_1"
    click "继续"
    click "继续"
    pause until screen "rm_test_pending_card_choice" timeout 5
    assert eval rm_test_pending_request["mode"] == "degradation"
    assert eval rm_player.current_time_slot == "morning_1"
    # All-one d6 fixtures leave only non-targeted legal penalties.
    click expression rm_test_card_label(rm_test_pending_request["cards"][0])
    pause until not screen "rm_test_pending_card_choice" timeout 5
    assert eval rm_player.degradation_penalty_pending["str"] == 0
    assert eval rm_player.current_time_slot == "morning_1"
    click "继续"
    assert eval rm_player.current_time_slot == "morning_2"
    assert eval rm_player.degradation_progress["str"] == 0

testcase dice_growth.sleep_converts_training_once:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_player.test_growth_progress["dex"] = 6
        rm_core.start_turn(rm_player, "sleep_decision")
    run Jump("rm_test_flow_loop")
    pause until screen "choice" timeout 5
    click "睡觉"
    assert eval rm_test_outcome["events"].count("test_training_bonus:dex") == 1
    assert eval rm_player.test_growth_progress["dex"] == 0
    assert eval rm_player.attribute_bonus_gain_counters["dex"] == 1
    assert eval rm_player.day == 102
    assert eval rm_player.current_time_slot == "breakfast"
    click "继续"
    pause until screen "choice" timeout 5
    python:
        rm_core.start_turn(rm_player, "sleep_decision")
    run Jump("rm_test_flow_loop")
    pause until screen "choice" timeout 5
    click "睡觉"
    assert eval "test_training_bonus:dex" not in rm_test_outcome["events"]
    assert eval rm_player.attribute_bonus_gain_counters["dex"] == 1
    assert eval rm_player.day == 103

testcase dice_growth.chosen_upgrade:
    run Start("rm_test_dice_growth_choice")
    pause until screen "rm_test_pending_die_choice" timeout 5
    assert eval [die["id"] for die in rm_test_pending_dice_choices(rm_test_pending_request, rm_test_pending_card)] == ["str_1"]
    assert "str_1"
    assert not "str_capped"
    click "str_1"
    pause until screen "choice" timeout 5
    assert eval len(rm_player.find_die("str_1").faces) == 8
    assert eval rm_player.find_die("str_1").faces[-2:] == [1, 6]
    assert eval len(rm_player.find_die("str_capped").faces) == 12
    assert eval rm_player.growth_reward_pending["str"] == 0

label rm_test_dice_growth_choice:
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.find_die("str_1").faces = [1, 2, 3, 4, 5, 6]
    $ rm_player.dice_pool.append(rm_core.RMDice("str_capped", "str", [12] * 12))
    $ rm_player.growth_reward_pending["str"] = 1
    $ rm_test_pending_request = {"mode": "growth", "attr": "str"}
    $ rm_test_pending_card = {"type": "upgrade_chosen_die_type"}
    call screen rm_test_pending_die_choice(rm_test_pending_request, rm_test_pending_card)
    $ rm_test_pending_card = rm_test_apply_card_selection(rm_test_pending_card, _return)
    $ rm_test_pending_result_text = rm_test_apply_pending_card(rm_test_pending_request, rm_test_pending_card)
    menu:
        "返回":
            return

testcase dice_growth.chosen_increase:
    run Start("rm_test_dice_growth_increase")
    pause until screen "rm_test_pending_die_choice" timeout 5
    assert eval [die["id"] for die in rm_test_pending_dice_choices(rm_test_pending_request, rm_test_pending_card)] == ["str_1"]
    assert not "str_capped"
    click "str_1"
    pause until screen "rm_test_pending_face_choice" timeout 5
    assert eval rm_test_pending_face_choices("str_1", card=rm_test_pending_card) == [{"index": 2, "value": 5}]
    click "第3面：5"
    pause until screen "choice" timeout 5
    assert eval rm_player.find_die("str_1").faces == [6] * 6
    assert eval rm_player.growth_reward_pending["str"] == 0

label rm_test_dice_growth_increase:
    $ rm_player = rm_core.create_initial_character()
    $ rm_player.find_die("str_1").faces = [6, 6, 5, 6, 6, 6]
    $ rm_player.dice_pool.append(rm_core.RMDice("str_capped", "str", [8] * 8))
    $ rm_player.growth_reward_pending["str"] = 1
    $ rm_test_pending_request = {"mode": "growth", "attr": "str"}
    $ rm_test_pending_card = {"type": "increase_chosen_face", "increase_amount": 2}
    call screen rm_test_pending_die_choice(rm_test_pending_request, rm_test_pending_card)
    $ rm_test_pending_card = rm_test_apply_card_selection(rm_test_pending_card, _return)
    call screen rm_test_pending_face_choice(rm_test_pending_card["die_id"], rm_test_pending_card)
    $ rm_test_pending_card = rm_test_apply_card_selection(rm_test_pending_card, face_index=_return)
    $ rm_test_pending_result_text = rm_test_apply_pending_card(rm_test_pending_request, rm_test_pending_card)
    menu:
        "返回":
            return
