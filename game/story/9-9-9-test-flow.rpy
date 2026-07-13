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
    # 测试行动轮：上午1，上午2，下午1，下午2，晚上1，晚上2，深夜。
    $ rm_ui_test_skin_active = False
    $ rm_test_start_flow()
    jump rm_test_flow_loop


label rm_test_flow_loop:
    $ rm_test_sync_clock()

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

    if selected_schedule == "test_sleep":
        call rm_test_resolve_pending_cards

    $ rm_test_advance_turn(selected_schedule)
    jump rm_test_flow_loop


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
            call screen rm_test_pending_face_choice(rm_test_pending_die_id)
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
