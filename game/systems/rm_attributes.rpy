init -17 python:
    def rm_current_attribute(attribute, character=None):
        """Return formal attribute + attribute value + active temporary bonuses."""
        character = character or rm_ensure_player()
        return rm_core.current_attribute(character, attribute)

    def rm_effective_attribute(attribute, character=None):
        """Return the capped attribute value used by check formulas."""
        character = character or rm_ensure_player()
        return rm_core.effective_attribute(character, attribute)

    def rm_attribute_summary(character=None):
        character = character or rm_ensure_player()
        return {
            name: {
                "current": rm_core.current_attribute(character, name),
                "effective": rm_core.effective_attribute(character, name),
            }
            for name in rm_core.ATTRIBUTES
        }

    def gain_attribute_bonus(state, attr, base_probability):
        return rm_core.gain_attribute_bonus(state, attr, base_probability, rng=renpy.random)

    def add_attribute_bonus(state, attr, amount):
        return rm_core.add_attribute_bonus(state, attr, amount)

    def add_attribute_value(state, attr, amount):
        return rm_core.add_attribute_value(state, attr, amount)

    def add_formal_attribute(state, attr, amount):
        return rm_core.add_formal_attribute(state, attr, amount)

    def process_small_rest(state=None):
        state = state or rm_ensure_player()
        return rm_core.process_small_rest(state, rng=renpy.random)

    def process_large_rest(state=None):
        state = state or rm_ensure_player()
        return rm_core.process_large_rest(state, rng=renpy.random)
