init -15 python:
    def rm_dice_for(attribute, character=None):
        character = character or rm_ensure_player()
        return character.dice_for(attribute)

    def rm_set_die_enchantment(dice_id, enchantment, character=None):
        """Attach one enchantment to one die; new enchantment replaces old one."""
        character = character or rm_ensure_player()
        die = character.find_die(dice_id)
        if die is None:
            raise ValueError("Unknown die id: {!r}".format(dice_id))
        rm_core.set_die_enchantment(die, enchantment, replace=True)
        return die

    def rm_roll_die(die, character=None):
        return rm_core.roll_die(die, rng=renpy.random)

    def rm_set_die_temporary_enchantment(dice_id, enchantment, character=None):
        character = character or rm_ensure_player()
        die = character.find_die(dice_id)
        if die is None:
            raise ValueError("Unknown die id: {!r}".format(dice_id))
        return rm_core.set_die_enchantment(die, enchantment, temporary=True, replace=True)

    def rm_process_temporary_enchant_decay(character=None):
        character = character or rm_ensure_player()
        return rm_core.process_temporary_enchant_decay(character, rng=renpy.random)
