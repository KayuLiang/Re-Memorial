init -9 python:
    def start_turn(state, time_slot):
        return rm_core.start_turn(state, time_slot)

    def resolve_action(state, schedule_spec):
        return rm_core.resolve_action(state, schedule_spec)

    def end_turn(state, turn_result):
        return rm_core.end_turn(state, turn_result, rng=renpy.random)

    def end_day(state):
        return rm_core.end_day(state, rng=renpy.random)

    def end_week_if_needed(state):
        return rm_core.end_week_if_needed(state, rng=renpy.random)

    def advance_time_slot(state):
        return rm_core.advance_time_slot(state)

    def rm_end_action_round(mood_delta_base=0, character=None):
        """Run first-stage action-round settlement in handbook order."""
        character = character or rm_ensure_player()
        return rm_core.end_action_round(character, mood_delta_base, rng=renpy.random)
