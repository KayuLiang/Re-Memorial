import random
import unittest

from game.systems import rm_core as rm


class AlwaysSuccessRandom(random.Random):
    def random(self):
        return 0.0


class StrengthTrainingBonusRuleTests(unittest.TestCase):
    def test_success_roll_plan_uses_segmented_strength_table(self):
        cases = {
            1: [1.0, 1.0, 1.0],
            6: [1.0, 0.5, 0.5],
            7: [1.0, 1.0],
            12: [1.0],
            13: [1.0],
            20: [0.5],
        }
        for str_value, expected in cases.items():
            with self.subTest(str_value=str_value):
                self.assertEqual(
                    rm.build_strength_training_bonus_rolls(str_value, rm.RESULT_SUCCESS),
                    expected,
                )

    def test_hard_and_big_success_grant_max_segment_layers(self):
        cases = (
            (1, rm.RESULT_HARD_SUCCESS, [1.0, 1.0, 1.0]),
            (12, rm.RESULT_HARD_SUCCESS, [1.0, 1.0]),
            (20, rm.RESULT_HARD_SUCCESS, [1.0]),
            (20, rm.RESULT_BIG_SUCCESS, [1.0]),
        )
        for str_value, rank, expected in cases:
            with self.subTest(str_value=str_value, rank=rank):
                self.assertEqual(rm.build_strength_training_bonus_rolls(str_value, rank), expected)

    def test_failure_gets_no_strength_bonus_rolls(self):
        self.assertEqual(rm.build_strength_training_bonus_rolls(1, rm.RESULT_FAILURE), [])
        self.assertEqual(rm.build_strength_training_bonus_rolls(1, rm.RESULT_BIG_FAILURE), [])

    def test_apply_strength_training_bonus_adds_layers_and_keeps_growth_counter(self):
        character = rm.create_initial_character({"str": 1, "dex": 4, "int": 3}, rng=random.Random(1))
        result = rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_HARD_SUCCESS, success=True)

        summary = rm.apply_strength_training_str_bonus(character, result, rng=random.Random(2))

        self.assertEqual(summary["success_count"], 3)
        self.assertEqual(summary["roll_plan"], [1.0, 1.0, 1.0])
        self.assertEqual(rm.current_attribute(character, "str"), 4)
        self.assertEqual(character.attribute_bonus_gain_counters["str"], 3)
        self.assertTrue(all(item["source"] == "test_strength_training" for item in character.attribute_bonuses["str"]))

    def test_apply_strength_training_bonus_uses_current_strength_before_adding_layers(self):
        character = rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(3))
        rm.add_attribute_bonus(character, "str", 9)
        result = rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_HARD_SUCCESS, success=True)

        summary = rm.apply_strength_training_str_bonus(character, result, rng=random.Random(4))

        self.assertEqual(summary["str_value"], 12)
        self.assertEqual(summary["success_count"], 2)

    def test_strength_training_result_applies_bonus_without_using_generic_probability_decay(self):
        character = rm.create_initial_character({"str": 1, "dex": 4, "int": 3}, rng=random.Random(5))
        result = rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_SUCCESS, success=True)

        applied = rm.apply_test_strength_training_result(character, result, rng=AlwaysSuccessRandom(6))

        self.assertEqual(applied["bonus"]["success_count"], 3)
        self.assertEqual(applied["progress_delta"], 2)

    def test_strength_training_bonus_probability_decays_from_existing_strength_bonuses(self):
        character = rm.create_initial_character({"str": 1, "dex": 4, "int": 3}, rng=random.Random(7))
        character.attribute_bonuses["str"] = [{"value": 1, "source": "existing"}]
        result = rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_SUCCESS, success=True)

        summary = rm.apply_strength_training_str_bonus(character, result, rng=AlwaysSuccessRandom(8))

        self.assertEqual(summary["roll_plan"], [0.6667, 0.4, 0.2667])

    def test_strength_training_bonus_decay_is_recomputed_after_each_gained_layer(self):
        character = rm.create_initial_character({"str": 1, "dex": 4, "int": 3}, rng=random.Random(9))
        result = rm.CheckResult(available=True, attribute="str", rank=rm.RESULT_SUCCESS, success=True)

        summary = rm.apply_strength_training_str_bonus(character, result, rng=AlwaysSuccessRandom(10))

        self.assertEqual(summary["base_roll_plan"], [1.0, 1.0, 1.0])
        self.assertEqual(summary["roll_plan"], [1.0, 0.6667, 0.4444])
        self.assertEqual(summary["success_count"], 3)


if __name__ == "__main__":
    unittest.main()
