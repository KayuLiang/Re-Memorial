default stat_con = 3
default stat_str = 1
default stat_dex = 1
default stat_int = 1
default stat_pow = 1


init python:
    from opening_stats_logic import (
        adjust_stat,
        attribute_check_unavailable,
        can_adjust_stat,
        get_attribute_dice as _get_attribute_dice,
        remaining_points,
        stats_complete,
    )

    def _opening_stat_values():
        return {
            "str": store.stat_str,
            "dex": store.stat_dex,
            "int": store.stat_int,
            "pow": store.stat_pow,
        }

    def opening_stat_points_remaining():
        return remaining_points(_opening_stat_values())

    def opening_can_adjust_stat(stat_name, delta):
        return can_adjust_stat(_opening_stat_values(), stat_name, delta)

    def opening_adjust_stat(stat_name, delta):
        values = adjust_stat(_opening_stat_values(), stat_name, delta)
        store.stat_str = values["str"]
        store.stat_dex = values["dex"]
        store.stat_int = values["int"]
        store.stat_pow = values["pow"]

    def opening_stats_complete():
        return stats_complete(_opening_stat_values())

    def get_base_stat(stat_name):
        store_names = {
            "con": "stat_con",
            "str": "stat_str",
            "dex": "stat_dex",
            "int": "stat_int",
            "pow": "stat_pow",
        }
        try:
            store_name = store_names[stat_name]
        except (KeyError, TypeError):
            raise ValueError("Unknown attribute: {!r}".format(stat_name))
        return getattr(store, store_name)

    def get_effective_stat(stat_name):
        return get_base_stat(stat_name)

    def get_attribute_dice(stat_name):
        return _get_attribute_dice(stat_name)

    def perform_attribute_check(stat_name, energy=1):
        dice = get_attribute_dice(stat_name)
        if not dice:
            return attribute_check_unavailable(stat_name)
        return {
            "available": True,
            "stat": stat_name,
            "energy": energy,
            "rolls": tuple(),
        }
