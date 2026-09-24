label rm_health_save_preview:
    $ rm_damage_health(15)
    $ rm_heal_health(.75)
    "生命值保存测试。"
    $ rm_damage_health(30)
    while True:
        pause

label rm_health_rollback_preview:
    # Simulate old saves with no HP and a plain formal-attribute dictionary.
    $ del rm_player.health
    $ rm_player.formal_attributes = __import__("builtins").dict(rm_player.formal_attributes)
    $ rm_core.ensure_second_stage_state(rm_player)
    $ rm_damage_health(10)
    "体质变化前。"
    $ rm_core.test_console_adjust_formal_attribute(rm_player, "con", -1)
    "体质变化后。"
    while True:
        pause

testsuite health:
    parameter saved_afm = [None]
    before testcase:
        $ saved_afm = _preferences.afm_enable
        $ _preferences.afm_enable = False
    after testcase:
        $ _preferences.afm_enable = saved_afm
        run MainMenu(confirm=False)

testcase health.hud_and_save:
    run Start("rm_hud_visual_preview")
    pause .3
    assert eval rm_status_health() == (30, 30)
    run Function(renpy.screenshot, "E:/ChatGPT/Temp/rememorial-health/hud-full.png")
    run Function(rm_damage_health, 15)
    move pos (1205, 205)
    pause .3
    assert id "hud_meter_tip"
    assert eval "15 / 30" in rm_status_health_tooltip()
    run Function(renpy.screenshot, "E:/ChatGPT/Temp/rememorial-health/hud-half.png")
    run Function(rm_heal_health, 30)
    run Jump("rm_health_save_preview")
    pause .3
    pause .2
    assert eval rm_player.health == 15.75
    run Function(renpy.save, "health-verification", include_screenshot=False)
    assert eval renpy.get_save_data("health-verification")["rm_player"].health == 15.75
    run Function(rm_damage_health, 30)
    pause .2
    assert eval rm_player.emergency_rescue_pending
    assert eval rm_player.emergency_rescue_used
    assert eval rm_player.health > 0
    run Function(rm_damage_health, 30)
    pause .2
    assert id "health_death_title"
    assert eval rm_health_game_over()
    run Function(renpy.screenshot, "E:/ChatGPT/Temp/rememorial-health/death.png")
    click id "health_load"
    pause .2
    assert screen "load"
    assert not id "health_death_title"
    run Function(renpy.load, "health-verification")
    pause .3
    assert eval rm_player.health == 15.75
    assert not id "health_death_title"
    run Function(rm_damage_health, 15.625)
    move pos (1205, 205)
    pause .3
    assert eval rm_player.health == .125
    run Function(renpy.screenshot, "E:/ChatGPT/Temp/rememorial-health/hud-low.png")

testcase health.rollback:
    run Start("rm_hud_visual_preview")
    pause .2
    run Jump("rm_health_rollback_preview")
    pause .2
    assert eval isinstance(rm_player.formal_attributes, rm_core.RevertableDict)
    assert eval rm_status_health() == (20, 30)
    click pos (1500, 1250)
    pause .2
    assert eval rm_player.formal_attributes["con"] == 5
    assert eval rm_status_health() == (15, 25)
    run Rollback(force=True)
    pause .2
    assert eval rm_player.formal_attributes["con"] == 6
    assert eval rm_status_health() == (20, 30)

testcase health.sleep_death:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_core.start_deep_fatigue(rm_player)
        rm_player.deep_fatigue['relapsed'] = True
        rm_player.day = rm_player.deep_fatigue['last_night']
        rm_player.weekday = 1
        rm_damage_health(26)
        rm_core.start_turn(rm_player, "sleep_decision")
    run Jump("rm_test_flow_loop")
    pause until screen "choice" timeout 5
    click "睡觉"
    pause .2
    assert eval rm_player.emergency_rescue_used
    assert eval rm_player.health > 0
    assert not id "health_death_title"

testcase health.wake_death:
    run Start("rm_test_flow_start")
    pause until screen "choice" timeout 5
    python:
        rm_core.start_deep_fatigue(rm_player)
        rm_player.day = rm_player.deep_fatigue['last_night']
        rm_player.weekday = 1
        rm_damage_health(22)
        rm_core.start_turn(rm_player, "sleep_decision")
        rm_core.continue_night(rm_player)
        rm_core.advance_time_slot(rm_player)
        rm_core.begin_sleep(rm_player, renpy.random, bonus_die_ids=[rm_core.usable_dice(rm_player, "con")[0].id] * 10)
        rm_core.finish_wake(rm_player, rm_core.RESULT_FAILURE, renpy.random)
    run Function(renpy.restart_interaction)
    pause .2
    assert eval rm_player.emergency_rescue_used
    assert eval rm_player.health > 0
    assert not id "health_death_title"
