"""Data-driven cooking rules shared by Ren'Py and the standalone kitchen."""

from __future__ import division

import json
import math
import random
import re
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
_COMPARISON = re.compile(r"^(.+?)(>=|<=|==|>|<)(-?\d+(?:\.\d+)?)$")
_OTHER = re.compile(r"^other_(fruit|vegetable)\((.+)\)$")


def load_tables(directory=DATA_DIR):
    """Return independently editable ingredient, recipe and rule tables."""
    directory = Path(directory)
    return tuple(json.loads((directory / name).read_text(encoding="utf-8"))
                 for name in ("ingredients.json", "recipes.json", "config.json"))


def _item_id(item):
    return item if isinstance(item, str) else item["id"]


def aggregate(items, ingredients):
    """Count actual ingredient units, not the sum of degree values."""
    count = Counter()
    degrees = Counter()
    categories = Counter()
    raw_produce = set()
    seafood_types = set()
    raw_veg_mush = set()
    fixed_total = 0
    for item in items:
        name = _item_id(item)
        if name not in ingredients:
            raise ValueError("Unknown ingredient: %s" % name)
        row = ingredients[name]
        fixed = row["fixed"] if isinstance(item, str) else item.get("fixed", row["fixed"])
        if fixed is None:
            raise ValueError("Processed ingredient %s needs inherited Fixed" % name)
        fixed_total += fixed
        count[name] += 1
        for category in row["categories"]:
            categories[category] += 1
        for key, amount in row["signals"].items():
            degrees[key] += amount
        if not row["processed"] and ("vegetable" in row["categories"] or "fruit" in row["categories"]):
            raw_produce.add(name)
        if not row["processed"] and ("vegetable" in row["categories"] or "mushroom" in row["categories"]):
            raw_veg_mush.add(name)
        if "seafood" in row["categories"]:
            seafood_types.add(name)
    total = len(items)
    degrees["vegetable_degree"] = categories["vegetable"]
    degrees["fruit_degree"] = categories["fruit"]
    degrees["curry_vegetable_degree"] = categories["vegetable"] + categories["mushroom"] + count["豆腐"]
    degrees["curry_degree"] = 1.5 * min(degrees["spice_degree"], degrees["curry_vegetable_degree"])
    degrees["sweet_sour_degree"] = 1.5 * min(degrees["sweet_degree"], degrees["acid_degree"])
    degrees["luwei_degree"] = 1.5 * min(degrees["soy_degree"], degrees["spice_degree"])
    return {
        "count": count, "degrees": degrees, "categories": categories,
        "ingredient_count": total, "fixed_total": fixed_total,
        "water_share": degrees["water_degree"] / float(total) if total else 0,
        "raw_produce_types": len(raw_produce), "seafood_types": len(seafood_types),
        "raw_vegetable_or_mushroom": categories["vegetable"] + categories["mushroom"],
        "raw_vegetable_or_mushroom_types": len(raw_veg_mush),
    }


def _matches_anti(item, anti, ingredients):
    name = _item_id(item)
    row = ingredients[name]
    return anti == name or anti in row["categories"]


def is_legal_filler(item, recipe, ingredients):
    return not any(_matches_anti(item, anti, ingredients) for anti in recipe["anti"])


def _value(key, stats, recipe, items, ingredients):
    if key in stats["count"]:
        return stats["count"][key]
    if key in stats["degrees"]:
        return stats["degrees"][key]
    if key in stats["categories"]:
        return stats["categories"][key]
    if key in ("water_share", "ingredient_count", "raw_produce_types", "seafood_types",
               "raw_vegetable_or_mushroom", "raw_vegetable_or_mushroom_types"):
        return stats[key]
    if key == "legal_filler":
        return sum(is_legal_filler(item, recipe, ingredients) and
                   not any(_matches_anti(item, excluded, ingredients) for excluded in recipe["filler_exclude"])
                   for item in items)
    if key == "accompaniment":
        return sum(is_legal_filler(item, recipe, ingredients) and
                   not any(_matches_anti(item, excluded, ingredients) for excluded in recipe["accompaniment_exclude"])
                   for item in items)
    other = _OTHER.match(key)
    if other:
        category, excluded = other.groups()
        return sum(category in ingredients[_item_id(item)]["categories"] and _item_id(item) != excluded
                   for item in items)
    if key in ingredients:
        return stats["count"][key]
    if key in ("water_degree", "liquid_degree", "oilfat_degree", "fry_signal", "dairy_degree",
               "tomato_degree", "spicy_degree", "sweet_degree", "acid_degree", "soy_degree",
               "spice_degree", "tea_degree", "matcha_load", "coffee_degree", "coffee_load",
               "cocoa_degree", "cocoa_load", "meat_degree", "seafood_degree", "vegetable_degree",
               "fruit_degree", "curry_vegetable_degree", "curry_degree", "sweet_sour_degree",
               "luwei_degree", "alcohol_load"):
        return 0
    if key in ("vegetable", "mushroom", "fruit", "bean", "meat", "seafood", "rice", "noodle", "flour", "egg"):
        return 0
    raise ValueError("Unknown recipe condition field: %s" % key)


def matches_condition(condition, stats, recipe, items, ingredients):
    condition = condition.strip()
    if condition.startswith("oneof(") and condition.endswith(")"):
        return any(matches_condition(token, stats, recipe, items, ingredients)
                   for token in condition[6:-1].split("|"))
    if condition.startswith("atleast"):
        match = re.match(r"^atleast(\d+)\((.+)\)$", condition)
        if not match:
            raise ValueError("Invalid condition: %s" % condition)
        minimum, members = match.groups()
        return sum(matches_condition(token, stats, recipe, items, ingredients)
                   for token in members.split("|")) >= int(minimum)
    match = _COMPARISON.match(condition)
    if match:
        key, op, value = match.groups()
        left, right = _value(key, stats, recipe, items, ingredients), float(value)
        return {">=": left >= right, "<=": left <= right, "==": left == right,
                ">": left > right, "<": left < right}[op]
    return _value(condition, stats, recipe, items, ingredients) >= 1


def matches_recipe(recipe, stats, items, ingredients):
    return (all(matches_condition(rule, stats, recipe, items, ingredients) for rule in recipe["required"])
            and all(matches_condition(rule, stats, recipe, items, ingredients) for rule in recipe["limit"]))


def flavor_conflict(recipe, stats, config):
    matrix = config["flavor_matrix"][recipe["flavor_domain"]]
    total = 0
    for flavor, status in matrix.items():
        load = stats["degrees"][flavor + "_load"]
        if not load or status == "OK":
            continue
        tolerance = recipe["flavor_tolerance_override"].get(flavor)
        if tolerance is None:
            tolerance = 1 if status == "RECIPE" and flavor in recipe["flavor_allow"] else 0
        total += max(0, load - tolerance)
    return total


def recipe_target(recipe, ingredient_count):
    target = recipe["Target"]
    if target is None:
        return None
    if ingredient_count <= 6:
        return target
    return int(math.ceil(target * (1 + 0.125 * (ingredient_count - 6))))


def formula_target(recipe, config):
    """Recalculate a table Target after a designer changes Technique or R."""
    if recipe["spec"] is None or recipe["Technique"] is None or recipe["R"] is None:
        return None
    base = config["specs"][recipe["spec"]]["SpecBase"]
    return int(math.floor((base + max(0, 2 * recipe["R"] - 8)) * (1 + recipe["Technique"])))


def formula_budget(recipe, config):
    if recipe["spec"] is None or recipe["R"] is None:
        return None
    spec = config["specs"][recipe["spec"]]
    return recipe["R"] * spec["M"] + spec["B"]


def r_from_slots(structure=False, structural_ingredients=(), concrete_slots=(),
                 category_slots=(), ingredients=None):
    """Compute recipe R from authored slots, never from the player's actual filler."""
    if ingredients is None:
        ingredients, _, _ = load_tables()
    score = 1.0 if structure else 0.0
    value_seen = set()
    for name in structural_ingredients:
        if name not in value_seen:
            score += {3: 1.0, 4: 2.0, 5: 2.5, 6: 3.0}.get(ingredients[name]["fixed"], 0)
            value_seen.add(name)
    concrete_seen = Counter()
    for name in concrete_slots:
        concrete_seen[name] += 1
        score += 2.0 if concrete_seen[name] == 1 else 0.5
        if concrete_seen[name] == 1 and name not in value_seen:
            score += {3: 1.0, 4: 2.0, 5: 2.5, 6: 3.0}.get(ingredients[name]["fixed"], 0)
            value_seen.add(name)
    category_seen = Counter()
    for category in category_slots:
        category_seen[category] += 1
        score += 1.0 if category_seen[category] == 1 else 0.5
    return score


def _processing_result(items, ingredients):
    if len(items) != 1:
        return None
    name = _item_id(items[0])
    outputs = {"咖啡豆": "咖啡粉", "茶叶": "抹茶粉", "可可": "可可粉",
               "红豆": "豆沙", "绿豆": "豆沙"}
    if name in outputs:
        return {"id": outputs[name], "fixed": ingredients[name]["fixed"]}
    if "fruit" in ingredients[name]["categories"]:
        return {"id": "果酱", "fixed": ingredients[name]["fixed"]}
    if ingredients[name]["processed"]:
        return {"id": name, "fixed": items[0].get("fixed", ingredients[name]["fixed"]) if isinstance(items[0], dict) else ingredients[name]["fixed"]}
    return None


def preview(items, ingredients=None, recipes=None, config=None):
    if ingredients is None or recipes is None or config is None:
        ingredients, recipes, config = load_tables()
    items = list(items)
    stats = aggregate(items, ingredients)
    candidates = []
    for recipe in recipes:
        if matches_recipe(recipe, stats, items, ingredients):
            candidates.append({"recipe": recipe, "conflict": flavor_conflict(recipe, stats, config),
                               "target": recipe_target(recipe, len(items))})
    if not candidates:
        processed = _processing_result(items, ingredients)
        if processed:
            return {"kind": "processed", "item": processed, "stats": stats, "candidates": []}
        return {"kind": "wet_goop_no_recipe", "stats": stats, "candidates": [],
                "target": config["wet_goop_target"]}
    minimum = min(candidate["conflict"] for candidate in candidates)
    candidates = [c for c in candidates if c["conflict"] == minimum]
    highest = max(c["recipe"]["parse_priority"] for c in candidates)
    candidates = [c for c in candidates if c["recipe"]["parse_priority"] == highest]
    beaten = {name for c in candidates for name in c["recipe"]["overrides"]}
    candidates = [c for c in candidates if c["recipe"]["id"] not in beaten] or candidates
    targets = [c["target"] for c in candidates]
    target = min(targets) if all(t is not None for t in targets) else None
    return {"kind": "recipe", "stats": stats, "candidates": candidates, "target": target}


def frozen(instance, key, generator):
    values = instance.setdefault("saved_random", {})
    if key not in values:
        values[key] = generator()
    return values[key]


def _weighted_quality(rank, config, rng):
    roll = rng.random() * 100
    for label, weight in config["quality_roll"][rank]:
        roll -= weight
        if roll < 0:
            return label
    return config["quality_roll"][rank][-1][0]


def _result_rank(score, target, rolls, faces):
    if score >= 2 * target:
        return "big_success" if len(rolls) >= 2 and all(a == max(b) for a, b in zip(rolls, faces)) else "hard_success"
    if score >= target:
        return "success"
    return "big_failure" if len(rolls) >= 2 and sum(rolls) == sum(min(f) for f in faces) else "failure"


def display_name(recipe, stats):
    variants = recipe.get("display_variants", {})
    for ingredient, name in variants.items():
        if stats["count"][ingredient] and sum(stats["count"][other] for other in variants if other != ingredient) == 0:
            return name
    return recipe["name"]


def cook(instance, dice_faces, cooking_level, skill_fixed=0, energy=None,
         ingredients=None, recipes=None, config=None, rng=None):
    """Settle one pending instance; the same instance always returns its first result."""
    if "result" in instance:
        return instance["result"]
    if ingredients is None or recipes is None or config is None:
        ingredients, recipes, config = load_tables()
    rng = rng or random
    items = instance["ingredients"]
    view = preview(items, ingredients, recipes, config)
    if view["kind"] == "processed":
        if energy is not None and energy < 1:
            return {"status": "insufficient_energy", "energy_cost": 1}
        result = {"status": "processed", "item": view["item"], "energy_cost": 1}
        instance["result"] = result
        return result
    if view["target"] is None:
        return {"status": "configuration_pending", "reason": "WetGoopTarget" if view["kind"] == "wet_goop_no_recipe" else "Target/Spec/Technique/R/Budget"}
    if not 1 <= len(dice_faces) <= 3:
        raise ValueError("Cooking check uses 1 to 3 DEX/INT dice")
    faces = [list(range(1, die + 1)) if isinstance(die, int) else list(die) for die in dice_faces]
    if any(not face for face in faces):
        raise ValueError("Cooking die has no faces")
    cost = 2 if len(faces) == 3 else 1
    if energy is not None and energy < cost:
        return {"status": "insufficient_energy", "energy_cost": cost}
    selected = None
    if view["kind"] == "recipe":
        pool = view["candidates"]
        selected_id = frozen(instance, "candidate_choice", lambda: rng.choice(pool)["recipe"]["id"])
        selected = next(c for c in pool if c["recipe"]["id"] == selected_id)
    rolls = frozen(instance, "dice_rolls", lambda: [rng.choice(face) for face in faces])
    if len(rolls) != len(faces):
        raise ValueError("Frozen dice count differs from current selection")
    stats = view["stats"]
    co = config["coefficients"]
    score = sum(rolls) * co["C_dice"] + (cooking_level + stats["fixed_total"] + skill_fixed) * co["C_fixed"]
    rank = _result_rank(score, view["target"], rolls, faces)
    quality_roll = frozen(instance, "quality_roll", lambda: _weighted_quality(rank, config, rng))
    conflict = selected["conflict"] if selected else None
    if conflict is None or conflict >= 3:
        quality = "潮湿黏糊"
    elif conflict == 2:
        quality = "奇怪的" if quality_roll != "潮湿黏糊" else "潮湿黏糊"
    elif conflict == 1:
        strange = frozen(instance, "conflict_label_roll", lambda: rng.random() < .5)
        quality = "潮湿黏糊" if quality_roll == "潮湿黏糊" else "奇怪的" if strange else quality_roll
    else:
        quality = quality_roll
    count = len(items)
    large = frozen(instance, "large_portion_roll", lambda: count >= 8 or count >= 6 and rng.random() < .5)
    recipe = selected["recipe"] if selected else None
    satiety = config["specs"][recipe["spec"]]["satiety"] * (2 if large else 1) if recipe and recipe["spec"] else None
    base_budget = recipe["Budget"] if recipe else None
    multiplier = config["quality_multiplier"].get(quality)
    result = {
        "status": "cooked", "recipe_id": recipe["id"] if recipe else None,
        "name": display_name(recipe, stats) if recipe else "潮湿黏糊", "quality": quality,
        "rank": rank, "rolls": rolls, "score": score, "target": view["target"],
        "conflict": conflict, "large_portion": large, "satiety": satiety,
        "base_budget": base_budget,
        "final_budget": base_budget * multiplier if base_budget is not None and multiplier is not None else None,
        "effect_probability_multiplier": 1.5 if large else 1,
        "xp_delta": config["result_xp"][rank] + (config["quality_xp_per_satiety"][quality] * satiety if satiety is not None else 0),
        "energy_cost": cost,
    }
    instance["result"] = result
    return result


def xp_thresholds(first=35, count=20):
    """Per-level and cumulative XP using the table's half-up integer rounding."""
    values = []
    required = first
    cumulative = 0
    for _ in range(count):
        cumulative += required
        values.append((required, cumulative))
        required = int(math.floor(required * 1.2 + .5))
    return values


def quick_cook_unlocked(mastery, recipe_id, quality="普通的"):
    entry = mastery.get(recipe_id, {})
    return entry.get("total", 0) >= 20 and (quality == "普通的" or entry.get(quality, 0) >= 20)


def quick_cook(instance, recipe_id, mastery, quality="普通的", energy=None,
               ingredients=None, recipes=None, config=None, rng=None):
    """Produce an unlocked recipe without a cooking check or result XP."""
    if "result" in instance:
        return instance["result"]
    if ingredients is None or recipes is None or config is None:
        ingredients, recipes, config = load_tables()
    recipe = next((row for row in recipes if row["id"] == recipe_id), None)
    if recipe is None:
        raise ValueError("Unknown recipe: %s" % recipe_id)
    if not quick_cook_unlocked(mastery, recipe_id, quality):
        return {"status": "mastery_required"}
    if energy is not None and energy < 1:
        return {"status": "insufficient_energy", "energy_cost": 1}
    items = instance["ingredients"]
    stats = aggregate(items, ingredients)
    if not matches_recipe(recipe, stats, items, ingredients):
        return {"status": "invalid_ingredients"}
    if recipe["spec"] is None or recipe["Budget"] is None:
        return {"status": "configuration_pending", "reason": "Spec/Budget"}
    rng = rng or random
    count = len(items)
    conflict = flavor_conflict(recipe, stats, config)
    if conflict >= 3:
        final_quality = "潮湿黏糊"
    elif conflict == 2 or (conflict == 1 and frozen(instance, "conflict_label_roll", lambda: rng.random() < .5)):
        final_quality = "奇怪的"
    else:
        final_quality = quality
    large = frozen(instance, "large_portion_roll", lambda: count >= 8 or count >= 6 and rng.random() < .5)
    satiety = config["specs"][recipe["spec"]]["satiety"] * (2 if large else 1)
    result = {
        "status": "cooked", "recipe_id": recipe_id, "name": display_name(recipe, stats),
        "quality": final_quality, "rank": None, "rolls": [], "score": None, "target": None,
        "conflict": conflict, "large_portion": large,
        "satiety": satiety, "base_budget": recipe["Budget"],
        "final_budget": recipe["Budget"] * config["quality_multiplier"][final_quality]
                        if final_quality in config["quality_multiplier"] else None,
        "effect_probability_multiplier": 1.5 if large else 1,
        "xp_delta": config["quality_xp_per_satiety"][final_quality] * satiety,
        "energy_cost": 1,
    }
    instance["result"] = result
    return result


def record_mastery(mastery, result):
    recipe_id = result.get("recipe_id")
    if result.get("status") != "cooked" or recipe_id is None:
        return mastery
    entry = mastery.setdefault(recipe_id, {})
    entry["total"] = entry.get("total", 0) + 1
    label = result["quality"]
    entry[label] = entry.get(label, 0) + 1
    return mastery


def capacity_after(current, spec, config, deliberate_extra=False):
    """Return the next capacity and whether the planned action takes a turn."""
    new = current + config["specs"][spec]["capacity"]
    return {"capacity": new, "message": "时间差不多了，赶紧吃饭" if new == 3 else None,
            "next_turn": bool(deliberate_extra and new > 3)}
