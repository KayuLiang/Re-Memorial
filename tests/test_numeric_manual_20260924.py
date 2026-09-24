import random
import unittest

from game.systems import rm_core as rm


class FixedRandom:
    def __init__(self, choices=(), randoms=(), integers=()):
        self.choices = iter(choices)
        self.randoms = iter(randoms)
        self.integers = iter(integers)

    def choice(self, values):
        return next(self.choices, values[0])

    def random(self):
        return next(self.randoms, .99)

    def randint(self, low, high):
        return next(self.integers, low)


class NumericManualTests(unittest.TestCase):
    def player(self):
        return rm.create_initial_character(rng=random.Random(1))

    def test_normal_pool_floor_precedes_independent_palpitations(self):
        state = self.player()
        state.current_pain = 10
        state.palpitations = True
        spec = rm.CheckSpec("str", 10, ["str_1"])
        self.assertAlmostEqual(rm.check_final_multiplier(state, spec, 1), .50 * .85)
        self.assertEqual(rm.check_advantage_counts(state, spec)[1], 1)

    def test_multiple_bonus_rerolls_player_selected_same_die(self):
        state = self.player()
        state.dice_pool = [rm.RMDice("a", "str", [1, 4]), rm.RMDice("b", "str", [1, 4])]
        state.energy = 10
        state.long_emotions["confidence"] = True
        rm.add_emotion(state, rm.EMOTION_JOY)
        spec = rm.CheckSpec("str", 5, ["a", "b"], bonus_die_ids=["b", "b"])
        result = rm.perform_check(state, spec, FixedRandom(choices=[1, 1, 4, 4]))
        self.assertEqual((result.advantage_count, result.disadvantage_count), (2, 0))
        self.assertEqual([roll["value"] for roll in result.dice_results], [1, 4])
        self.assertEqual(result.dice_results[1]["rolls"], [1, 4, 4])

    def test_shared_training_load_and_failure_injury(self):
        state = self.player()
        rm.add_training_fatigue(state, "test_strength_training", 1)
        self.assertEqual(rm.training_fatigue_layers(state, "test_jogging"), 1)
        self.assertEqual(rm.roll_training_fatigue_requirement_penalty(2, FixedRandom(integers=[4, 6])), 10)
        self.assertEqual(rm.resolve_training_injury(state, rm.RESULT_SUCCESS, 0), [])
        events = rm.resolve_training_injury(state, rm.RESULT_BIG_FAILURE, 0, FixedRandom(integers=[1]))
        self.assertIn("injury:strain:0", events)
        self.assertEqual(state.current_pain, 1)
        self.assertEqual(rm.training_load_dice(7), (4, 6, 8, 10, 12, 20, 20))
        self.assertEqual(rm.training_load_dice(8), (4, 6, 8, 10, 12, 20, 20, 20))
        rm.process_small_rest(state, FixedRandom())
        self.assertEqual(state.training_load, 0)

    def test_growth_thresholds_and_direct_formal_change(self):
        state = self.player()
        rm.add_attribute_bonus(state, "str", 3)
        self.assertEqual(state.growth_reward_pending["str"], 1)
        self.assertEqual(state.dice_growth_progress["str"], 0)
        rm.add_attribute_value(state, "dex", 2)
        self.assertEqual(state.growth_reward_pending["dex"], 1)
        rm.add_formal_attribute(state, "pow", -1)
        self.assertEqual(state.degradation_penalty_pending["pow"], 1)
        self.assertEqual(state.degradation_progress["pow"], 0)

    def test_injury_pain_source_and_repeat_hospital_fracture(self):
        state = self.player()
        for _ in range(4):
            rm.acquire_injury(state, "fracture", FixedRandom(integers=[1, 1, 1, 1]))
        self.assertEqual(state.injuries["fracture"]["reinjury"], 2)
        self.assertEqual(state.current_pain, 12)
        self.assertEqual(state.injuries["fracture"]["pain_source_cap"], 12)
        self.assertEqual(rm.visit_hospital(state, ["fracture"])["pain"], 6)
        self.assertEqual(state.injuries["fracture"]["remaining_days"], 7)
        self.assertFalse(rm.visit_hospital(state, ["fracture"])["available"])
        state.day += 1
        rm.visit_hospital(state, ["fracture"])
        self.assertEqual(state.injuries["fracture"]["remaining_days"], 2)
        rm.clear_injury(state, "fracture")
        self.assertEqual(state.current_pain, 0)

    def test_per_drug_dependency_and_seventh_withdrawal(self):
        state = self.player()
        rm.add_medicine_stock(state, "venlafaxine", 20)
        for day in range(1, 8):
            state.day = day
            state.medicine_taken_today.clear()
            rm.take_medicine(state, "venlafaxine")
            rm.settle_medication_day(state)
        self.assertTrue(state.drug_dependences["venlafaxine"])
        self.assertFalse(state.drug_dependences.get("trazodone", False))
        for day in range(8, 15):
            state.day = day
            state.medicine_taken_today.clear()
            events = rm.settle_medication_day(state)
            self.assertIn("withdrawal:venlafaxine", events)
        self.assertFalse(state.drug_dependences["venlafaxine"])
        self.assertEqual(state.drug_free_days["venlafaxine"], 7)

    def test_hospital_poison_cure_preserves_same_day_risk(self):
        state = self.player()
        rm.add_medicine_stock(state, "painkiller", 3)
        rm.take_ordinary_medicine(state, "painkiller", FixedRandom())
        rm.take_ordinary_medicine(state, "painkiller", FixedRandom(randoms=[0], integers=[1]))
        self.assertTrue(state.ordinary_poisoning)
        self.assertAlmostEqual(state.ordinary_poison_risk, .25)
        rm.visit_hospital(state, ["ordinary_poisoning"])
        self.assertFalse(state.ordinary_poisoning)
        self.assertEqual(state.ordinary_medicine_taken_today["painkiller"], 2)
        self.assertAlmostEqual(state.ordinary_poison_risk, .25)

    def test_existing_poison_damages_on_first_dose_of_next_day(self):
        state = self.player()
        rm.add_medicine_stock(state, "painkiller", 1)
        state.ordinary_poisoning = True
        before = state.health
        result = rm.take_ordinary_medicine(state, "painkiller", FixedRandom(integers=[2]))
        self.assertEqual(before - state.health, 2)
        self.assertIn("health_damage:2", result["events"])

    def test_weather_rain_outdoors_and_severe_weather_block(self):
        state = self.player()
        spec = rm.CheckSpec("con", 8, outdoors=True, sport=True)
        state.current_weather = rm.WEATHER_HEAVY_RAIN
        self.assertTrue(rm.weather_check_effects(state, spec)["available"])
        self.assertAlmostEqual(rm.weather_check_effects(state, spec)["final_multiplier"], .75)
        state.current_weather = rm.WEATHER_STORM
        self.assertFalse(rm.weather_check_effects(state, spec)["available"])

    def test_alcohol_social_bonus_stays_in_normal_pool_and_mood_uses_pow(self):
        state = self.player()
        state.mood = 100
        expected_delta = rm.adjusted_mood_delta(state, 5)
        rm.consume_alcohol(state, FixedRandom())
        self.assertEqual(state.mood, int(100 + expected_delta))
        self.assertEqual(state.intoxication, 1)
        state.emotions[rm.EMOTION_CALM] = 0
        ordinary = rm.CheckSpec("str", 5, ["str_1"])
        social = rm.CheckSpec("str", 5, ["str_1"], social=True)
        self.assertAlmostEqual(rm.check_final_multiplier(state, ordinary, 1), .95)
        self.assertAlmostEqual(rm.check_final_multiplier(state, social, 1), 1.15 * .95)

        state.intoxication = 5
        state.current_pain = 20
        self.assertAlmostEqual(rm.check_final_multiplier(state, social, 1), .50 * .55)

    def test_palpitations_only_triggers_anxiety_when_first_acquired(self):
        state = self.player()
        for _ in range(2):
            rm.consume_coffee(state, FixedRandom())
        self.assertFalse(state.palpitations)
        rm.consume_coffee(state, FixedRandom(randoms=[0, 0]))
        self.assertTrue(state.palpitations)
        self.assertEqual(rm.emotion_layers(state, rm.EMOTION_ANXIETY), 1)
        rm.consume_coffee(state, FixedRandom(randoms=[0, 0]))
        self.assertEqual(rm.emotion_layers(state, rm.EMOTION_ANXIETY), 1)

    def test_enchantment_sources_cancel_opposite_emotion_before_rolling(self):
        state = self.player()
        state.dice_pool = [rm.RMDice("a", "str", [1, 4], rm.ENCHANT_SWIFT)]
        state.energy = 10
        rm.add_emotion(state, rm.EMOTION_SADNESS)
        spec = rm.CheckSpec("str", 3, ["a"])
        result = rm.perform_check(state, spec, FixedRandom(choices=[1]))
        self.assertEqual((result.advantage_count, result.disadvantage_count), (1, 1))
        self.assertEqual(result.dice_results[0]["rolls"], [1])

        rm.remove_emotion(state, rm.EMOTION_SADNESS)
        rm.add_emotion(state, rm.EMOTION_JOY)
        state.dice_pool[0].enchantment = rm.ENCHANT_SLUGGISH
        result = rm.perform_check(state, spec, FixedRandom(choices=[4]))
        self.assertEqual((result.advantage_count, result.disadvantage_count), (1, 1))
        self.assertEqual(result.dice_results[0]["rolls"], [4])

    def test_sleep_uses_selected_bonus_die_and_updates_long_emotion_streak(self):
        state = self.player()
        state.dice_pool = [rm.RMDice("a", "con", [1, 4]), rm.RMDice("b", "con", [1, 4])]
        state.current_weather = rm.WEATHER_LIGHT_RAIN
        result = rm.perform_sleep_quality_check(state, FixedRandom(choices=[1, 1, 4]), ["b"])
        self.assertEqual([row["rolls"] for row in result.dice_results], [[1], [1, 4]])

        state.current_weather = rm.WEATHER_SUNNY
        state.long_emotions["confidence"] = True
        state.check_streak["failure"] = 2
        state.current_pain = 1
        result = rm.perform_sleep_quality_check(state, FixedRandom(choices=[1, 1]))
        self.assertFalse(result.success)
        self.assertIn("confidence_cleared", result.streak_events)
        self.assertFalse(state.long_emotions["confidence"])

    def test_training_location_legality_is_exposed_before_check(self):
        state = self.player()
        state.current_time_slot = "morning_1"
        self.assertEqual(rm.training_schedule_legal(state, "test_strength_training", "park")[1],
                         "training_not_available_in_park")
        self.assertTrue(rm.training_schedule_legal(state, "test_jogging", "park")[0])
        self.assertEqual(rm.training_schedule_legal(state, "test_jogging", "home")[1],
                         "equipment_required")
        state.home_equipment["treadmill"] = True
        self.assertTrue(rm.training_schedule_legal(state, "test_jogging", "home")[0])
        state.current_time_slot = "late_night_1"
        self.assertEqual(rm.training_schedule_legal(state, "test_strength_training", "gym")[1],
                         "gym_closed")
        state.current_weather = rm.WEATHER_STORM
        self.assertEqual(rm.training_schedule_legal(state, "test_jogging", "park")[1],
                         "severe_weather_blocks_outdoors")
        state.current_time_slot = "morning_1"
        state.training_load = 8
        self.assertTrue(rm.training_schedule_legal(state, "test_strength_training", "gym")[0])

    def test_legacy_dependence_and_weather_migrate_once(self):
        state = self.player()
        state.drug_dependence = True
        state.current_weather = rm.WEATHER_THUNDERSTORM
        del state.drug_dependences
        del state.weather_overlays
        rm.ensure_second_stage_state(state)
        self.assertTrue(state.legacy_drug_dependence)
        self.assertEqual((state.current_weather, list(state.weather_overlays)),
                         (rm.WEATHER_HEAVY_RAIN, ["thunder"]))
        rm.ensure_second_stage_state(state)
        self.assertEqual(list(state.weather_overlays), ["thunder"])
        for day in range(1, 8):
            state.day = day
            rm.settle_medication_day(state)
        self.assertFalse(state.legacy_drug_dependence)
        self.assertFalse(state.drug_dependence)

    def test_patch01_habit_counts_distinct_days(self):
        state = self.player()
        for day in range(1, 6):
            state.day = day
            rm.record_time_habit_action(state, "study", "morning_1")
            rm.record_time_habit_action(state, "study", "morning_2")
            self.assertEqual(sum(item["day"] == day and item["category"] == "study"
                                 for item in state.time_habit_history), 1)
        self.assertTrue(state.time_habits["morning:study"])
        state.day = 5
        rm.record_time_habit_action(state, "social", "morning_2")
        self.assertEqual(sum(item["day"] == 5 for item in state.time_habit_history), 2)

    def test_patch01_withdrawal_reuses_k_pow_once(self):
        state = self.player()
        state.formal_attributes["pow"] = 12
        state.mood = 100
        expected = rm.adjusted_mood_delta(state, -5)
        before = state.mood
        rm.apply_withdrawal(state, "venlafaxine")
        self.assertEqual(state.mood, int(before + expected))
        k = rm.calculate_k_pow(state)
        rm.apply_withdrawal(state, "lithium")
        self.assertAlmostEqual(state.withdrawal_ember_multipliers["lithium"][0],
                               1 + .075 / k)
        rm.apply_withdrawal(state, "trazodone")
        state.dice_pool = [rm.RMDice("con", "con", [2, 4])]
        result = rm.perform_sleep_quality_check(state, FixedRandom(choices=[2]))
        self.assertAlmostEqual(result.dice_multiplier, 1 - .075 / k)

    def test_patch01_sport_factor_uses_pow_baseline_and_fixed_offsets(self):
        state = self.player()
        state.formal_attributes["pow"] = 6
        for rank, expected in ((rm.RESULT_SUCCESS, 190),
                               (rm.RESULT_HARD_SUCCESS, 185),
                               (rm.RESULT_BIG_SUCCESS, 180)):
            state.mood = 200
            rm.apply_exercise_mood_return(state, rank)
            self.assertEqual(state.mood, expected)
        state.mood = 200
        rm.apply_exercise_mood_return(state, rm.RESULT_FAILURE)
        self.assertEqual(state.mood, 200)
        state.formal_attributes["pow"] = 12
        state.mood = 200
        rm.apply_exercise_mood_return(state, rm.RESULT_HARD_SUCCESS)
        self.assertEqual(state.mood, 175)


if __name__ == "__main__":
    unittest.main()
