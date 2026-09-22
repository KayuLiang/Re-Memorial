init -13 python:
    def rm_make_check_spec(attribute, requirement, dice_ids=None, action_type=rm_core.ACTION_SCHEDULE, max_dice=3, min_dice=1, extra_modifier=0, forced=False, is_late_night=False):
        return rm_core.CheckSpec(attribute, requirement, dice_ids, action_type, max_dice, min_dice, extra_modifier, forced, is_late_night)

    def rm_perform_check(spec, character=None):
        """Execute one backend check and return an RMCheckResult object."""
        character = character or rm_ensure_player()
        return rm_core.perform_check(character, spec, rng=renpy.random)

    def rm_perform_mock_check(attribute="dex", requirement=5, character=None):
        character = character or rm_ensure_player()
        dice = character.dice_for(attribute)
        dice_ids = [dice[0].id] if dice else []
        return rm_core.perform_check(character, rm_core.CheckSpec(attribute, requirement, dice_ids), rng=renpy.random)

