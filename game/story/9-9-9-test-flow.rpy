label rm_ui_test_menu:
    menu:
        "接下来要测试什么呢？"

        "对话框UI":
            $ rm_ui_test_skin_active = True
            call screen rm_ui_test_dialogue_preview
            jump rm_ui_test_menu

        "时钟与心境条":
            $ rm_ui_test_skin_active = True
            call screen rm_ui_test_hud_preview
            jump rm_ui_test_menu

        "检定界面":
            $ rm_ui_test_skin_active = True
            $ rm_test_start_flow()
            jump rm_test_flow_loop

        "奖励选择":
            $ rm_ui_test_skin_active = True
            call rm_ui_test_reward_choice
            jump rm_ui_test_menu

        "返回标题菜单":
            $ rm_ui_test_skin_active = False
            return


label rm_ui_test_reward_choice:
    $ rm_ui_test_skin_active = True
    $ rm_test_start_flow()
    $ rm_test_reward_request = rm_test_prepare_growth_reward_test()
    if rm_test_reward_request:
        call rm_test_resolve_pending_cards
        "[rm_test_pending_result_text]"
    else:
        "奖励选择测试无法启动：没有可用的成长奖励。"
    return


label rm_test_flow_start:
    # 餐次、六个常规行动轮、睡觉决定，以及最多三个深夜行动轮。
    $ rm_ui_test_skin_active = False
    $ rm_test_start_flow()
    jump rm_test_flow_loop


label rm_test_flow_loop:
    if rm_core.is_dead(rm_ensure_player()):
        jump rm_health_end
    $ rm_test_sync_clock()
    $ rm_test_node = rm_ensure_player().current_time_slot

    if rm_test_node in rm_core.MEAL_SLOTS:
        menu:
            "现在是[rm_test_turn_text()]时间。"
            "吃饭":
                $ rm_core.choose_meal(rm_ensure_player(), True)
            "不吃":
                $ rm_core.choose_meal(rm_ensure_player(), False)
        jump rm_test_flow_loop

    if rm_test_node in rm_core.SLEEP_DECISIONS:
        menu:
            "今天就到这里，还是继续？"
            "睡觉":
                call rm_test_sleep_flow
            "继续行动":
                $ rm_core.continue_night(rm_ensure_player())
            "吃夜宵" if rm_test_node in ("night_break_1", "night_break_2") and not rm_ensure_player().night_snack_eaten:
                $ rm_core.choose_night_snack(rm_ensure_player())
        jump rm_test_flow_loop

    if rm_test_node == "forced_sleep":
        "你再也撑不住了，眼前一黑，失去了意识。"
        call rm_test_sleep_flow
        jump rm_test_flow_loop

    if rm_test_node == "wake_check":
        call rm_test_wake_flow
        jump rm_test_flow_loop

    "现在是[rm_test_day_text()][rm_test_turn_text()]时间点。"
    "接下来要做什么。"

    call screen rm_test_schedule_select
    $ selected_schedule = _return

    if selected_schedule == "__rm_ui_test_exit__":
        $ rm_ui_test_skin_active = False
        jump rm_ui_test_menu

    if rm_test_schedule_uses_check(selected_schedule):
        call rm_test_schedule_check_flow(selected_schedule)
    else:
        $ rm_test_outcome = rm_test_execute_rest_schedule(selected_schedule)

    "[rm_test_last_result_text]"

    if rm_test_outcome.get("available", True):
        call rm_test_resolve_pending_cards
        $ rm_test_advance_turn(selected_schedule)
    jump rm_test_flow_loop


label rm_test_sleep_flow:
    $ rm_test_outcome = rm_test_execute_rest_schedule("test_sleep")
    if rm_core.is_dead(rm_ensure_player()):
        jump rm_health_end
    "[rm_test_last_result_text]"
    call rm_test_resolve_pending_cards
    return


label rm_test_wake_flow:
    "该起床了。这次意志检定不消耗精力。"
    if rm_core.usable_dice(rm_ensure_player(), "pow"):
        $ rm_wake_requirement = rm_core.wake_requirement(rm_ensure_player())
        $ rm_wake_max_dice = rm_core.max_dice_for_check(rm_core.CheckSpec("pow", rm_wake_requirement), rm_core.mood_check_profile(rm_core.mood_state(rm_ensure_player())))
        call screen attribute_dice_select("pow", min_dice=1, max_dice=rm_wake_max_dice, requirement=rm_wake_requirement, check_kind="起床", action_type=rm_core.ACTION_WAKE)
        $ rm_wake_dice = _return
        if rm_wake_dice == "__rm_ui_test_exit__":
            $ rm_ui_test_skin_active = False
            jump rm_ui_test_menu
        $ rm_wake_result = rm_core.perform_wake_check(rm_ensure_player(), rm_wake_requirement, rm_wake_dice, rng=renpy.random)
        $ rm_wake_display = rm_test_result_dict_for_schedule(rm_wake_result, rm_ensure_player(), rm_wake_dice, "test_sleep")
        call screen attribute_check_roll_animation(rm_wake_display)
        call screen attribute_check_result(rm_wake_display)
    else:
        "没有可用的意志骰，你没能提前醒来。"
        $ rm_wake_result = rm_core.RESULT_FAILURE
    $ rm_wake_outcome = rm_core.finish_wake(rm_ensure_player(), rm_wake_result, rng=renpy.random)
    if rm_core.is_dead(rm_ensure_player()):
        jump rm_health_end
    $ rm_test_sync_clock()
    if rm_wake_outcome["skip_morning"] == 2:
        "醒来时已经到了午饭时间。"
    elif rm_wake_outcome["skip_morning"] == 1:
        "你睡过了上午的第一轮。"
    else:
        "你按正常时间起床了。"
    if "healthy_routine_blocked" in rm_wake_outcome["events"]:
        if "good_routine_spent" in rm_wake_outcome["events"]:
            "健康作息抵消了本次疲劳和困意，随后消失。"
        else:
            "健康作息抵消了本次疲劳和困意，并保留下来。"
    elif "good_routine_spent" in rm_wake_outcome["events"]:
        "这次健康作息未能抵消熬夜影响，并已消耗。"
    if rm_wake_outcome["fatigue"]:
        "熬夜带来了1层疲劳，精力上限降低1点。"
    if rm_wake_outcome["drowsiness"]:
        "提前起床带来了[rm_wake_outcome['drowsiness']]层困意。"
    $ rm_wake_disease_events = [event for event in rm_wake_outcome["events"] if event.startswith("deep_fatigue_")]
    if rm_wake_disease_events:
        $ rm_wake_disease_text = rm_test_event_text(rm_wake_disease_events)
        "[rm_wake_disease_text]"
    call rm_test_resolve_pending_cards
    return


label rm_test_schedule_check_flow(schedule_id):
    $ rm_test_required_stat = rm_test_check_attribute(schedule_id)
    $ rm_test_requirement = rm_test_check_requirement(schedule_id)
    $ rm_test_check_kind = rm_test_schedule_names()[schedule_id]
    $ rm_test_allowed_stats = rm_test_allowed_die_attributes(schedule_id)
    $ rm_test_required_die_stats = rm_test_required_die_attributes(schedule_id)
    $ selected_die_ids = None

    while selected_die_ids is None:
        call screen attribute_dice_select(rm_test_required_stat, min_dice=1, max_dice=3, requirement=rm_test_requirement, check_kind=rm_test_check_kind, action_type=rm_core.ACTION_SCHEDULE, allowed_stats=rm_test_allowed_stats, required_die_stats=rm_test_required_die_stats)
        $ selected_die_ids = _return

        if selected_die_ids == "__rm_ui_test_exit__":
            $ rm_ui_test_skin_active = False
            jump rm_ui_test_menu

    $ rm_test_check_result = rm_test_perform_schedule_check(schedule_id, selected_die_ids, rm_test_requirement)

    call screen attribute_check_roll_animation(rm_test_check_result)

    call screen attribute_check_result(rm_test_check_result)

    $ rm_test_outcome = rm_test_finalize_schedule_check(schedule_id, rm_test_check_result)
    return


label rm_test_resolve_pending_cards:
    $ rm_test_pending_request = rm_test_pending_card_request()
    while rm_test_pending_request:
        "[rm_test_pending_card_title(rm_test_pending_request)]"
        call screen rm_test_pending_card_choice(rm_test_pending_request)
        $ rm_test_pending_card = _return
        if rm_test_pending_card == "__rm_ui_test_exit__":
            $ rm_ui_test_skin_active = False
            jump rm_ui_test_menu

        $ rm_test_pending_die_id = None
        $ rm_test_pending_face_index = None
        if rm_test_card_needs_die_choice(rm_test_pending_card):
            call screen rm_test_pending_die_choice(rm_test_pending_request, rm_test_pending_card)
            $ rm_test_pending_die_id = _return
            if rm_test_pending_die_id == "__rm_ui_test_exit__":
                $ rm_ui_test_skin_active = False
                jump rm_ui_test_menu

        if rm_test_card_needs_face_choice(rm_test_pending_card):
            call screen rm_test_pending_face_choice(rm_test_pending_die_id, rm_test_pending_card)
            $ rm_test_pending_face_index = _return
            if rm_test_pending_face_index == "__rm_ui_test_exit__":
                $ rm_ui_test_skin_active = False
                jump rm_ui_test_menu

        $ rm_test_pending_card = rm_test_apply_card_selection(rm_test_pending_card, rm_test_pending_die_id, rm_test_pending_face_index)
        $ rm_test_pending_result_text = rm_test_apply_pending_card(rm_test_pending_request, rm_test_pending_card)
        "[rm_test_pending_result_text]"
        $ rm_test_pending_request = rm_test_pending_card_request()
    return


label test_rm_ui_layout_editor:
    call screen rm_ui_layout_editor("dice_select")
    return
