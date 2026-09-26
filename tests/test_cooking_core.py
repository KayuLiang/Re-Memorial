import copy
import random
import unittest

from game.systems import cooking_core as cooking
from game.systems import rm_core


class CookingCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ingredients, cls.recipes, cls.config = cooking.load_tables()

    def view(self, *items, recipes=None, config=None):
        return cooking.preview(items, self.ingredients, recipes or self.recipes, config or self.config)

    def names(self, view):
        return [item["recipe"]["name"] for item in view.get("candidates", [])]

    def test_recipe_table_is_complete_and_formula_driven(self):
        self.assertEqual(len(self.recipes), 138)
        for recipe in self.recipes:
            for key in ("required", "limit", "Technique", "R", "Target", "Budget", "anti"):
                self.assertIn(key, recipe)
            if recipe["name"] == "扬州炒饭":
                self.assertIsNone(recipe["Target"])
                self.assertIsNone(recipe["Budget"])
            else:
                self.assertEqual(recipe["Target"], cooking.formula_target(recipe, self.config), recipe["name"])
                self.assertAlmostEqual(recipe["Budget"], cooking.formula_budget(recipe, self.config), places=6)
        self.assertEqual(cooking.r_from_slots(structure=True, structural_ingredients=["干酪"],
                                              ingredients=self.ingredients), 3)
        self.assertEqual(cooking.r_from_slots(concrete_slots=["禽肉"] * 3,
                                              ingredients=self.ingredients), 4)

    def test_patch_priorities_and_yangzhou_three_of_four(self):
        self.assertEqual(self.names(self.view("米饭", "鲜虾", "蛋", "青菜")), ["扬州炒饭"])
        self.assertNotIn("扬州炒饭", self.names(self.view("米饭", "鲜虾", "蛋")))
        self.assertEqual(self.names(self.view("米饭", "鲜虾", "蛋", "青菜", "螃蟹", "豆腐")), ["蟹黄豆腐"])
        self.assertEqual(self.names(self.view("米饭", "青菜")), ["什锦炒饭"])

    def test_flavor_competes_before_priority_and_final_pool_controls_target(self):
        recipes = copy.deepcopy(self.recipes[:2])
        for row in recipes:
            row["required"] = ["水"]
            row["limit"] = []
            row["flavor_domain"] = "savory_meat"
            row["parse_priority"] = 100
            row["Target"] = 12
        recipes[0]["parse_priority"] = 400
        recipes[0]["Target"] = 4
        recipes[0]["flavor_tolerance_override"] = {"matcha": 0}
        recipes[1]["flavor_tolerance_override"] = {"matcha": 1}
        view = self.view("水", "抹茶粉", recipes=recipes)
        self.assertEqual(self.names(view), [recipes[1]["name"]])
        self.assertEqual(view["target"], 12)

    def test_same_tier_override_then_frozen_uniform_choice(self):
        recipes = copy.deepcopy(self.recipes[:3])
        for index, row in enumerate(recipes):
            row["required"] = ["水"]
            row["limit"] = []
            row["parse_priority"] = 100
            row["Target"] = 4 + index
        recipes[0]["overrides"] = [recipes[2]["id"]]
        view = self.view("水", recipes=recipes)
        self.assertEqual(self.names(view), [recipes[0]["name"], recipes[1]["name"]])
        self.assertEqual(view["target"], 4)
        instance = {"ingredients": ["水"], "saved_random": {}}
        first = cooking.cook(instance, [6, 6], 0, ingredients=self.ingredients,
                             recipes=recipes, config=self.config, rng=random.Random(3))
        self.assertIn(first["recipe_id"], (recipes[0]["id"], recipes[1]["id"]))
        self.assertEqual(first["target"], 4)
        self.assertEqual(cooking.cook(instance, [20], 99, ingredients=self.ingredients,
                                      recipes=recipes, config=self.config), first)

    def test_degrees_and_processed_categories(self):
        stats = cooking.aggregate(["茶叶", "抹茶粉", "咖啡豆", "咖啡粉", "可可", "可可粉",
                                   "橘子", "香辛料", "普通蘑菇", "豆腐", "番茄酱", "果酱", "豆沙"],
                                  {**self.ingredients, "果酱": {**self.ingredients["果酱"], "fixed": 2}})
        degrees = stats["degrees"]
        self.assertEqual((degrees["tea_degree"], degrees["matcha_load"]), (2, 1))
        self.assertEqual((degrees["coffee_degree"], degrees["coffee_load"]), (2, 2))
        self.assertEqual((degrees["cocoa_degree"], degrees["cocoa_load"]), (2, 2))
        self.assertEqual(degrees["acid_degree"], 1)
        self.assertEqual(degrees["curry_vegetable_degree"], 2)
        self.assertEqual(degrees["curry_degree"], 1.5)
        self.assertEqual(degrees["vegetable_degree"], 0)
        self.assertEqual(stats["raw_produce_types"], 1)

    def test_water_and_domain_limits(self):
        self.assertEqual(self.names(self.view("面粉", "水")), ["疙瘩汤"])
        self.assertNotIn("什锦炒饭", self.names(self.view("米饭", "水", "青菜")))
        self.assertNotIn("素食沙拉", self.names(self.view("青菜", "番茄", "蛋")))
        self.assertEqual(self.view("可可", "水")["kind"], "wet_goop_no_recipe")
        self.assertNotIn("炸鱼排", self.names(self.view("鱼肉", "黄油")))

    def test_filler_and_special_meat_limits(self):
        turkey = next(row for row in self.recipes if row["name"] == "火鸡正餐")
        self.assertTrue(cooking.matches_recipe(turkey, cooking.aggregate(["禽肉"] * 3 + ["糖"], self.ingredients),
                                               ["禽肉"] * 3 + ["糖"], self.ingredients))
        self.assertFalse(cooking.matches_recipe(turkey, cooking.aggregate(["禽肉"] * 3 + ["兽肉"], self.ingredients),
                                                ["禽肉"] * 3 + ["兽肉"], self.ingredients))
        chicken = next(row for row in self.recipes if row["name"] == "鸡汤拉面")
        self.assertFalse(cooking.matches_recipe(chicken, cooking.aggregate(["方便面", "水", "禽肉", "兽肉"], self.ingredients),
                                                ["方便面", "水", "禽肉", "兽肉"], self.ingredients))

    def test_wet_goop_branches_and_pending_target(self):
        self.assertEqual(self.view("水", "糖")["kind"], "wet_goop_no_recipe")
        pending = cooking.cook({"ingredients": ["水", "糖"], "saved_random": {}}, [6, 6], 0,
                               ingredients=self.ingredients, recipes=self.recipes, config=self.config)
        self.assertEqual(pending["status"], "configuration_pending")
        self.assertEqual(pending["reason"], "WetGoopTarget")
        view = self.view("禽肉", "抹茶粉", "咖啡粉", "可可粉")
        self.assertEqual(view["kind"], "recipe")
        self.assertGreaterEqual(view["candidates"][0]["conflict"], 3)
        result = cooking.cook({"ingredients": ["禽肉", "抹茶粉", "咖啡粉", "可可粉"], "saved_random": {}},
                              [6, 6], 0, ingredients=self.ingredients, recipes=self.recipes,
                              config=self.config, rng=random.Random(2))
        self.assertEqual(result["quality"], "潮湿黏糊")
        self.assertIsNotNone(result["target"])

    def test_random_is_frozen_for_entire_instance(self):
        instance = {"ingredients": ["米饭", "蛋", "青菜", "油", "酱油", "糖"], "saved_random": {}}
        first = cooking.cook(instance, [6, 6], 0, ingredients=self.ingredients, recipes=self.recipes,
                             config=self.config, rng=random.Random(1))
        second = cooking.cook(instance, [20, 20, 20], 99, ingredients=self.ingredients, recipes=self.recipes,
                              config=self.config, rng=random.Random(99))
        self.assertEqual(first, second)
        self.assertIn("dice_rolls", instance["saved_random"])
        self.assertIn("quality_roll", instance["saved_random"])

    def test_size_target_and_budget_boundaries(self):
        recipe = next(row for row in self.recipes if row["name"] == "什锦炒饭")
        self.assertEqual(cooking.recipe_target(recipe, 6), 15)
        self.assertEqual(cooking.recipe_target(recipe, 7), 17)
        self.assertEqual(cooking.recipe_target(recipe, 8), 19)
        self.assertEqual(cooking.capacity_after(2, "饮料", self.config)["message"], "时间差不多了，赶紧吃饭")
        self.assertFalse(cooking.capacity_after(3, "饮料", self.config)["next_turn"])
        self.assertTrue(cooking.capacity_after(3, "饮料", self.config, deliberate_extra=True)["next_turn"])

    def test_single_ingredient_processing_and_passthrough(self):
        self.assertEqual(self.view("茶叶")["item"], {"id": "抹茶粉", "fixed": 3})
        self.assertEqual(self.view("抹茶粉")["item"], {"id": "抹茶粉", "fixed": 3})
        self.assertEqual(self.view("榴莲")["item"], {"id": "果酱", "fixed": 5})

    def test_mastery_and_quick_cook(self):
        recipe = next(row for row in self.recipes if row["name"] == "美式咖啡")
        mastery = {recipe["id"]: {"total": 20, "美味的": 20}}
        self.assertTrue(cooking.quick_cook_unlocked(mastery, recipe["id"], "美味的"))
        self.assertFalse(cooking.quick_cook_unlocked(mastery, recipe["id"], "完美的"))
        result = cooking.quick_cook({"ingredients": ["咖啡豆", "水"], "saved_random": {}}, recipe["id"],
                                    mastery, "美味的", energy=1, ingredients=self.ingredients,
                                    recipes=self.recipes, config=self.config)
        self.assertEqual(result["status"], "cooked")
        self.assertIsNone(result["rank"])
        self.assertEqual(result["energy_cost"], 1)

    def test_hunger_record_on_increase_not_at_meal_end(self):
        player = rm_core.create_initial_character()
        player.hunger_level = 2
        rm_core.begin_meal_node(player)
        self.assertEqual(len(player.severe_hunger_history), 0)
        rm_core.finish_meal_node(player)
        self.assertEqual(len(player.severe_hunger_history), 0)
        rm_core.add_hunger(player)
        self.assertEqual(len(player.severe_hunger_history), 1)
        rm_core.add_hunger(player, 2, rng=random.Random(1))
        self.assertIsNotNone(player.malnutrition)

    def test_satiety_progress_lasts_until_next_formal_meal(self):
        player = rm_core.create_initial_character()
        rm_core.consume_food(player, "饮料")
        self.assertEqual(player.meal_satiety_progress, 1)
        rm_core.finish_meal_node(player)
        self.assertEqual(player.meal_satiety_progress, 1)
        rm_core.begin_meal_node(player)
        self.assertEqual(player.meal_satiety_progress, 0)
        rm_core.consume_food(player, "甜品")
        self.assertEqual(player.hunger_level, 0)
        self.assertEqual(player.meal_satiety_progress, 0)


if __name__ == "__main__":
    unittest.main()
