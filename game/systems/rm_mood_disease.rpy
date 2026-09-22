init -14 python:
    def get_mood_state(state=None):
        state = state or rm_ensure_player()
        return rm_core.get_mood_state(state)

    def calculate_k_pow(state=None):
        state = state or rm_ensure_player()
        return rm_core.calculate_k_pow(state)

    def apply_mood_delta(state, delta_base):
        return rm_core.apply_mood_delta(state, delta_base)

    def calculate_enter_disease_probability(state=None):
        state = state or rm_ensure_player()
        return rm_core.calculate_enter_disease_probability(state)

    def roll_enter_disease(state=None):
        state = state or rm_ensure_player()
        return rm_core.roll_enter_disease(state, rng=renpy.random)

    def calculate_stable_probability(state=None):
        state = state or rm_ensure_player()
        return rm_core.calculate_stable_probability(state)

    def roll_stabilize(state=None):
        state = state or rm_ensure_player()
        return rm_core.roll_stabilize(state, rng=renpy.random)

    def calculate_switch_probability(state=None):
        state = state or rm_ensure_player()
        return rm_core.calculate_switch_probability(state)

    def roll_switch_disease(state=None):
        state = state or rm_ensure_player()
        return rm_core.roll_switch_disease(state, rng=renpy.random)

    def apply_disease_entry(state=None):
        state = state or rm_ensure_player()
        return rm_core.apply_disease_entry(state)

    def apply_disease_switch(state=None):
        state = state or rm_ensure_player()
        return rm_core.apply_disease_switch(state)

    def apply_stable_return(state=None):
        state = state or rm_ensure_player()
        return rm_core.apply_stable_return(state)

    def apply_sleep_recovery(state=None):
        state = state or rm_ensure_player()
        return rm_core.apply_sleep_recovery(state)

    def update_man_dep_after_mood_delta(state, final_delta):
        return rm_core.update_man_dep_after_mood_delta(state, final_delta)

    def process_disease_end_turn_checks(state=None):
        state = state or rm_ensure_player()
        return rm_core.process_disease_end_turn_checks(state, rng=renpy.random)

    def maybe_trigger_disease_random_event(state=None):
        state = state or rm_ensure_player()
        return rm_core.maybe_trigger_disease_random_event(state, rng=renpy.random)

    def rm_mood_state(character=None):
        character = character or rm_ensure_player()
        return rm_core.mood_state(character)

    def rm_adjusted_mood_delta(base_delta, character=None):
        """Apply POW-based Mood delta correction without mutating Mood."""
        character = character or rm_ensure_player()
        return rm_core.adjusted_mood_delta(character, base_delta)

    def rm_disease_enter_probability(character=None):
        character = character or rm_ensure_player()
        return rm_core.disease_enter_probability(character)

    def rm_stable_probability(character=None):
        character = character or rm_ensure_player()
        return rm_core.stable_probability(character)
