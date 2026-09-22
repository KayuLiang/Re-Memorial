# Developer test: exercise real menu routing and shared time settlement in Ren'Py.
testsuite sleep_cycle:
    parameter saved_afm = [None]
    before testcase:
        $ saved_afm = _preferences.afm_enable
        $ _preferences.afm_enable = False
    after testcase:
        $ _preferences.afm_enable = saved_afm
        run MainMenu(confirm=False)

testcase sleep_cycle.day_flow:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    assert eval rm_player.current_time_slot == "breakfast"
    assert "吃饭"
    assert "不吃"
    click "不吃"
    assert eval rm_player.current_time_slot == "morning_1"
    click "继续"
    click "继续"
    pause until screen "rm_test_schedule_select" timeout 5
    assert screen "rm_test_schedule_select"
    click "休息（测试）"
    click "继续"
    assert eval rm_player.current_time_slot == "morning_2"
    click "继续"
    click "继续"
    pause until screen "rm_test_schedule_select" timeout 5
    click "休息（测试）"
    click "继续"
    assert eval rm_player.current_time_slot == "lunch"
    click "吃饭"
    assert eval rm_player.current_time_slot == "afternoon_1"
    python:
        for action in range(4):
            if rm_player.current_time_slot == "dinner":
                rm_core.choose_meal(rm_player, True)
            rm_core.advance_time_slot(rm_player)
    run Jump("rm_test_flow_loop")
    pause until screen "choice" timeout 5
    assert eval rm_player.current_time_slot == "sleep_decision"
    click "睡觉"
    assert eval rm_player.day == 102
    assert eval rm_player.current_time_slot == "breakfast"
    assert eval rm_player.good_routine_streak == 1
    python:
        for night in range(6):
            rm_core.start_turn(rm_player, "sleep_decision")
            rm_core.begin_sleep(rm_player, renpy.random)
    assert eval rm_player.good_routine
    assert eval rm_player.day == 108

testcase sleep_cycle.coma_wake_and_shield:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_player.good_routine = True
        rm_player.formal_attributes["pow"] = 10
        rm_core.add_emotion(rm_player, rm_core.EMOTION_DISTRACTION, 1)
        rm_player.find_die("pow_1").faces = [20] * 20
        rm_player.find_die("pow_2").faces = [20] * 20
        rm_core.start_turn(rm_player, "sleep_decision")
        rm_core.continue_night(rm_player)
        rm_core.advance_time_slot(rm_player)
    run Jump("rm_test_flow_loop")
    pause until screen "choice" timeout 5
    click "吃夜宵"
    pause until screen "choice" timeout 5
    assert eval rm_player.current_time_slot == "night_break_2"
    assert "吃夜宵"
    click "继续行动"
    assert eval rm_player.current_time_slot == "late_night_3"
    python:
        rm_core.advance_time_slot(rm_player)
    run Jump("rm_test_flow_loop")
    assert eval rm_player.current_time_slot == "forced_sleep"
    click "继续"
    assert eval rm_player.current_time_slot == "wake_check"
    click "继续"
    click "继续"
    pause until screen "attribute_dice_select" timeout 5
    assert eval rm_wake_requirement == 22
    assert eval renpy.get_screen_variable("requirement", "attribute_dice_select") == 22
    assert eval attribute_check_header("pow", 22, rm_core.ACTION_WAKE)["fixed"] == 5
    assert eval attribute_check_header("pow", 22, rm_core.ACTION_WAKE)["needed_roll"] == 17
    $ renpy.set_screen_variable("selected_die_ids", ["pow_1", "pow_2"], screen="attribute_dice_select")
    run Function(renpy.restart_interaction)
    pause .2
    assert eval renpy.get_screen_variable("selected_die_ids", "attribute_dice_select") == ["pow_1", "pow_2"]
    click "确认骰子"
    pause .2
    assert eval renpy.get_screen_variable("confirm_open", "attribute_dice_select")
    assert eval attribute_check_energy_cost("pow", ["pow_1", "pow_2"], rm_core.ACTION_WAKE) == 0
    click "确认"
    pause until screen "attribute_check_result" timeout 5
    assert eval rm_wake_result.rank == rm_core.RESULT_BIG_SUCCESS
    assert eval rm_wake_result.base_requirement == 22
    assert eval rm_wake_result.requirement == 22
    assert eval rm_wake_result.extra_modifier == 0
    assert eval rm_wake_result.total == 45
    assert eval rm_wake_result.energy_cost == 0
    click "继续"
    assert eval rm_player.current_time_slot == "breakfast"
    assert eval rm_player.day == 102
    assert eval rm_player.fatigue_layers == rm_wake_outcome["fatigue"]
    assert eval rm_core.emotion_layers(rm_player, rm_core.EMOTION_DISTRACTION) == rm_wake_outcome["distraction"]
    assert eval rm_player.good_routine == ("good_routine_spent" not in rm_wake_outcome["events"])
    assert eval (rm_player.fatigue_layers == 0) == ("healthy_routine_blocked" in rm_wake_outcome["events"])
    assert eval rm_player.energy == rm_core.energy_max(rm_player)
    assert eval rm_player.sleep_pending is None

testcase sleep_cycle.disease_deadline:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_core.start_deep_fatigue(rm_player)
        rm_core.start_turn(rm_player, "sleep_decision")
        rm_core.continue_night(rm_player)
        rm_core.advance_time_slot(rm_player)
        rm_core.begin_sleep(rm_player, renpy.random)
        rm_core.finish_wake(rm_player, rm_core.RESULT_FAILURE)
        for night in range(6):
            rm_core.start_turn(rm_player, "sleep_decision")
            rm_core.begin_sleep(rm_player, renpy.random)
    assert eval rm_player.day == 108
    assert eval rm_player.deep_fatigue is None
    assert eval rm_player.formal_attributes["con"] == 4
    assert eval rm_player.current_attribute("con") == 4
    assert eval rm_player.degradation_penalty_pending["con"] == 2
    assert eval not rm_player.good_routine
