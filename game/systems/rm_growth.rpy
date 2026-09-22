init -12 python:
    def rm_add_attribute_bonus(attribute, value, source="debug", character=None):
        """Add a temporary attribute bonus layer; rest conversion is later-phase logic."""
        character = character or rm_ensure_player()
        rm_core.ensure_second_stage_state(character)
        character.attribute_bonuses[attribute].append(rm_core.RevertableDict(value=int(value), source=source))
        return rm_core.current_attribute(character, attribute)

    def rm_add_attribute_value(attribute, value, character=None):
        """Add a mid-term attribute value that participates in checks."""
        character = character or rm_ensure_player()
        rm_core.ensure_second_stage_state(character)
        character.attribute_values[attribute] += int(value)
        return rm_core.current_attribute(character, attribute)

    def add_dice_growth_progress(state, attr, amount):
        return rm_core.add_dice_growth_progress(state, attr, amount)

    def process_dice_growth_progress_on_small_rest(state=None):
        state = state or rm_ensure_player()
        return rm_core.process_dice_growth_progress_on_small_rest(state)

    def add_growth_reward_pending(state, attr, count=1):
        return rm_core.add_growth_reward_pending(state, attr, count)

    def draw_growth_reward_cards(state, attr, draw_count=3):
        return rm_core.draw_growth_reward_cards(state, attr, draw_count, rng=renpy.random)

    def draw_pending_growth_reward_cards(state, attr, draw_count=3):
        return rm_core.draw_pending_growth_reward_cards(state, attr, draw_count, rng=renpy.random)

    def apply_growth_reward(state, attr, reward_card):
        return rm_core.apply_growth_reward(state, attr, reward_card, rng=renpy.random)

    def apply_pending_growth_reward(state, attr, reward_card):
        return rm_core.apply_pending_growth_reward(state, attr, reward_card, rng=renpy.random)

    def add_degradation_progress(state, attr, amount):
        return rm_core.add_degradation_progress(state, attr, amount)

    def process_degradation_threshold(state, attr):
        return rm_core.process_degradation_threshold(state, attr)

    def draw_degradation_penalty_cards(state, attr, draw_count=3):
        return rm_core.draw_degradation_penalty_cards(state, attr, draw_count, rng=renpy.random)

    def draw_pending_degradation_penalty_cards(state, attr, draw_count=3):
        return rm_core.draw_pending_degradation_penalty_cards(state, attr, draw_count, rng=renpy.random)

    def apply_degradation_penalty(state, attr, penalty_card):
        return rm_core.apply_degradation_penalty(state, attr, penalty_card, rng=renpy.random)

    def apply_pending_degradation_penalty(state, attr, penalty_card):
        return rm_core.apply_pending_degradation_penalty(state, attr, penalty_card, rng=renpy.random)
