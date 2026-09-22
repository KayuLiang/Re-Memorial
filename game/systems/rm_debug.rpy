label rm_debug_create_character:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ summary = rm_attribute_summary()
    "RM Debug: 初始角色已创建。"
    "属性：[summary]"
    "精力：[rm_player.energy] / [rm_energy_max()]"
    return

label rm_debug_mock_check:
    $ rm_ensure_player()
    $ result = rm_perform_mock_check("dex", 5)
    "RM Debug: Mock DEX 检定。"
    "可执行：[result.available]  结果等级：[result.rank]  总值：[result.total]  消耗精力：[result.energy_cost]"
    "骰子：[result.dice_results]"
    return

label rm_debug_mood_check:
    $ rm_ensure_player()
    $ rm_player.mood = -80
    $ result = rm_perform_mock_check("dex", 5)
    "RM Debug: Mood=-80 的检定修正。"
    "心境：[result.mood_state]  属性修正：[result.attribute_modifier]  骰面倍率：[result.dice_multiplier]  总值：[result.total]"
    return

label rm_debug_turn_end:
    $ rm_ensure_player()
    $ rm_player.mood = 200
    $ settlement = rm_end_action_round(0)
    "RM Debug: 行动轮结束结算。"
    "Mood：[settlement['mood']]  病程：[settlement['disease_state']]  事件：[settlement['events']]"
    return

label test_mood_disease_system:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ rm_player.mood = 100
    "Mood=100 POW=6 enter probability: [calculate_enter_disease_probability(rm_player)]"
    $ rm_player.mood = 150
    "Mood=150 POW=6 enter probability: [calculate_enter_disease_probability(rm_player)]"
    $ rm_player.disease_state = rm_core.DISEASE_MANIA
    $ rm_player.mood = 50
    $ rm_player.man = 100
    $ rm_player.dep = 20
    $ stable_event = apply_stable_return(rm_player)
    "Stable test: [stable_event] mood=[rm_player.mood] disease=[rm_player.disease_state]"
    $ rm_player.disease_state = rm_core.DISEASE_DEPRESSION
    $ rm_player.mood = -100
    $ rm_player.dep = 120
    $ rm_player.man = 0
    "Switch probability: [calculate_switch_probability(rm_player)]"
    return

label test_rest_growth_system:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ add_attribute_bonus(rm_player, "str", 3)
    "Before small rest bonuses: [rm_player.attribute_bonuses['str']]"
    $ small_events = process_small_rest(rm_player)
    "Small rest events: [small_events]"
    "After small rest bonuses=[rm_player.attribute_bonuses['str']] values=[rm_player.attribute_values['str']]"
    $ add_attribute_value(rm_player, "str", 3)
    $ large_events = process_large_rest(rm_player)
    "Large rest events: [large_events]"
    "After large rest values=[rm_player.attribute_values['str']] formal=[rm_player.formal_attributes['str']] degradation=[rm_player.degradation_progress['str']]"
    return

label test_strength_training_bonus_rule:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    "Strength training STR bonus rule test."
    python:
        strength_training_debug = []
        for str_value in (1, 6, 7, 12, 13, 20):
            success_plan = rm_core.calculate_strength_training_bonus_plan(str_value, rm_core.RESULT_SUCCESS)
            hard_plan = rm_core.calculate_strength_training_bonus_plan(str_value, rm_core.RESULT_HARD_SUCCESS)
            critical_plan = rm_core.calculate_strength_training_bonus_plan(str_value, "critical_success")
            total_gained = 0
            rng = rm_core.random.Random(str_value)
            for _ in range(20):
                sample = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=rng)
                sample.formal_attributes["str"] = str_value
                result = rm_core.CheckResult(available=True, attribute="str", rank=rm_core.RESULT_SUCCESS, success=True)
                total_gained += rm_core.apply_strength_training_str_bonus(sample, result, rng=rng)["success_count"]
            strength_training_debug.append({
                "str": str_value,
                "success": success_plan["roll_plan"],
                "hard": hard_plan["roll_plan"],
                "critical": critical_plan["roll_plan"],
                "average": total_gained / 20.0,
            })
    $ strength_training_line = strength_training_debug[0]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    $ strength_training_line = strength_training_debug[1]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    $ strength_training_line = strength_training_debug[2]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    $ strength_training_line = strength_training_debug[3]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    $ strength_training_line = strength_training_debug[4]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    $ strength_training_line = strength_training_debug[5]
    "STR [strength_training_line['str']] success=[strength_training_line['success']] hard=[strength_training_line['hard']] critical=[strength_training_line['critical']] avg20=[strength_training_line['average']]"
    return

label test_growth_reward_system:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ add_dice_growth_progress(rm_player, "int", 6)
    $ growth_events = process_dice_growth_progress_on_small_rest(rm_player)
    $ growth_cards = draw_growth_reward_cards(rm_player, "int", 3)
    $ growth_result = apply_growth_reward(rm_player, "int", growth_cards[0]) if growth_cards else None
    "Growth events: [growth_events]"
    "Growth cards: [growth_cards]"
    "Growth result: [growth_result]"
    "INT dice: [rm_core.dice_pool_summary(rm_player)]"
    return

label test_degradation_penalty_system:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ add_degradation_progress(rm_player, "dex", 6)
    $ penalty_cards = draw_degradation_penalty_cards(rm_player, "dex", 3)
    $ penalty_result = apply_degradation_penalty(rm_player, "dex", penalty_cards[0]) if penalty_cards else None
    "Penalty cards: [penalty_cards]"
    "Penalty result: [penalty_result]"
    "DEX dice: [rm_core.dice_pool_summary(rm_player)]"
    return

label test_fog_cards:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ cards = draw_growth_reward_cards(rm_player, "str", 3)
    $ fogged = apply_fog_to_cards(cards)
    $ fog_result = resolve_fog_reward(rm_player, "str", fogged[0]) if fogged else None
    "Fogged cards: [fogged]"
    "Fog result: [fog_result]"
    return

label test_full_turn_second_stage:
    $ rm_reset_player({"str": 3, "dex": 3, "int": 2})
    $ start_turn(rm_player, "morning_1")
    $ mock = rm_core.ScheduleSpec("mock_study", "Mock Study", mood_delta=5)
    $ turn_result = resolve_action(rm_player, mock)
    $ end_result = end_turn(rm_player, turn_result)
    "End turn: [end_result]"
    $ rm_player.mood = 100
    $ end_result_2 = end_turn(rm_player, {"mood_delta": 0, "events": []})
    "Disease check turn: [end_result_2]"
    $ day_result = end_day(rm_player)
    $ week_result = end_week_if_needed(rm_player)
    "End day: [day_result]"
    "End week if needed: [week_result]"
    return
