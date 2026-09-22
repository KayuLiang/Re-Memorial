import random
import unittest

from game.systems import rm_core as rm


class FixedRandom:
    def __init__(self, randoms=None, choices=None, gauss=0.0, integers=None):
        self.randoms = iter(randoms or [])
        self.choices = iter(choices or [])
        self.gauss_value = gauss
        self.integers = iter(integers or [])

    def random(self):
        return next(self.randoms, 0.99)

    def choice(self, values):
        value = next(self.choices, None)
        return values[0] if value is None else value

    def uniform(self, low, high):
        return low + (high - low) * self.random()

    def gauss(self, mean, sigma):
        return mean + sigma * self.gauss_value

    def randint(self, low, high):
        return next(self.integers, low)


class VNextRuleTests(unittest.TestCase):
    def make_player(self):
        return rm.create_initial_character({"str": 3, "dex": 3, "int": 2}, rng=random.Random(1))

    def test_initial_story_statuses_are_explicit_and_idempotent(self):
        player = self.make_player()
        self.assertIsNone(player.ember)
        first = rm.apply_initial_gameplay_statuses(player, FixedRandom(randoms=[0.1]))
        second = rm.apply_initial_gameplay_statuses(player, FixedRandom(randoms=[0.9]))
        self.assertEqual((player.ember, player.ect_residual_days, player.drug_dependence), (180, 30, True))
        self.assertTrue(player.current_weather)
        self.assertTrue(first)
        self.assertEqual(second, [])

    def test_emotion_opposites_and_two_die_threshold(self):
        player = self.make_player()
        rm.add_emotion(player, rm.EMOTION_DISTRACTION, 2)
        rm.add_emotion(player, rm.EMOTION_EXCITEMENT, 1)
        self.assertEqual(rm.emotion_layers(player, rm.EMOTION_DISTRACTION), 1)
        one = rm.perform_check(player, rm.CheckSpec("str", 1, ["str_1"], check_context="story"), FixedRandom(choices=[6]))
        self.assertEqual(one.final_multiplier, 1.0)
        self.assertEqual(rm.emotion_layers(player, rm.EMOTION_DISTRACTION), 1)
        player.energy = 99
        two = rm.perform_check(player, rm.CheckSpec("str", 1, ["str_1", "dex_1"],
            allowed_dice_attributes=("str", "dex"), check_context="story"), FixedRandom(choices=[6, 6]))
        self.assertAlmostEqual(two.final_multiplier, .75)
        self.assertEqual(rm.emotion_layers(player, rm.EMOTION_DISTRACTION), 0)

    def test_bipolar_medicine_pending_duplicate_and_multiplication(self):
        player = self.make_player()
        player.bipolar_ember = 180
        for medicine in ("lithium", "aripiprazole"):
            rm.add_medicine_stock(player, medicine, 2)
            self.assertTrue(rm.take_medicine(player, medicine, FixedRandom(randoms=[.9]))["available"])
        duplicate = rm.take_medicine(player, "lithium", confirm_repeat=False)
        self.assertEqual(duplicate["reason"], "repeat_confirmation_required")
        self.assertEqual(player.medicine_counts["lithium"], 1)
        base = rm.bipolar_ember_delta(player, FixedRandom(randoms=[0.0, 0.0]))
        self.assertEqual(base, 9)  # floor(15 * .85 * .75)
        self.assertEqual(dict(player.pending_bipolar_medications), {})

    def test_immediate_medicines_use_pow_mood_path(self):
        player = self.make_player()
        for medicine in ("venlafaxine", "trazodone", "alprazolam"):
            rm.add_medicine_stock(player, medicine, 1)
        player.mood = 0
        self.assertGreater(rm.take_medicine(player, "venlafaxine")["mood_delta"], 0)
        rm.add_emotion(player, rm.EMOTION_ANXIETY)
        rm.take_medicine(player, "alprazolam")
        self.assertEqual(rm.emotion_layers(player, rm.EMOTION_ANXIETY), 0)
        rm.take_medicine(player, "trazodone")
        self.assertEqual(player.trazodone_sleep_bonus_day, player.day)

    def test_weather_generation_uses_season_and_weather_offsets(self):
        player = self.make_player()
        generated = rm.generate_weather(player, season="winter", override=rm.WEATHER_HEAVY_SNOW,
            rng=FixedRandom(gauss=0.0))
        self.assertEqual(generated, {"weather": rm.WEATHER_HEAVY_SNOW, "temperature": 0, "band": "extreme_cold"})
        for season in rm.SEASONS:
            self.assertEqual(sum(rm.WEATHER_WEIGHTS[season]), 100)

    def test_environment_disease_has_first_day_damage_then_recovery_before_damage(self):
        player = self.make_player()
        player.current_temperature = 0
        events = rm.trigger_environment_disease(player, "cold", FixedRandom(integers=[4]))
        health_after_acquisition = player.health
        self.assertIn("health_damage:4", events)
        self.assertEqual(rm.settle_environment_diseases_morning(player, FixedRandom(randoms=[0.0])), [])
        player.day += 1
        events = rm.settle_environment_diseases_morning(player, FixedRandom(randoms=[0.0]))
        self.assertIn("environment_disease_cured:cold", events)
        self.assertEqual(player.health, health_after_acquisition + 5)

    def test_sleep_quality_poor_adds_half_cap_and_never_sets_to_half(self):
        player = self.make_player()
        player.energy = 2
        check = rm.perform_sleep_quality_check(player, FixedRandom(choices=[1, 1]))
        self.assertEqual(check.quality, rm.SLEEP_QUALITY_POOR)
        maximum = rm.energy_max(player)
        recovery = rm.restore_sleep_energy(player, check.quality, night_main=True)
        self.assertEqual(recovery["after"], min(maximum, 2 + maximum // 2))

    def test_excellent_night_sleep_adds_fixed_cap_after_percent_bonus(self):
        player = self.make_player()
        player.good_routine = True
        player.energy = 0
        base = int(1.5 * sum(d.expectation() for d in player.dice_for("con")))
        rm.restore_sleep_energy(player, rm.SLEEP_QUALITY_EXCELLENT, night_main=True)
        self.assertEqual(rm.energy_max(player), int(base * 1.25) + 1)
        self.assertEqual(player.energy, rm.energy_max(player))

    def test_night_snack_consumes_a_late_night_round_without_daily_cap(self):
        player = self.make_player()
        rm.start_turn(player, "sleep_decision")
        first = rm.choose_night_snack(player)
        second = rm.choose_night_snack(player)
        third = rm.choose_night_snack(player)
        self.assertEqual((first["time_slot"], second["time_slot"], third["time_slot"]),
            ("night_break_1", "night_break_2", "forced_sleep"))
        self.assertEqual(player.night_actions_completed, 3)

    def test_time_habit_is_rolling_five_of_seven_and_limited_to_three(self):
        player = self.make_player()
        for day in range(1, 6):
            player.day = day
            rm.record_time_habit_action(player, "study", "morning_1")
        self.assertTrue(player.time_habits["morning:study"])
        spec = rm.CheckSpec("int", 1, schedule_category="study")
        player.current_time_slot = "morning_2"
        self.assertEqual(rm.time_habit_energy_discount(player, spec), 1)
        player.day = 12
        rm.refresh_time_habits(player)
        self.assertFalse(player.time_habits)

    def test_space_rules_modify_only_named_positive_output(self):
        self.assertEqual(rm.apply_space_reward(9, "gym", "training"), 11)
        self.assertEqual(rm.apply_space_reward(-9, "gym", "training"), -9)
        self.assertEqual(rm.apply_space_reward(9, "home", "mood"), 10)
        self.assertEqual(rm.apply_space_reward(9, "home", "energy", rest=True), 9)

    def test_nutrition_disease_aggravates_and_medicine_costs_formal_attribute(self):
        player = self.make_player()
        player.digestive_disorder = rm.RevertableDict(layers=1, last_trigger_day=1)
        player.hunger_level = -1
        events = rm.consume_food(player, "dessert", FixedRandom(integers=[3]))
        self.assertIn("digestive_disorder_aggravated", events)
        self.assertEqual(player.digestive_disorder["layers"], 2)
        before = player.formal_attributes["dex"]
        rm.treat_nutrition_disease(player, "digestive", "medicine")
        self.assertEqual(player.formal_attributes["dex"], before - 2)
        self.assertIsNone(player.digestive_disorder)

    def test_alcohol_uses_combined_social_modifier_and_forced_sleep_hook(self):
        player = self.make_player()
        for _ in range(3):
            rm.consume_alcohol(player, FixedRandom(randoms=[.9]))
        social = rm.CheckSpec("str", 1, social=True, check_context="story")
        ordinary = rm.CheckSpec("str", 1, social=False, check_context="story")
        self.assertAlmostEqual(rm.alcohol_check_multiplier(player, social), 1.40)
        self.assertAlmostEqual(rm.alcohol_check_multiplier(player, ordinary), .85)
        rm.consume_alcohol(player, FixedRandom(randoms=[.9]))
        events = rm.consume_alcohol(player, FixedRandom(randoms=[.9]))
        self.assertIn("forced_drunk_sleep", events)
        self.assertIn("drunk_hospital_event_hook", events)


if __name__ == "__main__":
    unittest.main()
