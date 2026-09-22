init -13 python:
    def rm_status_character_summary(character=None):
        """Return the current player status summary for story HUD screens."""
        character = character or rm_ensure_player()
        return rm_core.character_summary(character)

    def rm_status_dice_pool_summary(character=None):
        """Return UI-ready rows for every die currently owned by the player."""
        character = character or rm_ensure_player()
        return rm_core.dice_pool_summary(character)

    def rm_status_mood_value(character=None):
        character = character or rm_ensure_player()
        return int(character.mood)

    def rm_status_energy_points(character=None):
        character = character or rm_ensure_player()
        return int(character.energy)

    def rm_status_energy_max(character=None):
        character = character or rm_ensure_player()
        return rm_core.energy_max(character)

    def rm_status_health(character=None):
        character = character or rm_ensure_player()
        rm_core.ensure_health(character)
        return character.health, rm_core.health_max(character)

    def rm_status_health_tooltip(character=None):
        return rm_core.health_tooltip(character or rm_ensure_player())

    def rm_status_mood_tooltip(character=None):
        character = character or rm_ensure_player()
        return rm_core.mood_tooltip(character)

    def rm_status_energy_tooltip(character=None):
        character = character or rm_ensure_player()
        return rm_core.energy_tooltip(character)

    def rm_status_statuses(character=None):
        character = character or rm_ensure_player()
        return rm_core.status_summary(character)
