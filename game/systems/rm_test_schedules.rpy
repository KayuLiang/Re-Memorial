default rm_test_flow_active = False
default rm_test_day = 101
default rm_test_turn_index = 0
default rm_test_last_result_text = ""

init -9 python:
    RM_TEST_TURNS = (
        ("上午1", 8 * 60),
        ("上午2", 10 * 60),
        ("下午1", 13 * 60),
        ("下午2", 15 * 60),
        ("晚上1", 18 * 60),
        ("晚上2", 20 * 60),
        ("深夜", 23 * 60),
    )

    def rm_test_day_text():
        return "第{}天".format(store.rm_test_day)

    def rm_test_turn_text():
        return RM_TEST_TURNS[store.rm_test_turn_index][0]

    def rm_test_sync_clock():
        store.day_count = store.rm_test_day
        store.current_time_minutes = RM_TEST_TURNS[store.rm_test_turn_index][1]
        if getattr(store, "rm_player", None) is not None:
            store.rm_player.day = int(store.rm_test_day)
            store.rm_player.weekday = 1 + ((int(store.rm_test_day) - 1) % 7)

    def rm_test_start_flow():
        store.rm_test_flow_active = True
        store.rm_test_day = 101
        store.rm_test_turn_index = 0
        store.rm_test_last_result_text = ""
        store.rm_player = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=renpy.random)
        store.story_hud_status_unlocked = True
        store.story_hud_character_panel_unlocked = True
        rm_test_sync_clock()
        renpy.restart_interaction()

    def rm_test_prepare_growth_reward_test(attr="str"):
        character = rm_ensure_player()
        rm_core.add_growth_reward_pending(character, attr, 1)
        return rm_test_pending_card_request(character)

    def rm_test_advance_turn(schedule_id=None):
        if schedule_id == "test_sleep" or store.rm_test_turn_index >= len(RM_TEST_TURNS) - 1:
            store.rm_test_day += 1
            store.rm_test_turn_index = 0
        else:
            store.rm_test_turn_index += 1
        rm_test_sync_clock()

    def rm_test_schedule_names():
        return {
            "test_rest": "休息（测试）",
            "test_sleep": "睡觉（测试）",
            "test_strength_training": "力量训练（测试）",
            "test_dex_training": "灵巧训练（测试）",
            "test_jogging": "慢跑（测试）",
        }

    def rm_test_is_daytime_turn():
        return store.rm_test_turn_index in (0, 1, 2, 3)

    def rm_test_is_deep_night_turn():
        return store.rm_test_turn_index == len(RM_TEST_TURNS) - 1

    def rm_test_schedule_available(schedule_id):
        if schedule_id == "test_rest":
            return not rm_test_is_deep_night_turn()
        if schedule_id == "test_sleep":
            return rm_test_is_deep_night_turn()
        return True

    def rm_test_schedule_unavailable_text(schedule_id):
        if schedule_id == "test_rest":
            return "休息（测试）只能在深夜以外使用。"
        if schedule_id == "test_sleep":
            return "睡觉（测试）只能在深夜使用。"
        return "当前时间不能使用该日程。"

    def rm_test_schedule_uses_check(schedule_id):
        return schedule_id in ("test_strength_training", "test_dex_training", "test_jogging")

    def rm_test_check_attribute(schedule_id):
        """Return the mock check attribute for a test schedule."""
        mapping = {
            "test_rest": "con",
            "test_sleep": "pow",
            "test_strength_training": "str",
            "test_dex_training": "dex",
            "test_jogging": "con",
        }
        if schedule_id not in mapping:
            raise ValueError("Unknown test schedule: {!r}".format(schedule_id))
        return mapping[schedule_id]

    def rm_test_allowed_die_attributes(schedule_id):
        if schedule_id == "test_jogging":
            return ("con", "dex", "str")
        return (rm_test_check_attribute(schedule_id),)

    def rm_test_required_die_attributes(schedule_id):
        if schedule_id == "test_jogging":
            return ("con",)
        return ()

    def rm_test_check_requirement(schedule_id, character=None):
        """Return the mock target number for a test schedule."""
        character = character or rm_ensure_player()
        if schedule_id in ("test_strength_training", "test_dex_training", "test_jogging"):
            return rm_core.test_training_requirement_for_schedule(character, schedule_id, rng=renpy.random)
        attribute = rm_test_check_attribute(schedule_id)
        return int(character.formal_attributes.get(attribute, 0))

    def rm_test_result_dict_for_schedule(result, character, dice_ids, schedule_id):
        attribute = result.attribute if result is not None else rm_test_check_attribute(schedule_id)
        selected_ids = normalize_attribute_die_ids(dice_ids)
        result_ids = list(result.dice_ids) if result is not None and result.dice_ids else selected_ids
        dice = [character.find_die(die_id) for die_id in result_ids]
        dice = [die for die in dice if die is not None]
        first_die = dice[0] if dice else None
        die_faces = tuple(first_die.faces) if first_die else ()
        rolls = tuple(item["value"] for item in result.dice_results) if result.dice_results else ()
        roll_value = rolls[0] if rolls else None
        return {
            "_result": result,
            "schedule_id": schedule_id,
            "available": result.available,
            "reason": result.reason,
            "stat": attribute,
            "stat_label": rm_core.ATTRIBUTE_LABELS[attribute],
            "stat_value": rm_core.effective_attribute(character, attribute),
            "stat_half": result.attribute_modifier,
            "die_id": first_die.id if first_die else (selected_ids[0] if selected_ids else None),
            "die_ids": tuple(result_ids),
            "die_label": " + ".join("{} d{}".format(rm_core.ATTRIBUTE_LABELS[die.attribute], len(die.faces)) for die in dice) if dice else "",
            "die_faces": die_faces,
            "die_sides": len(die_faces),
            "die_faces_text": " / ".join(format_die_faces(die.faces) for die in dice) if dice else "",
            "rolls": rolls,
            "mood_modifier": result.extra_modifier,
            "dice_total": result.dice_total,
            "total": result.total,
            "success_threshold": result.requirement,
            "success": result.success,
            "rank": result.rank,
            "roll_value": roll_value,
        }

    def rm_test_perform_schedule_check(schedule_id, dice_ids, requirement=None):
        character = rm_ensure_player()
        attribute = rm_test_check_attribute(schedule_id)
        if requirement is None:
            requirement = rm_test_check_requirement(schedule_id, character)
        selected_ids = normalize_attribute_die_ids(dice_ids)
        spec = rm_core.CheckSpec(
            attribute,
            requirement,
            dice_ids=selected_ids,
            action_type=rm_core.ACTION_SCHEDULE,
            big_failure_slack=rm_core.training_fatigue_big_failure_slack(character, schedule_id),
            allowed_dice_attributes=rm_test_allowed_die_attributes(schedule_id),
            required_dice_attributes=rm_test_required_die_attributes(schedule_id),
        )
        result = rm_core.perform_check(character, spec, rng=renpy.random)
        return rm_test_result_dict_for_schedule(result, character, selected_ids, schedule_id)

    def rm_test_apply_schedule_effect(schedule_id, result, character=None):
        character = character or rm_ensure_player()
        events = []
        if schedule_id == "test_jogging":
            applied = rm_core.apply_test_exercise_schedule_result(character, schedule_id, result, rng=renpy.random)
            bonus = applied.get("bonus") or {}
            for attribute in bonus.get("granted_attributes", []):
                events.append("test_training_bonus:{}".format(attribute))
        elif schedule_id in ("test_strength_training", "test_dex_training"):
            applied = rm_core.apply_test_training_schedule_result(character, schedule_id, result, rng=renpy.random)
            bonus = applied.get("bonus") or {}
            for _index in range(int(bonus.get("success_count", 0))):
                events.append("test_training_bonus:{}".format(rm_core.test_training_schedule_attribute(schedule_id)))
        elif schedule_id == "test_rest":
            rest = rm_core.resolve_test_day_rest(character, rng=renpy.random)
            events.extend(rest.get("events", []))
        elif schedule_id == "test_sleep":
            sleep = rm_core.resolve_test_sleep(character, rng=renpy.random)
            events.extend(sleep.get("events", []))
        else:
            raise ValueError("Unknown test schedule: {!r}".format(schedule_id))
        return events

    def rm_test_execute_rest_schedule(schedule_id, character=None):
        character = character or rm_ensure_player()
        name = rm_test_schedule_names()[schedule_id]
        if not rm_test_schedule_available(schedule_id):
            store.rm_test_last_result_text = "{}无法执行。{}".format(name, rm_test_schedule_unavailable_text(schedule_id))
            return {"schedule_id": schedule_id, "name": name, "available": False, "events": []}
        if schedule_id == "test_rest":
            result = rm_core.resolve_test_day_rest(character, rng=renpy.random)
        elif schedule_id == "test_sleep":
            result = rm_core.resolve_test_sleep(character, rng=renpy.random)
        else:
            raise ValueError("Schedule must use the check flow: {!r}".format(schedule_id))
        events = result.get("events", [])
        turn = rm_core.end_action_round(character, 0, rng=renpy.random, exact_mood_delta=True)
        store.rm_test_last_result_text = "{}完成。{} 本轮事件：{}。".format(
            name,
            rm_test_rest_result_text(schedule_id, result),
            rm_test_event_text(events),
        )
        return {"schedule_id": schedule_id, "name": name, "rest": result, "turn": turn, "events": events}

    def rm_test_rest_result_text(schedule_id, result):
        if not result.get("available", False):
            return "无法执行：{}。".format(result.get("reason", "unknown"))
        if schedule_id == "test_rest":
            roll = result.get("roll", {})
            return "随机体质骰 {} 掷出 {}，恢复 {} 点精力。".format(
                result.get("die_id", ""),
                roll.get("value", 0),
                result.get("restored", 0),
            )
        if schedule_id == "test_sleep":
            return "深夜睡觉，精力恢复至 {}/{}。".format(result.get("energy_after", 0), rm_core.energy_max(rm_ensure_player()))
        return ""

    def rm_test_event_text(events):
        """Translate backend event ids into readable test-flow settlement text."""
        if not events:
            return "无"
        texts = []
        for event in events:
            if event == "small_rest":
                texts.append("小休结算")
            elif event == "large_rest":
                texts.append("大休结算")
            elif event == "sleep":
                texts.append("睡眠结算")
            elif event == "sleep_recovery":
                texts.append("睡眠 Mood 恢复")
            elif event == "day_rest":
                texts.append("白天休息")
            elif event.startswith("energy_restored:"):
                texts.append("精力恢复 +{}".format(event.split(":", 1)[1]))
            elif event.startswith("energy_full:"):
                texts.append("精力完全恢复")
            elif event.startswith("test_training_bonus:"):
                attr = event.split(":", 1)[1]
                texts.append("{}属性加成 +1".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("test_strength_bonus:"):
                continue
            elif event.startswith("fatigue_reduced:"):
                parts = event.split(":")
                label = rm_core.TEST_TRAINING_SCHEDULE_LABELS.get(parts[1], parts[1])
                texts.append("疲劳：{} -1（剩余{}）".format(label, parts[2]))
            elif event.startswith("fatigue_cleared:"):
                schedule_id = event.split(":", 1)[1]
                label = rm_core.TEST_TRAINING_SCHEDULE_LABELS.get(schedule_id, schedule_id)
                texts.append("疲劳：{} 清空".format(label))
            elif event.startswith("bonus_to_value:"):
                attr = event.split(":", 1)[1]
                texts.append("{}属性加成转化为属性加值".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("bonus_lost:"):
                attr = event.split(":", 1)[1]
                texts.append("{}属性加成消失".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("growth_reward_pending:"):
                attr = event.split(":", 1)[1]
                texts.append("{}骰子成长奖励 +1".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("degradation_penalty_pending:"):
                attr = event.split(":", 1)[1]
                texts.append("{}骰子退化惩罚 +1".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("value_to_formal:"):
                attr = event.split(":", 1)[1]
                texts.append("{}属性加值转化为正式属性".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            elif event.startswith("value_lost:"):
                attr = event.split(":", 1)[1]
                texts.append("{}属性加值退化".format(rm_core.ATTRIBUTE_LABELS.get(attr, attr)))
            else:
                texts.append(str(event))
        return "；".join(texts)

    def rm_test_finalize_schedule_check(schedule_id, result_dict, character=None):
        character = character or rm_ensure_player()
        result = result_dict.get("_result")
        events = rm_test_apply_schedule_effect(schedule_id, result, character)
        mood_delta = 10 if result_dict.get("available") and result_dict.get("success") else -10
        turn = rm_core.end_action_round(character, mood_delta, rng=renpy.random, exact_mood_delta=True)
        name = rm_test_schedule_names()[schedule_id]
        event_text = rm_test_event_text(events)
        store.rm_test_last_result_text = "{}完成。{} 本轮事件：{}。".format(
            name,
            rm_test_check_text(result) if result is not None else "",
            event_text,
        )
        return {"schedule_id": schedule_id, "name": name, "check": result, "turn": turn, "events": events}

    def rm_test_check_text(result):
        if result is None:
            return ""
        if not result.available:
            return "检定无法执行：{}。".format(result.reason)
        return "检定结果：{}，总值 {} / 目标 {}，Mood变化按成败结算。".format(
            result.rank,
            result.total,
            result.requirement,
        )

    def rm_test_result_dict(result, character, die_id):
        die = character.find_die(die_id)
        die_faces = tuple(die.faces) if die else ()
        dice_result = result.dice_results[0] if result.dice_results else None
        roll_value = dice_result["value"] if dice_result else None
        rolls = tuple(dice_result["rolls"][-1:]) if dice_result else ()
        return {
            "_result": result,
            "available": result.available,
            "reason": result.reason,
            "stat": "str",
            "stat_label": rm_core.ATTRIBUTE_LABELS["str"],
            "stat_value": rm_core.effective_attribute(character, "str"),
            "stat_half": result.attribute_modifier,
            "die_id": die_id,
            "die_label": "{} d{}".format(rm_core.ATTRIBUTE_LABELS["str"], len(die_faces)) if die else die_id,
            "die_faces": die_faces,
            "die_sides": len(die_faces),
            "die_faces_text": format_die_faces(die_faces),
            "rolls": rolls,
            "mood_modifier": result.extra_modifier,
            "total": result.total,
            "success_threshold": result.requirement,
            "success": result.success,
            "rank": result.rank,
            "roll_value": roll_value,
        }

    def rm_test_perform_strength_training_check(die_id):
        character = rm_ensure_player()
        requirement = rm_core.test_strength_training_requirement(character)
        spec = rm_core.CheckSpec("str", requirement, dice_ids=[die_id], action_type=rm_core.ACTION_SCHEDULE)
        result = rm_core.perform_check(character, spec, rng=renpy.random)
        return rm_test_result_dict(result, character, die_id)

    def rm_test_finalize_strength_training(result_dict, character=None):
        character = character or rm_ensure_player()
        result = result_dict.get("_result")
        if result is not None:
            rm_core.apply_test_strength_training_result(character, result, rng=renpy.random)
        mood_delta = 10 if result_dict.get("available") and result_dict.get("success") else -10
        turn = rm_core.end_action_round(character, mood_delta, rng=renpy.random, exact_mood_delta=True)
        store.rm_test_last_result_text = "{}完成。{} 本轮事件：无。".format(
            rm_test_schedule_names()["test_strength_training"],
            rm_test_check_text(result) if result is not None else "",
        )
        return {
            "schedule_id": "test_strength_training",
            "name": rm_test_schedule_names()["test_strength_training"],
            "check": result,
            "turn": turn,
            "events": [],
        }

    def rm_test_execute_schedule(schedule_id, character=None):
        if rm_test_schedule_uses_check(schedule_id):
            raise ValueError("Schedule must use the interactive dice check flow: {!r}".format(schedule_id))
        return rm_test_execute_rest_schedule(schedule_id, character)
        character = character or rm_ensure_player()
        result = None
        events = []
        mood_delta = 0

        if schedule_id == "test_rest":
            events.extend(rm_core.resolve_test_rest(character))
            character.energy = min(rm_core.energy_max(character), character.energy + 2)
        elif schedule_id == "test_sleep":
            character.energy = rm_core.energy_max(character)
        elif schedule_id == "test_strength_training":
            raise ValueError("Strength training must use the interactive dice check flow.")
        else:
            raise ValueError("Unknown test schedule: {!r}".format(schedule_id))

        turn = rm_core.end_action_round(character, mood_delta, rng=renpy.random, exact_mood_delta=True)
        name = rm_test_schedule_names()[schedule_id]
        event_text = "；".join(events) if events else "无"
        store.rm_test_last_result_text = "{}完成。{} 本轮事件：{}。".format(
            name,
            rm_test_check_text(result),
            event_text,
        )
        return {"schedule_id": schedule_id, "name": name, "check": result, "turn": turn, "events": events}

    def rm_test_pending_card_request(character=None):
        """Return the next pending dice reward/penalty card request for test flow."""
        character = character or rm_ensure_player()
        for attr in rm_core.pending_growth_reward_attrs(character):
            return {
                "mode": "growth",
                "attr": attr,
                "cards": rm_core.draw_pending_growth_reward_cards(character, attr, 3, rng=renpy.random),
            }
        for attr in rm_core.pending_degradation_penalty_attrs(character):
            return {
                "mode": "degradation",
                "attr": attr,
                "cards": rm_core.draw_pending_degradation_penalty_cards(character, attr, 3, rng=renpy.random),
            }
        return None

    def rm_test_pending_card_title(request):
        attr = request.get("attr")
        attr_label = rm_core.ATTRIBUTE_LABELS.get(attr, attr)
        if request.get("mode") == "growth":
            return "{}骰子成长奖励".format(attr_label)
        return "{}骰子退化惩罚".format(attr_label)

    def rm_test_card_label(card):
        return rm_core.card_label(card)

    def rm_test_card_description(card):
        return rm_core.card_description(card)

    def rm_test_card_needs_die_choice(card):
        return rm_core.card_needs_die_choice(card)

    def rm_test_card_needs_face_choice(card):
        return rm_core.card_needs_face_choice(card)

    def rm_test_pending_dice_choices(request, card=None, character=None):
        character = character or rm_ensure_player()
        attr = request.get("attr")
        dice = list(character.dice_for(attr))
        if card and card.get("type") in ("clear_negative_enchant", "convert_negative_enchant"):
            dice = [die for die in dice if die.enchantment in rm_core.NEGATIVE_ENCHANTMENTS]
        return [rm_core.dice_summary(die) for die in dice]

    def rm_test_pending_face_choices(die_id, character=None):
        character = character or rm_ensure_player()
        die = character.find_die(die_id)
        if die is None:
            return []
        return [{"index": index, "value": value} for index, value in enumerate(die.faces)]

    def rm_test_apply_card_selection(card, die_id=None, face_index=None):
        selected = dict(card)
        if die_id is not None:
            selected["die_id"] = die_id
        if face_index is not None:
            selected["face_index"] = int(face_index)
        return selected

    def rm_test_apply_pending_card(request, card, character=None):
        character = character or rm_ensure_player()
        attr = request.get("attr")
        if request.get("mode") == "growth":
            result = rm_core.apply_pending_growth_reward(character, attr, card, rng=renpy.random)
            kind = "奖励"
        else:
            result = rm_core.apply_pending_degradation_penalty(character, attr, card, rng=renpy.random)
            kind = "惩罚"
        return "{}{}：{}，结果={}".format(
            rm_core.ATTRIBUTE_LABELS.get(attr, attr),
            kind,
            rm_core.card_label(card),
            "已应用" if result.get("applied") else "未应用",
        )

    def rm_test_console_adjust_mood(delta):
        rm_core.test_console_adjust_mood(rm_ensure_player(), delta)
        renpy.restart_interaction()
        return None

    def rm_test_console_set_mood_state(state):
        rm_core.test_console_set_mood_state(rm_ensure_player(), state)
        renpy.restart_interaction()
        return None

    def rm_test_console_adjust_formal_attribute(attribute, delta):
        rm_core.test_console_adjust_formal_attribute(rm_ensure_player(), attribute, delta)
        renpy.restart_interaction()
        return None

    def rm_test_console_adjust_attribute_value(attribute, delta):
        rm_core.test_console_adjust_attribute_value(rm_ensure_player(), attribute, delta)
        renpy.restart_interaction()
        return None

    def rm_test_console_adjust_attribute_bonus(attribute, delta):
        rm_core.test_console_adjust_attribute_bonus(rm_ensure_player(), attribute, delta)
        renpy.restart_interaction()
        return None


screen rm_test_schedule_select():
    modal True
    zorder 210

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "rm_test_schedule_frame"

        vbox:
            spacing 16
            xfill True

            text "选择日程" style "rm_test_schedule_title_text"
            text "当前时间：[rm_test_day_text()] [rm_test_turn_text()]" style "rm_test_schedule_hint_text"

            textbutton "休息（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_rest")
                action Return("test_rest")

            textbutton "睡觉（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_sleep")
                action Return("test_sleep")

            textbutton "力量训练（测试）":
                style "rm_test_schedule_button"
                action Return("test_strength_training")

            textbutton "灵巧训练（测试）":
                style "rm_test_schedule_button"
                action Return("test_dex_training")

            textbutton "慢跑（测试）":
                style "rm_test_schedule_button"
                action Return("test_jogging")


screen rm_test_pending_card_choice(request):
    modal True
    zorder 215

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "rm_test_schedule_frame"

        vbox:
            spacing 16
            xfill True

            text "[rm_test_pending_card_title(request)]" style "rm_test_schedule_title_text"
            text "选择一张卡并立即结算。" style "rm_test_schedule_hint_text"

            hbox:
                spacing 18
                xalign 0.5

                for card in request.get("cards", []):
                    button:
                        style "rm_test_reward_card_button"
                        action Return(card)

                        vbox:
                            spacing 12
                            xfill True
                            text "[rm_test_card_label(card)]" style "rm_test_reward_card_title_text"
                            text "[rm_test_card_description(card)]" style "rm_test_reward_card_description_text"


screen rm_test_pending_die_choice(request, card=None):
    modal True
    zorder 216

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "rm_test_schedule_frame"

        vbox:
            spacing 16
            xfill True

            text "选择骰子" style "rm_test_schedule_title_text"
            text "[rm_test_pending_card_title(request)]" style "rm_test_schedule_hint_text"

            for die in rm_test_pending_dice_choices(request, card):
                textbutton "[die['label']] [die['id']]  [die['faces_text']]":
                    style "rm_test_schedule_button"
                    action Return(die["id"])


screen rm_test_pending_face_choice(die_id):
    modal True
    zorder 217

    use rm_allow_game_menu
    use modal_dim_background

    frame:
        style "rm_test_schedule_frame"

        vbox:
            spacing 16
            xfill True

            text "选择面值" style "rm_test_schedule_title_text"

            for face in rm_test_pending_face_choices(die_id):
                textbutton "第[face['index'] + 1]面：[face['value']]":
                    style "rm_test_schedule_button"
                    action Return(face["index"])


style rm_test_schedule_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 520
    background "#eee7d8f4"
    padding (30, 28)

style rm_test_schedule_title_text is gui_text:
    size 34
    bold True
    color "#171513"

style rm_test_schedule_hint_text is gui_text:
    size 22
    color "#5c554e"

style rm_test_schedule_button is button:
    xfill True
    ysize 56
    background "#d9cdbb"
    hover_background "#eadfcc"
    padding (18, 0)

style rm_test_schedule_button_text is button_text:
    size 24
    color "#171513"
    hover_color "#000000"
    yalign 0.5

style rm_test_reward_card_button is button:
    xsize 300
    ysize 260
    background "#f7f0e4"
    hover_background "#fff2d8"
    padding (20, 18)

style rm_test_reward_card_title_text is gui_text:
    size 26
    bold True
    color "#171513"

style rm_test_reward_card_description_text is gui_text:
    size 20
    color "#4d453e"
    line_spacing 4
