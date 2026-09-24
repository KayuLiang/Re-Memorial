default rm_player = None

init -18 python:
    from game.systems import rm_pillbox
    def rm_create_initial_character(allocation=None):
        """Create the first-stage numeric state used by schedules and checks."""
        return rm_core.create_initial_character(allocation, rng=renpy.random)

    def rm_reset_player(allocation=None):
        store.rm_player = rm_create_initial_character(allocation)
        return store.rm_player

    def rm_ensure_player():
        if store.rm_player is None:
            store.rm_player = rm_create_initial_character()
        rm_core.ensure_second_stage_state(store.rm_player)
        rm_pillbox.ensure_state(store.rm_player)
        return store.rm_player

    def rm_normalize_loaded_player():
        if store.rm_player is not None:
            rm_core.ensure_second_stage_state(store.rm_player)
            rm_pillbox.ensure_state(store.rm_player)

    config.after_load_callbacks.append(rm_normalize_loaded_player)
