ADJUSTABLE_STATS = ("str", "dex", "int", "pow")
STAT_MIN = 1
STAT_MAX = 20
TOTAL_ALLOCATABLE_POINTS = 17


def _normalized(values):
    return {
        stat_name: int(values.get(stat_name, STAT_MIN))
        for stat_name in ADJUSTABLE_STATS
    }


def points_spent(values):
    current = _normalized(values)
    return sum(
        current[stat_name] - STAT_MIN for stat_name in ADJUSTABLE_STATS
    )


def remaining_points(values):
    return TOTAL_ALLOCATABLE_POINTS - points_spent(values)


def can_adjust_stat(values, stat_name, delta):
    if stat_name not in ADJUSTABLE_STATS or delta not in (-1, 1):
        return False

    current = _normalized(values)
    next_value = current[stat_name] + delta
    if next_value < STAT_MIN or next_value > STAT_MAX:
        return False
    if delta > 0 and remaining_points(current) <= 0:
        return False
    return True


def adjust_stat(values, stat_name, delta):
    current = _normalized(values)
    if not can_adjust_stat(current, stat_name, delta):
        return current

    current[stat_name] += delta
    return current


def _has_valid_stat_values(values):
    return all(
        type(values.get(stat_name)) is int
        and STAT_MIN <= values[stat_name] <= STAT_MAX
        for stat_name in ADJUSTABLE_STATS
    )


def stats_complete(values):
    return (
        _has_valid_stat_values(values)
        and remaining_points(values) == 0
    )


def get_attribute_dice(_stat_name):
    return ()


def attribute_check_unavailable(stat_name):
    return {
        "available": False,
        "stat": stat_name,
        "reason": "attribute_dice_not_configured",
        "rolls": (),
    }
