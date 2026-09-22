init -10 python:
    def rm_mock_schedules():
        """Return abstract mock schedules only; formal schedule pools are out of scope."""
        return rm_core.mock_schedule_specs()

    def rm_get_mock_schedule(schedule_id):
        for spec in rm_mock_schedules():
            if spec.id == schedule_id:
                return spec
        raise ValueError("Unknown mock schedule: {!r}".format(schedule_id))

    def rm_execute_mock_schedule(schedule_id, character=None):
        character = character or rm_ensure_player()
        schedule = rm_get_mock_schedule(schedule_id)
        result = None
        if schedule.check_spec is not None:
            result = rm_core.perform_check(character, schedule.check_spec, rng=renpy.random)
        turn = rm_core.end_action_round(character, schedule.mood_delta, rng=renpy.random, check=result)
        return {"schedule": schedule, "check": result, "turn": turn}
