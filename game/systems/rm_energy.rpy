init -16 python:
    def rm_energy_max(character=None):
        """Calculate EnergyMax from CON dice expectations and routine modifiers."""
        character = character or rm_ensure_player()
        return rm_core.energy_max(character)

    def rm_refresh_energy(character=None):
        character = character or rm_ensure_player()
        character.energy = rm_core.energy_max(character)
        return character.energy

