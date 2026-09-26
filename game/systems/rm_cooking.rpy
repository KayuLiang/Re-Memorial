default rm_cooking_stock = []
default rm_cooking_pending = None
default rm_cooking_mastery = {}
default rm_cooking_xp_deltas = []
default rm_cooking_session_serial = 0

init -17 python:
    from renpy.revertable import RevertableDict, RevertableList
    from game.systems import cooking_core

    def rm_cooking_add_ingredient(item):
        """Inventory grant hook for authored shops, gathering and events."""
        ingredients, _, _ = cooking_core.load_tables()
        name = item if isinstance(item, str) else item["id"]
        if name not in ingredients:
            raise ValueError("Unknown cooking ingredient: {}".format(name))
        store.rm_cooking_stock.append(item)

    def rm_cooking_preview(items):
        return cooking_core.preview(items)

    def rm_cooking_start(items):
        """Keep one pending pot across menu exits and Ren'Py save/load."""
        if store.rm_cooking_pending is not None:
            return store.rm_cooking_pending
        remaining = list(store.rm_cooking_stock)
        for item in items:
            if item not in remaining:
                raise ValueError("Ingredient unavailable: {}".format(item))
            remaining.remove(item)
        store.rm_cooking_session_serial += 1
        store.rm_cooking_pending = RevertableDict(
            id="cook_{}".format(store.rm_cooking_session_serial),
            ingredients=RevertableList(items), saved_random=RevertableDict())
        return store.rm_cooking_pending

    def rm_cooking_commit(dice_ids, cooking_level=None, skill_fixed=0):
        pending = store.rm_cooking_pending
        if pending is None:
            raise ValueError("No pending cooking instance")
        if cooking_level is None:
            return {"status": "configuration_pending", "reason": "Cooking initial level"}
        player = rm_ensure_player()
        dice = [player.find_die(die_id) for die_id in dice_ids]
        if any(die is None or die.attribute not in ("dex", "int") or die.is_sealed() for die in dice):
            raise ValueError("Cooking accepts only usable DEX/INT dice")
        if len(set(dice_ids)) != len(dice_ids):
            raise ValueError("A die may be selected once")
        result = cooking_core.cook(
            pending, [die.faces for die in dice], cooking_level,
            skill_fixed=skill_fixed, energy=player.energy, rng=renpy.random)
        return rm_cooking_apply_result(result, player)

    def rm_cooking_commit_quick(recipe_id, quality="普通的"):
        pending = store.rm_cooking_pending
        if pending is None:
            raise ValueError("No pending cooking instance")
        player = rm_ensure_player()
        result = cooking_core.quick_cook(
            pending, recipe_id, store.rm_cooking_mastery, quality,
            energy=player.energy, rng=renpy.random)
        return rm_cooking_apply_result(result, player)

    def rm_cooking_apply_result(result, player):
        pending = store.rm_cooking_pending
        if result["status"] in ("cooked", "processed") and not pending.get("applied"):
            for item in pending["ingredients"]:
                store.rm_cooking_stock.remove(item)
            player.energy -= result["energy_cost"]
            if result["status"] == "processed":
                store.rm_cooking_stock.append(result["item"])
            else:
                store.rm_cooking_xp_deltas.append(result["xp_delta"])
                if result["recipe_id"] is not None:
                    recipe_id = result["recipe_id"]
                    entry = dict(store.rm_cooking_mastery.get(recipe_id, {}))
                    entry["total"] = entry.get("total", 0) + 1
                    entry[result["quality"]] = entry.get(result["quality"], 0) + 1
                    store.rm_cooking_mastery[recipe_id] = entry
            pending["applied"] = True
        return result

    def rm_cooking_close():
        """Close the settled pot; uncommitted pots remain pending."""
        if store.rm_cooking_pending and store.rm_cooking_pending.get("applied"):
            store.rm_cooking_pending = None
