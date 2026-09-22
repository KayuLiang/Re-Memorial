label rm_numeric_rollback_preview:
    $ rm_core.ensure_second_stage_state(rm_player)
    $ rm_player.find_die("str_1").faces[0] = 1
    $ rm_core.start_deep_fatigue(rm_player)
    "数值变化前。"
    python:
        rm_core.test_console_adjust_attribute_value(rm_player, "str", 1)
        rm_core.add_attribute_bonus(rm_player, "str", 1)
        rm_core.add_training_fatigue(rm_player, "test_strength_training", 1)
        rm_core.add_dice_growth_progress(rm_player, "str", 2)
        rm_player.meal_choices["breakfast"] = True
        rm_player.fatigue_history.append(rm_player.day + 7)
        rm_player.deep_fatigue["layers"] += 1
        rm_core.add_emotion(rm_player, rm_core.EMOTION_DISTRACTION, 2)
        rm_player.pending_bipolar_medications["lithium"] = True
        rm_player.find_die("str_1").faces[0] = 6
        rm_core.set_die_enchantment(rm_player.find_die("str_1"), rm_core.ENCHANT_LIGHT)
        rm_player.dice_pool.append(rm_core.RMDice("str_rollback", "str", [1] * 6))
        rm_player.mood = 5
        rm_player.energy -= 1
    "数值变化后。"
    while True:
        pause

label rm_numeric_save_preview:
    python:
        rm_core.add_attribute_value(rm_player, "dex", 1)
        rm_core.add_dice_growth_progress(rm_player, "dex", 2)
        rm_player.find_die("dex_1").faces[0] = 6
    "嵌套数值保存测试。"
    while True:
        pause

label rm_numeric_legacy_preview:
    python:
        builtins = __import__("builtins")
        rm_player.attribute_values = builtins.dict(rm_player.attribute_values)
        rm_player.attribute_values["str"] = 2
        rm_player.attribute_bonuses = builtins.dict(
            (name, builtins.list(values)) for name, values in rm_player.attribute_bonuses.items()
        )
        rm_player.attribute_bonuses["str"].append(builtins.dict(value=1, source="legacy"))
        rm_player.dice_pool = builtins.list(rm_player.dice_pool)
        rm_player.find_die("str_1").faces = builtins.list(rm_player.find_die("str_1").faces)
        for field in ("test_growth_progress", "training_fatigue", "dice_growth_progress",
                      "growth_reward_pending", "degradation_progress", "degradation_penalty_pending",
                      "attribute_bonus_gain_counters", "attribute_value_gain_counters",
                      "formal_attribute_gain_counters"):
            setattr(rm_player, field, builtins.dict(getattr(rm_player, field)))
        rm_player.dice_growth_progress["str"] = 3
        rm_player.meal_choices = builtins.dict(breakfast=True)
        rm_player.sleep_fatigue = builtins.list(rm_player.sleep_fatigue)
        rm_player.fatigue_history = builtins.list((108,))
        rm_player.deep_fatigue = builtins.dict(layers=2, first_day=101, last_night=107,
                                               last_late_day=100, relapsed=True)
        rm_player.sleep_pending = builtins.dict(forced_coma=False, night_actions=1, slept_day=101)
        del builtins
    "旧存档数据准备完成。"
    "旧存档转换测试。"
    while True:
        pause

testsuite numeric_rollback:
    parameter saved_afm = [None]
    before testcase:
        $ saved_afm = _preferences.afm_enable
        $ _preferences.afm_enable = False
    after testcase:
        $ _preferences.afm_enable = saved_afm
        run MainMenu(confirm=False)

testcase numeric_rollback.rollback_nested_state:
    run Start("rm_hud_visual_preview")
    pause .2
    run Jump("rm_numeric_rollback_preview")
    pause .2
    assert "数值变化前"
    assert eval all(isinstance(getattr(rm_player, field), rm_core.RevertableDict) for field in ("formal_attributes", "attribute_values", "attribute_bonuses", "test_growth_progress", "training_fatigue", "dice_growth_progress", "growth_reward_pending", "degradation_progress", "degradation_penalty_pending", "attribute_bonus_gain_counters", "attribute_value_gain_counters", "formal_attribute_gain_counters", "meal_choices", "emotions", "pending_bipolar_medications", "medicine_counts", "environment_diseases", "time_habits"))
    assert eval isinstance(rm_player.dice_pool, rm_core.RevertableList) and all(isinstance(die, rm_core.RevertableObject) and isinstance(die.faces, rm_core.RevertableList) for die in rm_player.dice_pool)
    assert eval (rm_player.attribute_values["str"], len(rm_player.attribute_bonuses["str"]), rm_player.training_fatigue["test_strength_training"], rm_player.dice_growth_progress["str"]) == (0, 0, 0, 0)
    click pos (1500, 1250)
    pause .2
    assert "数值变化后"
    assert eval (rm_player.attribute_values["str"], len(rm_player.attribute_bonuses["str"]), rm_player.training_fatigue["test_strength_training"], rm_player.dice_growth_progress["str"]) == (1, 1, 1, 2)
    assert eval isinstance(rm_player.attribute_bonuses["str"], rm_core.RevertableList) and isinstance(rm_player.attribute_bonuses["str"][0], rm_core.RevertableDict)
    assert eval (rm_player.meal_choices["breakfast"], len(rm_player.fatigue_history), rm_player.deep_fatigue["layers"]) == (True, 1, 2)
    assert eval (rm_core.emotion_layers(rm_player, rm_core.EMOTION_DISTRACTION), bool(rm_player.pending_bipolar_medications.get("lithium"))) == (2, True)
    assert eval (rm_player.find_die("str_1").faces[0], rm_player.find_die("str_1").enchantment, len(rm_player.dice_pool), rm_player.mood, rm_player.energy) == (6, rm_core.ENCHANT_LIGHT, 8, 5, 1)
    run Rollback(force=True)
    pause .2
    assert "数值变化前"
    assert eval (rm_player.attribute_values["str"], len(rm_player.attribute_bonuses["str"]), rm_player.training_fatigue["test_strength_training"], rm_player.dice_growth_progress["str"]) == (0, 0, 0, 0)
    assert eval (rm_player.meal_choices, len(rm_player.fatigue_history), rm_player.deep_fatigue["layers"]) == ({}, 0, 1)
    assert eval (rm_core.emotion_layers(rm_player, rm_core.EMOTION_DISTRACTION), bool(rm_player.pending_bipolar_medications.get("lithium"))) == (0, False)
    assert eval (rm_player.find_die("str_1").faces[0], rm_player.find_die("str_1").enchantment, len(rm_player.dice_pool), rm_player.mood, rm_player.energy) == (1, None, 7, -40, 2)

testcase numeric_rollback.save_nested_state:
    run Start("rm_hud_visual_preview")
    pause .2
    run Jump("rm_numeric_save_preview")
    pause .2
    assert eval (rm_player.attribute_values["dex"], rm_player.dice_growth_progress["dex"], rm_player.find_die("dex_1").faces[0]) == (1, 2, 6)
    run Function(renpy.save, "numeric-rollback-verification", include_screenshot=False)
    python:
        rm_core.add_attribute_value(rm_player, "dex", 1)
        rm_core.add_dice_growth_progress(rm_player, "dex", 2)
        rm_player.find_die("dex_1").faces[0] = 1
    assert eval rm_player.attribute_values["dex"] == 2
    assert eval rm_player.dice_growth_progress["dex"] == 10
    assert eval rm_player.find_die("dex_1").faces[0] == 1
    run Function(renpy.load, "numeric-rollback-verification")
    pause .2
    assert eval (rm_player.attribute_values["dex"], rm_player.dice_growth_progress["dex"], rm_player.find_die("dex_1").faces[0]) == (1, 2, 6)

testcase numeric_rollback.legacy_save_conversion:
    run Start("rm_hud_visual_preview")
    pause .2
    run Jump("rm_numeric_legacy_preview")
    pause .2
    assert "旧存档数据准备完成"
    click pos (1500, 1250)
    pause .2
    assert "旧存档转换测试"
    assert eval type(rm_player.attribute_values) is dict and type(rm_player.dice_pool) is list and type(rm_player.find_die("str_1").faces) is list
    run Function(renpy.save, "numeric-legacy-verification", include_screenshot=False)
    run Function(renpy.load, "numeric-legacy-verification")
    pause .2
    assert eval (rm_player.attribute_values["str"], rm_player.dice_growth_progress["str"], rm_player.meal_choices["breakfast"], rm_player.deep_fatigue["layers"]) == (2, 3, True, 2)
    assert eval all(isinstance(getattr(rm_player, field), rm_core.RevertableDict) for field in ("formal_attributes", "attribute_values", "attribute_bonuses", "test_growth_progress", "training_fatigue", "dice_growth_progress", "growth_reward_pending", "degradation_progress", "degradation_penalty_pending", "attribute_bonus_gain_counters", "attribute_value_gain_counters", "formal_attribute_gain_counters", "meal_choices", "deep_fatigue", "sleep_pending"))
    assert eval all(isinstance(rm_player.attribute_bonuses[name], rm_core.RevertableList) for name in rm_core.ATTRIBUTES)
    assert eval isinstance(rm_player.attribute_bonuses["str"][0], rm_core.RevertableDict)
    assert eval isinstance(rm_player.dice_pool, rm_core.RevertableList) and all(isinstance(die.faces, rm_core.RevertableList) for die in rm_player.dice_pool)
    assert eval isinstance(rm_player.sleep_fatigue, rm_core.RevertableList) and isinstance(rm_player.fatigue_history, rm_core.RevertableList)
