"""Read-only presentation of physical dice. No rolls, rewards or state writes."""
from collections import Counter
from copy import copy
from functools import lru_cache
import random
from . import rm_core
LABELS = {"str":"力量", "dex":"灵巧", "con":"体质", "int":"智力", "pow":"意志"}
ORDER = ("str","dex","con","int","pow")

def rows(character, attribute="all", order="attribute", enchantment="all"):
    result = []
    totals = Counter(d.attribute for d in character.dice_pool)
    serials = Counter()
    for die in character.dice_pool:
        serials[die.attribute] += 1
        if attribute != "all" and die.attribute != attribute:
            continue
        if enchantment != "all" and bool(die.enchantment) != (enchantment == "enchanted"):
            continue
        row = rm_core.dice_summary(die)
        row.update(label=LABELS[die.attribute], sides=len(die.faces), serial=serials[die.attribute], total=totals[die.attribute])
        result.append(row)
    key = {"attribute": lambda d: (ORDER.index(d["attribute"]), d["serial"]),
           "sides": lambda d: (d["sides"], d["attribute"], d["serial"]),
           "mean": lambda d: (-d["expectation"], d["attribute"], d["serial"])}[order]
    return sorted(result, key=key)

def preview_indices(faces):
    """D4/6: every physical face. Larger dice: five concrete faces + ellipsis."""
    if len(faces) <= 6:
        return list(range(len(faces)))
    ranked = sorted(range(len(faces)), key=lambda i: (faces[i], i))
    return [ranked[round(i*(len(ranked)-1)/4)] for i in range(5)] + [None]

def distribution(faces):
    counts = Counter(faces)
    values = sorted(set(range(1,len(faces)+1)) | set(faces))
    return [(value, counts[value], counts[value]/float(len(faces))) for value in values]

def visible_faces(faces, offset=0):
    count = min(len(faces), 9) if len(faces) > 12 else len(faces)
    offset = max(0, min(offset, len(faces)-count))
    return list(range(offset, offset+count))

def growth(character):
    return [(a, LABELS[a], int(character.dice_growth_progress.get(a, 0)),
             int(character.growth_reward_pending.get(a, 0))) for a in ORDER]


def check_selection(character, spec, rng):
    """Resolve the displayed pool with a copy of the game's RNG, never roll it."""
    preview_rng = random.Random()
    preview_rng.setstate(rng.getstate())
    profile = rm_core.mood_check_profile(rm_core.mood_state(character))
    limit = rm_core.max_dice_for_check(spec, profile)
    dice = rm_core.selected_dice(character, spec, limit, preview_rng) if spec.dice_ids else []
    cost = rm_core.total_energy_cost(dice, spec, profile) if dice else 0
    if cost > 0:
        cost = max(1, cost - rm_core.time_habit_energy_discount(character, spec))
    weather = rm_core.weather_check_effects(character, spec)
    advantage, disadvantage = rm_core.check_advantage_counts(character, spec, weather, dice)
    net = advantage - disadvantage
    modes = ["normal" for die in dice]
    preview = dict(dice=dice, cost=cost, limit=limit,
        target=rm_core.adjusted_requirement(spec.requirement, profile),
        attribute_modifier=rm_core.attribute_modifier(character, spec.attribute, profile),
        extra_modifier=spec.extra_modifier + rm_core.drowsiness_check_modifier(character, spec.attribute),
        dice_multiplier=profile['dice_multiplier'],
        final_multiplier=rm_core.check_final_multiplier(character, spec, len(dice), weather),
        modes=modes, advantage=advantage, disadvantage=disadvantage,
        bonus_choice_pending=net > len(spec.bonus_die_ids),
        remaining=character.energy-cost, success_probability=None, total_range=None, reason="")
    missing = rm_core.missing_required_dice_attribute(dice, spec.required_dice_attributes)
    if len(dice) < spec.min_dice:
        preview['reason'] = "至少选择 {} 颗骰子".format(spec.min_dice)
    elif missing:
        preview['reason'] = "还需一颗{}骰子".format(LABELS[missing])
    elif not weather['available']:
        preview['reason'] = weather['reason']
    elif cost > character.energy:
        preview['reason'] = "精力不足，还差 {}".format(cost-character.energy)
        if spec.forced:
            preview.update(success_probability=0.0, remaining=character.energy)
    if not preview['reason']:
        if preview['bonus_choice_pending']:
            return preview
        targets = tuple(next(i for i, die in enumerate(dice) if die.id == die_id)
                        for die_id in spec.bonus_die_ids[:max(0, net)])
        outcomes = (check_sum_distribution(tuple((tuple(die.faces), mode) for die, mode in zip(dice, modes)))
                    if net == 0 else check_reroll_distribution(tuple((tuple(die.faces), mode) for die, mode in zip(dice, modes)), net, targets))
        success_weight = 0
        totals = []
        for dice_total, weight in outcomes:
            total = (preview['attribute_modifier'] + dice_total*preview['dice_multiplier'] + preview['extra_modifier'])*preview['final_multiplier']
            totals.append(total)
            rank = rm_core.result_rank(total, preview['target'], dice_total, dice, spec.big_failure_slack)
            rank = rm_core.apply_mania_big_failure(rank, total, preview['target'], rm_core.mood_state(character))
            if rank in (rm_core.RESULT_SUCCESS, rm_core.RESULT_HARD_SUCCESS, rm_core.RESULT_BIG_SUCCESS):
                success_weight += weight
        preview['success_probability'] = success_weight / sum(weight for _, weight in outcomes)
        preview['total_range'] = (min(totals), max(totals))
    return preview


@lru_cache(maxsize=256)
def check_sum_distribution(dice_modes):
    """Exact integer weights, including repeated physical faces and rerolls."""
    sums = Counter({0: 1})
    for faces, mode in dice_modes:
        values = Counter(faces)
        if mode != "normal":
            choose = max if mode == "bonus" else min
            values = Counter(choose(a, b) for a in faces for b in faces)
        combined = Counter()
        for total, weight in sums.items():
            for value, count in values.items():
                combined[total+value] += weight*count
        sums = combined
    return tuple(sorted(sums.items()))


@lru_cache(maxsize=128)
def check_reroll_distribution(dice_modes, net, targets=()):
    """Exact value distribution after each remaining source rerolls one invested die."""
    states = {(): 1.0}
    for faces, mode in dice_modes:
        counts = check_sum_distribution(((faces, mode),))
        total = float(sum(weight for _, weight in counts))
        states = {prefix + (value,): probability * weight / total
                  for prefix, probability in states.items() for value, weight in counts}
    for step in range(abs(net)):
        advanced = Counter()
        indices = (targets[step] if step < len(targets) else 0,) if net > 0 else tuple(range(len(dice_modes)))
        for values, probability in states.items():
            for index in indices:
                faces = dice_modes[index][0]
                for face in faces:
                    changed = list(values)
                    changed[index] = max(values[index], face) if net > 0 else min(values[index], face)
                    advanced[tuple(changed)] += probability / (len(indices) * len(faces))
        states = advanced
    sums = Counter()
    for values, probability in states.items():
        sums[sum(values)] += probability
    return tuple(sorted(sums.items()))


def check_selection_change(character, spec, rng, die_id):
    """Preview one click, preserving the current selection, player and RNG."""
    changed = copy(spec)
    changed.dice_ids = list(spec.dice_ids)
    if die_id in changed.dice_ids:
        changed.dice_ids.remove(die_id)
    else:
        changed.dice_ids.append(die_id)
    return check_selection(character, changed, rng)


def probability_text(probability):
    if probability is None:
        return "—"
    if probability == 0 or probability == 1:
        return "{:.0f}%".format(probability*100)
    if probability < .001:
        return "<0.1%"
    if probability > .999:
        return ">99.9%"
    return "{:.1f}%".format(probability*100)


def check_change_text(before, after, removing=False):
    if after['reason']:
        return ("移除后：" if removing else "加入后：") + after['reason']
    probability = after['success_probability']
    if probability is None:
        return "选择奖励重投目标后显示概率 · 精力 {}".format(after['cost'])
    if before['success_probability'] is None:
        return "选用后 {} · 精力 {}".format(probability_text(probability), after['cost'])
    delta = (probability-before['success_probability'])*100
    change = "{:+.1f}".format(delta) if abs(delta) >= .05 else ("微升" if delta > 0 else "微降" if delta < 0 else "不变")
    return "{} {}{} · 精力 {:+g}".format("移除" if removing else "加入", change, "百分点" if abs(delta) >= .05 else "", after['cost']-before['cost'])


def check_factor_details(character, spec, dice_count):
    injury = rm_core.injury_check_multiplier(character, spec)
    alcohol = rm_core.alcohol_check_multiplier(character, spec)
    heart = .85 if character.palpitations else 1.0
    normal = rm_core.check_final_multiplier(character, spec, dice_count) / (injury * alcohol * heart)
    factors = [("普通修正池（天气、情绪、疼痛等加算后）", normal),
               ("伤势独立倍率", injury), ("酒精独立倍率", alcohol), ("心悸独立倍率", heart)]
    return ["{}：总值 ×{:g}".format(label, factor) for label, factor in factors if factor != 1]


def growth_comparison(die, card, face_index=None):
    """Only show deterministic changes; random targets stay explicitly random."""
    kind = card.get("type")
    faces = die.faces
    if kind == "upgrade_chosen_die_type":
        return "D{} → D{}；新增两面：{}、{}".format(len(faces), len(faces)+2, min(faces), max(faces))
    if face_index is not None:
        before = faces[face_index]
        if kind == "increase_chosen_face":
            after = min(len(faces), before + int(card.get("increase_amount", 1)))
        elif kind == "replace_chosen_face_chosen_die":
            after = int(rm_core.clamp(rm_core.replacement_face_value(card, die), 1, len(faces)))
        elif kind == "decrease_chosen_face":
            after = max(1, before - 1)
        else:
            return rm_core.card_description(card)
        return "第{}面：{} → {}（面值上限 {}）".format(face_index+1, before, after, len(faces))
    if kind == "clear_negative_enchant":
        return "{} → 无附魔".format(rm_core.enchantment_label(die.enchantment))
    return rm_core.card_description(card)
