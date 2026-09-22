init python:
    from game.systems import rm_core as _rm_core
    import math

    def rm_start_opening_allocation():
        store.rm_player = _rm_core.create_opening_draft_character(rng=renpy.random)
        return store.rm_player

    def rm_opening_character():
        if store.rm_player is None:
            return rm_start_opening_allocation()
        return rm_ensure_player()

    def rm_opening_attribute_value(attribute):
        return rm_opening_character().formal_attributes[attribute]

    def opening_stat_points_remaining():
        return _rm_core.initial_attribute_points_remaining(rm_opening_character())

    def opening_can_adjust_stat(attribute, delta):
        return _rm_core.can_reallocate_initial_attribute(rm_opening_character(), attribute, delta)

    def rm_opening_adjust_attribute(attribute, delta):
        store.rm_player = _rm_core.reallocate_initial_attributes(
            rm_opening_character(),
            attribute,
            delta,
            rng=renpy.random,
        )
        return None

    def opening_adjust_stat(attribute, delta):
        rm_opening_adjust_attribute(attribute, delta)
        return None

    def opening_stats_complete():
        return opening_stat_points_remaining() == 0

    def _validate_stat_name(attribute):
        if attribute not in _rm_core.ATTRIBUTES:
            raise ValueError("Unknown attribute: {!r}".format(attribute))
        return attribute

    def get_effective_stat(attribute):
        _validate_stat_name(attribute)
        return _rm_core.effective_attribute(rm_opening_character(), attribute)

    def _die_label(die):
        return "{} d{}".format(_rm_core.ATTRIBUTE_LABELS[die.attribute], len(die.faces))

    def _die_to_dict(die, selectable=True):
        return {
            "id": die.id,
            "stat": die.attribute,
            "label": _die_label(die),
            "faces": tuple(die.faces),
            "selectable": selectable,
        }

    def get_attribute_dice(attribute):
        _validate_stat_name(attribute)
        return tuple(_die_to_dict(die) for die in rm_opening_character().dice_for(attribute))

    def _normal_attribute_tuple(attributes, fallback):
        if attributes is None:
            return (fallback,)
        if isinstance(attributes, (list, tuple)):
            return tuple(attributes)
        return (attributes,)

    def get_attribute_check_dice_options(required_attribute, allowed_attributes=None):
        _validate_stat_name(required_attribute)
        allowed = _normal_attribute_tuple(allowed_attributes, required_attribute)
        dice = []
        for die in rm_opening_character().dice_pool:
            dice.append(_die_to_dict(die, selectable=die.attribute in allowed and not die.is_sealed()))
        return tuple(dice)

    def format_die_faces(faces):
        faces = tuple(faces)
        if faces == tuple(range(1, 21)):
            return "1~20"
        return " / ".join(str(face) for face in faces)

    def attribute_check_action_type_label(action_type):
        if action_type == _rm_core.ACTION_WAKE:
            return "起床·免费"
        if action_type == _rm_core.ACTION_SCHEDULE:
            return "日程"
        if action_type == _rm_core.ACTION_FORCED_SCHEDULE:
            return "强制日程"
        return "即时"

    def attribute_check_header(attribute, requirement=6, action_type=None, check_kind=None):
        _validate_stat_name(attribute)
        action_type = action_type or _rm_core.ACTION_INSTANT
        character = rm_opening_character()
        profile = _rm_core.mood_check_profile(_rm_core.mood_state(character))
        target = _rm_core.adjusted_requirement(requirement, profile)
        fixed = _rm_core.attribute_modifier(character, attribute, profile)
        fixed += _rm_core.drowsiness_check_modifier(character, attribute)
        needed_roll = max(0, int(math.ceil(target - fixed)))
        return {
            "kind": check_kind or "{}检定".format(_rm_core.ATTRIBUTE_LABELS[attribute]),
            "action_type": action_type,
            "action_type_label": attribute_check_action_type_label(action_type),
            "target": target,
            "fixed": fixed,
            "needed_roll": needed_roll,
        }

    def attribute_check_energy_cost(attribute, die_ids=None, action_type=None, allowed_attributes=None, required_die_attributes=None):
        _validate_stat_name(attribute)
        action_type = action_type or _rm_core.ACTION_INSTANT
        character = rm_opening_character()
        selected_ids = normalize_attribute_die_ids(die_ids)
        if not selected_ids:
            return 0
        profile = _rm_core.mood_check_profile(_rm_core.mood_state(character))
        spec = _rm_core.CheckSpec(
            attribute,
            6,
            selected_ids,
            action_type=action_type,
            is_late_night=(character.current_time_slot in _rm_core.TIME_SLOTS[6:]),
            allowed_dice_attributes=_normal_attribute_tuple(allowed_attributes, attribute),
            required_dice_attributes=tuple(required_die_attributes or ()),
        )
        dice = _rm_core.selected_dice(character, spec, _rm_core.max_dice_for_check(spec, profile), renpy.random)
        return _rm_core.total_energy_cost(dice, spec, profile)

    def attribute_check_rank_label(rank):
        labels = {
            _rm_core.RESULT_BIG_FAILURE: "大失败",
            _rm_core.RESULT_FAILURE: "失败",
            _rm_core.RESULT_SUCCESS: "普通成功",
            _rm_core.RESULT_HARD_SUCCESS: "困难成功",
            _rm_core.RESULT_BIG_SUCCESS: "大成功",
        }
        return labels.get(rank, str(rank))

    def normalize_attribute_die_ids(die_ids):
        if die_ids is None:
            return []
        if isinstance(die_ids, (list, tuple)):
            return list(die_ids)
        return [die_ids]

    def preview_attribute_check(attribute, die_ids, allowed_attributes=None):
        _validate_stat_name(attribute)
        selected_ids = normalize_attribute_die_ids(die_ids)
        selected_dice = []
        for die in get_attribute_check_dice_options(attribute, allowed_attributes):
            if die["id"] in selected_ids:
                selected_dice.append(die)
        effective = get_effective_stat(attribute)
        first_die = selected_dice[0] if selected_dice else None
        return {
            "stat": attribute,
            "stat_label": _rm_core.ATTRIBUTE_LABELS[attribute],
            "stat_value": effective,
            "stat_half": effective // 2,
            "die_id": first_die["id"] if first_die else (selected_ids[0] if selected_ids else None),
            "die_ids": tuple(selected_ids),
            "die_label": " + ".join(die["label"] for die in selected_dice) if selected_dice else "",
            "die_faces": first_die["faces"] if first_die else (),
            "die_faces_text": " / ".join(format_die_faces(die["faces"]) for die in selected_dice) if selected_dice else "",
            "dice": tuple(selected_dice),
        }

    def attribute_selection_meets_requirements(die_ids, required_die_attributes=None):
        required = tuple(required_die_attributes or ())
        if not required:
            return True
        selected_ids = normalize_attribute_die_ids(die_ids)
        selected_attributes = set()
        for die in rm_opening_character().dice_pool:
            if die.id in selected_ids:
                selected_attributes.add(die.attribute)
        return all(attribute in selected_attributes for attribute in required)

    def perform_attribute_check(attribute, die_ids=None, energy=1):
        _validate_stat_name(attribute)
        dice = get_attribute_dice(attribute)
        selected_ids = normalize_attribute_die_ids(die_ids)
        if not selected_ids and dice:
            selected_ids = [dice[0]["id"]]
        if not selected_ids:
            return {
                "available": False,
                "stat": attribute,
                "reason": "attribute_dice_not_configured",
                "rolls": (),
            }
        spec = _rm_core.CheckSpec(attribute, 6, selected_ids, action_type=_rm_core.ACTION_INSTANT)
        result = _rm_core.perform_check(rm_opening_character(), spec, rng=renpy.random)
        rolled_ids = list(result.dice_ids or selected_ids)
        rolled_dice = [rm_opening_character().find_die(die_id) for die_id in rolled_ids]
        rolled_dice = [die for die in rolled_dice if die is not None]
        first_die = rolled_dice[0] if rolled_dice else None
        die_faces = tuple(first_die.faces) if first_die else ()
        rolls = tuple(item["value"] for item in result.dice_results)
        roll_value = result.dice_results[0]["value"] if result.dice_results else None
        return {
            "available": result.available,
            "reason": result.reason,
            "stat": attribute,
            "stat_label": _rm_core.ATTRIBUTE_LABELS[attribute],
            "stat_value": get_effective_stat(attribute),
            "stat_half": result.attribute_modifier,
            "die_id": first_die.id if first_die else selected_ids[0],
            "die_ids": tuple(rolled_ids),
            "die_label": " + ".join(_die_label(die) for die in rolled_dice) if rolled_dice else selected_ids[0],
            "die_faces": die_faces,
            "die_sides": len(die_faces),
            "die_faces_text": " / ".join(format_die_faces(die.faces) for die in rolled_dice) if rolled_dice else "",
            "rolls": rolls,
            "mood_modifier": result.extra_modifier,
            "dice_total": result.dice_total,
            "total": result.total,
            "success_threshold": result.requirement,
            "success": result.success,
            "rank": result.rank,
        }
