default rm_test_flow_active = False
default rm_test_day = 101
default rm_test_turn_index = 0
default rm_test_last_result_text = ""
default rm_test_training_location = "gym"

init -9 python:
    RM_TEST_TURNS = (
        ("上午1", 8 * 60),
        ("上午2", 10 * 60),
        ("下午1", 13 * 60),
        ("下午2", 15 * 60),
        ("晚上1", 18 * 60),
        ("晚上2", 20 * 60),
        # Existing test-clock timestamps only; final night timestamps are not designed yet.
        ("深夜1", 23 * 60),
        ("深夜2", 23 * 60),
        ("深夜3", 23 * 60),
    )

    def rm_test_day_text():
        return "第{}天".format(store.rm_test_day)

    def rm_test_turn_text():
        return rm_core.TIME_SLOT_LABELS.get(rm_ensure_player().current_time_slot, "")

    def rm_test_sync_clock():
        player = rm_ensure_player()
        rm_core.ensure_second_stage_state(player)
        if player.current_time_slot is None and store.rm_test_flow_active:
            # Old test saves only stored a separate seven-round index.
            rm_core.start_turn(player, rm_core.TIME_SLOTS[min(store.rm_test_turn_index, 8)])
        store.rm_test_day = player.day
        store.rm_test_turn_index = player.time_slot_index
        slot = player.current_time_slot
        clock_slot = {"breakfast": "morning_1", "lunch": "afternoon_1", "dinner": "evening_1",
                      "sleep_decision": "evening_2", "night_break_1": "late_night_1",
                      "night_break_2": "late_night_2", "forced_sleep": "late_night_3",
                      "wake_check": "morning_1"}.get(slot, slot)
        if clock_slot in rm_core.TIME_SLOTS:
            store.current_time_minutes = RM_TEST_TURNS[rm_core.TIME_SLOTS.index(clock_slot)][1]

    def rm_test_start_flow():
        store.rm_test_flow_active = True
        store.rm_test_day = 101
        store.rm_test_turn_index = 0
        store.rm_test_last_result_text = ""
        store.rm_test_training_location = "gym"
        store.rm_player = rm_core.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=renpy.random)
        store.rm_player.day = 101
        store.rm_player.weekday = 3
        rm_core.start_day(store.rm_player)
        store.story_hud_status_unlocked = True
        store.story_hud_character_panel_unlocked = True
        rm_test_sync_clock()
        renpy.restart_interaction()

    def rm_test_prepare_growth_reward_test(attr="str"):
        character = rm_ensure_player()
        rm_core.add_growth_reward_pending(character, attr, 1)
        return rm_test_pending_card_request(character)

    def rm_test_advance_turn(schedule_id=None):
        if schedule_id != "test_sleep":
            rm_core.advance_time_slot(rm_ensure_player())
        rm_test_sync_clock()

    def rm_test_schedule_names():
        return {
            "test_rest": "休息（测试）",
            "test_sleep": "睡觉（测试）",
            "test_strength_training": "负重训练（测试）",
            "test_dex_training": "协调训练（测试）",
            "test_jogging": "慢跑（测试）",
        }

    def rm_test_is_daytime_turn():
        return rm_ensure_player().current_time_slot in rm_core.TIME_SLOTS[:4]

    def rm_test_is_deep_night_turn():
        return rm_ensure_player().current_time_slot in rm_core.TIME_SLOTS[6:]

    def rm_test_schedule_available(schedule_id):
        player = rm_ensure_player()
        slot = player.current_time_slot
        if schedule_id != "test_sleep" and slot not in rm_core.TIME_SLOTS:
            return False
        if schedule_id in rm_core.TEST_TRAINING_SCHEDULE_ATTRIBUTES:
            return rm_core.training_schedule_legal(player, schedule_id, store.rm_test_training_location, slot)[0]
        if schedule_id == "test_sleep":
            return slot in rm_core.SLEEP_DECISIONS + ("forced_sleep",)
        if schedule_id == "test_rest":
            return not rm_test_is_deep_night_turn()
        return True

    def rm_test_schedule_unavailable_text(schedule_id):
        if schedule_id in rm_core.TEST_TRAINING_SCHEDULE_ATTRIBUTES:
            reason = rm_core.training_schedule_legal(rm_ensure_player(), schedule_id,
                store.rm_test_training_location)[1]
            return {"gym_closed": "深夜健身房关闭。", "training_not_available_in_park": "公园只能慢跑。",
                "severe_weather_blocks_outdoors": "恶劣天气不能在公园训练。",
                "equipment_required": "家中缺少该训练所需设备。"}.get(reason, "当前地点不能执行该训练。")
        if schedule_id == "test_rest":
            return "休息（测试）只能在深夜以外使用。"
        if schedule_id == "test_sleep":
            return "晚上2结束后或深夜行动间可以睡觉。第三轮深夜结束会强制昏迷。"
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

    def rm_test_bonus_reroll_count(schedule_id, dice_ids):
        character = rm_ensure_player()
        spec = rm_core.CheckSpec(rm_test_check_attribute(schedule_id), 1,
            dice_ids=dice_ids, action_type=rm_core.ACTION_SCHEDULE, sport=True,
            location=store.rm_test_training_location,
            outdoors=store.rm_test_training_location == "park")
        weather = rm_core.weather_check_effects(character, spec)
        dice = [character.find_die(die_id) for die_id in dice_ids]
        bonus, penalty = rm_core.check_advantage_counts(character, spec, weather, dice)
        return max(0, bonus - penalty)

    def rm_test_perform_schedule_check(schedule_id, dice_ids, requirement=None, bonus_die_ids=None):
        character = rm_ensure_player()
        legal, reason = rm_core.training_schedule_legal(character, schedule_id, store.rm_test_training_location)
        if not legal:
            return rm_test_result_dict_for_schedule(rm_core.unavailable_result(
                rm_core.CheckSpec(rm_test_check_attribute(schedule_id), requirement or 1), reason),
                character, dice_ids, schedule_id)
        attribute = rm_test_check_attribute(schedule_id)
        if requirement is None:
            requirement = rm_test_check_requirement(schedule_id, character)
        selected_ids = normalize_attribute_die_ids(dice_ids)
        spec = rm_core.CheckSpec(
            attribute,
            requirement,
            dice_ids=selected_ids,
            action_type=rm_core.ACTION_SCHEDULE,
            is_late_night=rm_test_is_deep_night_turn(),
            big_failure_slack=rm_core.training_fatigue_big_failure_slack(character, schedule_id),
            allowed_dice_attributes=rm_test_allowed_die_attributes(schedule_id),
            required_dice_attributes=rm_test_required_die_attributes(schedule_id),
            sport=True,
            outdoors=store.rm_test_training_location == "park",
            location=store.rm_test_training_location,
            bonus_die_ids=bonus_die_ids,
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

    def rm_test_execute_rest_schedule(schedule_id, character=None, bonus_die_ids=None):
        character = character or rm_ensure_player()
        name = rm_test_schedule_names()[schedule_id]
        if not rm_test_schedule_available(schedule_id):
            store.rm_test_last_result_text = "{}无法执行。{}".format(name, rm_test_schedule_unavailable_text(schedule_id))
            return {"schedule_id": schedule_id, "name": name, "available": False, "events": []}
        if schedule_id == "test_rest":
            result = rm_core.resolve_test_day_rest(character, rng=renpy.random)
        elif schedule_id == "test_sleep":
            result = rm_core.resolve_test_sleep(character, rng=renpy.random, bonus_die_ids=bonus_die_ids)
        else:
            raise ValueError("Schedule must use the check flow: {!r}".format(schedule_id))
        events = result.get("events", [])
        if not result.get("available", False):
            store.rm_test_last_result_text = "{}无法执行，不消耗行动轮。".format(name)
            return {"available": False, "events": events}
        turn = (rm_core.end_action_round(character, 0, rng=renpy.random, exact_mood_delta=True)
                if schedule_id == "test_rest" else None)
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
            return "睡眠结算，精力恢复至 {}/{}。".format(result.get("energy_after", 0), rm_core.energy_max(rm_ensure_player()))
        return ""

    def rm_test_event_text(events):
        """Translate backend event ids into readable test-flow settlement text."""
        if not events:
            return "无"
        texts = []
        for event in events:
            if event == "death":
                texts.append("生命值归零，角色死亡")
            elif event.startswith("health_restored:"):
                texts.append("小休恢复生命 +{}".format(event.split(":", 1)[1]))
            elif event == "sleep_fatigue_cleared":
                texts.append("按时睡觉，清除疲劳")
            elif event == "drowsiness_cleared":
                texts.append("按时睡觉，清除困意")
            elif event.startswith("drowsiness_reduced:"):
                texts.append("困意减少 {} 层".format(event.rsplit(":", 1)[1]))
            elif event == "deep_fatigue_started":
                texts.append("近七天内三次获得疲劳，引发深度疲劳")
            elif event == "deep_fatigue_recovered":
                texts.append("深度疲劳康复；健康作息重新累计")
            elif event.startswith("deep_fatigue_permanent_loss:"):
                texts.append("深度疲劳结算：永久体质 -{}，并结算相应骰子退化".format(event.rsplit(":", 1)[1]))
            elif event.startswith("deep_fatigue_added:"):
                texts.append("熬夜加重深度疲劳，现为 {} 层".format(event.rsplit(":", 1)[1]))
            elif event == "small_rest":
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
        if result is None or not result.available:
            store.rm_test_last_result_text = "检定无法执行，不消耗行动轮。"
            return {"available": False, "events": []}
        events = rm_test_apply_schedule_effect(schedule_id, result, character)
        turn = rm_core.end_action_round(character, 0, rng=renpy.random, check=result)
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
        spec = rm_core.CheckSpec("str", requirement, dice_ids=[die_id], action_type=rm_core.ACTION_SCHEDULE, sport=True)
        result = rm_core.perform_check(character, spec, rng=renpy.random)
        return rm_test_result_dict(result, character, die_id)

    def rm_test_finalize_strength_training(result_dict, character=None):
        character = character or rm_ensure_player()
        result = result_dict.get("_result")
        if result is not None:
            rm_core.apply_test_strength_training_result(character, result, rng=renpy.random)
        turn = rm_core.end_action_round(character, 0, rng=renpy.random, check=result)
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
        if card:
            dice = rm_core.growth_reward_dice_candidates(character, attr, card)
        return [rm_core.dice_summary(die) for die in dice]

    def rm_test_pending_face_choices(die_id, character=None, card=None):
        character = character or rm_ensure_player()
        die = character.find_die(die_id)
        if die is None:
            return []
        return [{"index": index, "value": die.faces[index]}
                for index in rm_core.growth_reward_face_indices(die, card or {})]

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
            spacing 21
            xfill True

            text "选择日程" style "rm_test_schedule_title_text"
            text "当前时间：[rm_test_day_text()] [rm_test_turn_text()]" style "rm_test_schedule_hint_text"
            textbutton ("训练地点：" + {"gym": "健身房", "park": "公园", "home": "家"}[rm_test_training_location]):
                style "rm_test_schedule_button"
                action SetVariable("rm_test_training_location", {"gym": "park", "park": "home", "home": "gym"}[rm_test_training_location])

            textbutton "休息（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_rest")
                action Return("test_rest")

            if rm_test_schedule_available("test_sleep"):
                textbutton "睡觉（测试）":
                    style "rm_test_schedule_button"
                    sensitive rm_test_schedule_available("test_sleep")
                    action Return("test_sleep")

            textbutton "负重训练（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_strength_training")
                action Return("test_strength_training")

            textbutton "协调训练（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_dex_training")
                action Return("test_dex_training")

            textbutton "慢跑（测试）":
                style "rm_test_schedule_button"
                sensitive rm_test_schedule_available("test_jogging")
                action Return("test_jogging")

    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()


# These screens only return a confirmed choice. The existing flow owns application.
screen rm_test_pending_card_choice(request):
    modal True
    zorder 215
    default selected_card = None
    use rm_allow_game_menu
    use modal_dim_background
    if selected_card is not None:
        key "game_menu" action SetScreenVariable("selected_card", None)
    frame:
        style "attribute_check_panel"
        fixed:
            text rm_test_pending_card_title(request) style "attribute_check_title"
            text "先选择一项，再确认；选择期间不会消耗待结算次数。" style "attribute_check_muted_text" ypos 90
            hbox:
                ypos 188 spacing 24
                for index, card in enumerate(request.get('cards', [])):
                    button:
                        id ("growth_card_"+str(index))
                        style "attribute_check_choice"
                        xysize (628,510)
                        selected selected_card == index
                        action SetScreenVariable("selected_card", index)
                        vbox:
                            spacing 30 xfill True
                            text rm_test_card_label(card) style "attribute_check_section_title"
                            text rm_test_card_description(card) style "attribute_check_body"
                            text ("已选" if selected_card == index else "点击选择") style "attribute_check_hint_text"
            vbox:
                ypos 750 spacing 18 xsize 1936
                if selected_card is not None:
                    $ card = request['cards'][selected_card]
                    text ("已选："+rm_test_card_label(card)) style "attribute_check_section_title"
                    text ("下一步选择目标骰子；仍未应用奖励。" if rm_test_card_needs_die_choice(card) else "确认后立即结算这一项；含随机结果的部分在结算时确定。") style "attribute_check_muted_text"
                else:
                    text "选择上方一项以查看确认步骤。" style "attribute_check_muted_text"
            add Solid("#b4aa96") ypos 958 xysize (1936,2)
            if selected_card is not None:
                textbutton "取消选择" id "growth_clear" style "attribute_check_tab_button" ypos 984 xsize 240 action SetScreenVariable("selected_card", None)
            textbutton ("下一步：选择骰子" if selected_card is not None and rm_test_card_needs_die_choice(request['cards'][selected_card]) else "确认并应用"):
                id "growth_confirm"
                style "attribute_check_button"
                xpos 1456 ypos 984 xsize 480
                sensitive selected_card is not None
                action Return(request['cards'][selected_card] if selected_card is not None else None)
    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()

screen rm_test_pending_die_choice(request, card=None):
    modal True
    zorder 216
    default selected_die = None
    use rm_allow_game_menu
    use modal_dim_background
    $ candidates = rm_test_pending_dice_choices(request, card)
    $ display_rows = {d['id']: d for d in rm_dice_view.rows(rm_ensure_player())}
    if selected_die is not None:
        key "game_menu" action SetScreenVariable("selected_die", None)
    frame:
        style "attribute_check_panel"
        fixed:
            text "选择目标骰子" style "attribute_check_title"
            text rm_test_pending_card_title(request) style "attribute_check_muted_text" ypos 90
            vpgrid:
                ypos 188 xysize (1120,714)
                cols 1 spacing 16 mousewheel True draggable True scrollbars "vertical"
                vscrollbar_xsize 10
                vscrollbar_base_bar "#dfd7c8"
                vscrollbar_thumb "#9c8d70"
                vscrollbar_hover_thumb "#6c6048"
                vscrollbar_unscrollable "hide"
                for die in candidates:
                    $ row = display_rows[die['id']]
                    button:
                        id ("growth_die_"+die['id'])
                        style "attribute_check_choice"
                        xysize (1080,194)
                        selected selected_die == die['id']
                        action SetScreenVariable("selected_die", die['id'])
                        vbox:
                            spacing 12
                            text ("{} D{} · {:02d}  /  {}".format(row['label'], row['sides'], row['serial'], row['enchantment_label'])) style "attribute_check_section_title"
                            text die['faces_text'] style "attribute_check_body"
            add Solid("#b4aa96") xpos 1192 ypos 188 xysize (1,714)
            vbox:
                xpos 1232 ypos 188 spacing 30 xsize 704
                if card:
                    text rm_test_card_label(card) style "attribute_check_section_title"
                    text rm_test_card_description(card) style "attribute_check_body"
                if selected_die is not None:
                    $ chosen = rm_ensure_player().find_die(selected_die)
                    text "变化预览" style "attribute_check_section_title"
                    text rm_dice_view.growth_comparison(chosen, card or {}) style "attribute_check_body" id "growth_comparison"
                    text ("下一步选择具体骰面。" if card and rm_test_card_needs_face_choice(card) else "确认后才会应用到这颗骰子。") style "attribute_check_muted_text"
                else:
                    text "从左侧选择一颗骰子。只列出符合条件的目标。" style "attribute_check_muted_text"
            add Solid("#b4aa96") ypos 958 xysize (1936,2)
            if selected_die is not None:
                textbutton "取消选择" id "growth_clear" style "attribute_check_tab_button" ypos 984 xsize 240 action SetScreenVariable("selected_die", None)
            textbutton ("下一步：选择骰面" if card and rm_test_card_needs_face_choice(card) else "确认并应用"):
                id "growth_confirm"
                style "attribute_check_button"
                xpos 1456 ypos 984 xsize 480
                sensitive selected_die is not None
                action Return(selected_die)
    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()

screen rm_test_pending_face_choice(die_id, card=None):
    modal True
    zorder 217
    default selected_face = None
    use rm_allow_game_menu
    use modal_dim_background
    $ die = rm_ensure_player().find_die(die_id)
    if selected_face is not None:
        key "game_menu" action SetScreenVariable("selected_face", None)
    frame:
        style "attribute_check_panel"
        fixed:
            text "选择目标骰面" style "attribute_check_title"
            text (_die_label(die)+"  ·  "+rm_test_card_label(card or {})) style "attribute_check_muted_text" ypos 90
            vpgrid:
                ypos 188 xysize (1120,714)
                cols 3 spacing 16 mousewheel True draggable True scrollbars "vertical"
                vscrollbar_xsize 10
                vscrollbar_base_bar "#dfd7c8"
                vscrollbar_thumb "#9c8d70"
                vscrollbar_hover_thumb "#6c6048"
                vscrollbar_unscrollable "hide"
                for face in rm_test_pending_face_choices(die_id, card=card):
                    button:
                        id ("growth_face_"+str(face['index']))
                        style "attribute_check_choice"
                        xysize (352,150)
                        selected selected_face == face['index']
                        action SetScreenVariable("selected_face", face['index'])
                        text "第[face['index'] + 1]面：[face['value']]" style "attribute_check_section_title" align (.5,.5)
            add Solid("#b4aa96") xpos 1192 ypos 188 xysize (1,714)
            vbox:
                xpos 1232 ypos 188 spacing 30 xsize 704
                text "变化预览" style "attribute_check_section_title"
                if selected_face is not None:
                    text rm_dice_view.growth_comparison(die, card or {}, selected_face) style "attribute_check_title" id "growth_comparison"
                    text "只改变这一个骰面，其余骰面保持原值。" style "attribute_check_muted_text"
                else:
                    text "选择一个可用骰面，查看本次变化。" style "attribute_check_body"
                text "确认后应用；取消选择可重新比较。" style "attribute_check_muted_text"
            add Solid("#b4aa96") ypos 958 xysize (1936,2)
            if selected_face is not None:
                textbutton "取消选择" id "growth_clear" style "attribute_check_tab_button" ypos 984 xsize 240 action SetScreenVariable("selected_face", None)
            textbutton "确认并应用":
                id "growth_confirm"
                style "attribute_check_button"
                xpos 1456 ypos 984 xsize 480
                sensitive selected_face is not None
                action Return(selected_face)
    if rm_ui_test_skin_active:
        use rm_ui_test_close_button()


style rm_test_schedule_frame is frame:
    xalign 0.5
    yalign 0.5
    xsize 693
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_list.png", 62, 34), "True", "#eee7d8f4")
    padding (40, 37)

style rm_test_schedule_title_text is gui_text:
    size 45
    bold True
    color "#000000"

style rm_test_schedule_hint_text is gui_text:
    size 29
    color "#000000"

style rm_test_schedule_button is button:
    xfill True
    ysize 75
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", "#d9cdbb")
    hover_background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/option_button.png", 40, 16), "True", "#eadfcc")
    padding (24, 0)

style rm_test_schedule_button_text is button_text:
    size 32
    color "#000000"
    hover_color "#000000"
    yalign 0.5

style rm_test_reward_card_button is button:
    xsize 400
    ysize 347
    background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_card.png", 34, 34), "True", "#f7f0e4")
    hover_background ConditionSwitch("rm_ui_test_skin_active", Frame("gui/ui_test_skin/dice_card.png", 34, 34), "True", "#fff2d8")
    padding (27, 24)

style rm_test_reward_card_title_text is gui_text:
    size 35
    bold True
    color "#000000"

style rm_test_reward_card_description_text is gui_text:
    size 27
    color "#000000"
    line_spacing 5
