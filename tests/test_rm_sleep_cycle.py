import itertools
import random
import unittest

from game.systems import rm_core as rm


class SleepCycleTests(unittest.TestCase):
    def setUp(self):
        self.player = rm.create_initial_character(rng=random.Random(7))

    def test_six_actions_and_three_meals_end_at_sleep_decision(self):
        p = self.player
        rm.start_day(p)
        sequence = []
        while p.current_time_slot != "sleep_decision":
            sequence.append(p.current_time_slot)
            if p.current_time_slot in rm.MEAL_SLOTS:
                before = (p.energy, p.mood)
                rm.choose_meal(p, True)
                self.assertEqual((p.energy, p.mood), before)
            else:
                rm.advance_time_slot(p)
        self.assertEqual(sequence, ["breakfast", "morning_1", "morning_2", "lunch",
                                   "afternoon_1", "afternoon_2", "dinner", "evening_1", "evening_2"])
        self.assertEqual(p.day, 1)
        self.assertEqual(p.night_actions_completed, 0)

    def test_meal_cannot_be_bypassed_as_action_and_event_sees_choice(self):
        p = self.player
        rm.start_day(p)
        with self.assertRaises(ValueError):
            rm.advance_time_slot(p)
        result = rm.resolve_action(p, rm.ScheduleSpec("mock", "mock"))
        self.assertFalse(result["available"])
        self.assertFalse(rm.end_turn(p, result)["available"])
        calls = []
        rm.choose_meal(p, False, lambda state, slot, eat: calls.append((slot, eat)))
        self.assertEqual(calls, [("breakfast", False)])

    def test_third_night_completes_then_coma_no_fourth_or_automatic_new_day(self):
        p = self.player
        rm.start_turn(p, "sleep_decision")
        for number, destination in enumerate(("night_break_1", "night_break_2", "forced_sleep"), 1):
            result = rm.choose_night_snack(p)
            self.assertTrue(result["available"])
            self.assertEqual(p.current_time_slot, destination)
        self.assertEqual(p.current_time_slot, "forced_sleep")
        self.assertEqual(p.night_actions_completed, 3)
        self.assertEqual(p.day, 1)
        with self.assertRaises(ValueError):
            rm.continue_night(p)

    def test_voluntary_wake_results(self):
        for rank in (rm.RESULT_SUCCESS, rm.RESULT_HARD_SUCCESS, rm.RESULT_BIG_SUCCESS):
            self.assertEqual(rm.wake_outcome(rank), {"skip_morning": 0, "early": True})
        for rank in (rm.RESULT_FAILURE, rm.RESULT_BIG_FAILURE):
            self.assertEqual(rm.wake_outcome(rank), {"skip_morning": 1, "early": False})

    def test_coma_wake_results(self):
        expected = {rm.RESULT_BIG_SUCCESS: (0, True), rm.RESULT_HARD_SUCCESS: (1, True),
                    rm.RESULT_SUCCESS: (2, False), rm.RESULT_FAILURE: (2, False), rm.RESULT_BIG_FAILURE: (2, False)}
        for rank, (skip, early) in expected.items():
            self.assertEqual(rm.wake_outcome(rank, True), {"skip_morning": skip, "early": early})

    def test_wake_check_free_with_zero_energy_and_three_heavy_dice(self):
        p = self.player
        p.energy = 0
        p.dice_pool.append(rm.RMDice("pow_extra", "pow", list(range(1, 21))))
        dice = p.dice_for("pow")
        for die in dice:
            die.enchantment = rm.ENCHANT_HEAVY
        result = rm.perform_wake_check(p, rm.WAKE_REQUIREMENT, [die.id for die in dice], random.Random(8))
        self.assertTrue(result.available)
        self.assertEqual(len(result.dice_results), 3)
        self.assertEqual((result.energy_cost, p.energy), (0, 0))

    def test_initial_all_out_success_is_72_5_percent_at_target_15(self):
        dice = self.player.dice_for("pow")
        totals = [sum(values) + 3 for values in itertools.product(*(die.faces for die in dice))]
        self.assertEqual(sum(totals) / len(totals), 19)
        self.assertEqual(rm.WAKE_REQUIREMENT, 15)
        self.assertEqual(sum(total >= rm.WAKE_REQUIREMENT for total in totals) / len(totals), .725)
        result = rm.perform_wake_check(self.player, rm.WAKE_REQUIREMENT, [die.id for die in dice], random.Random(8))
        self.assertEqual(result.attribute_modifier, 3)
        self.assertEqual(result.extra_modifier, 0)
        self.assertEqual(result.total, result.dice_total + 3)
        ranks = [rm.result_rank(sum(values) + 3, rm.WAKE_REQUIREMENT, sum(values), dice)
                 for values in itertools.product(*(die.faces for die in dice))]
        self.assertIn(rm.RESULT_HARD_SUCCESS, ranks)
        self.assertIn(rm.RESULT_BIG_SUCCESS, ranks)

    def test_wake_curve_uses_formal_pow_and_half_up_rounding(self):
        expected = [15,17,19,20,22,23,24,25,26,27,28,28,28,29,29]
        for value,target in zip(range(6,21),expected):
            self.player.formal_attributes['pow'] = value
            self.assertEqual(rm.wake_requirement(self.player),target)
        for value,target in ((0,15),(5,15),(21,29),(30,29)):
            self.player.formal_attributes['pow'] = value
            self.assertEqual(rm.wake_requirement(self.player),target)
        self.player.formal_attributes['pow'] = 15
        self.player.fatigue_layers = 1
        rm.add_emotion(self.player, rm.EMOTION_DISTRACTION, 1)
        self.player.attribute_values['pow'] = 2
        rm.add_attribute_bonus(self.player,'pow',1)
        self.assertEqual(rm.wake_requirement(self.player),27)
        self.player.mood = 61
        self.player.energy = 0
        result = rm.perform_wake_check(self.player,dice_ids=['pow_1','pow_2'],rng=random.Random(8))
        self.assertEqual(result.base_requirement,27)
        self.assertEqual(result.requirement,32)
        self.assertEqual(result.attribute_modifier,9)
        self.assertEqual(result.extra_modifier,0)
        self.assertEqual(result.energy_cost,0)

    def test_fatigue_and_distraction_do_not_reduce_attributes(self):
        p = self.player
        before = rm.energy_max(p)
        p.fatigue_layers = 2
        rm.add_emotion(p, rm.EMOTION_DISTRACTION, 2)
        p.day = 100
        self.assertEqual(rm.energy_max(p), before - 2)
        self.assertEqual(rm.current_attribute(p, "pow"), 6)
        self.assertEqual(rm.drowsiness_check_modifier(p, "pow"), 0)
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 2)
        self.assertEqual(p.attribute_values["pow"], 0)
        self.assertEqual(p.attribute_bonuses["pow"], [])

    def test_formal_loss_uses_manual_degradation_but_temporary_loss_does_not(self):
        p = self.player
        rm.start_deep_fatigue(p)
        self.assertEqual(p.current_attribute("con"), 5)
        self.assertEqual(p.degradation_penalty_pending["con"], 0)
        rm.add_formal_attribute(p, "con", -2)
        self.assertEqual(p.degradation_penalty_pending["con"], 2)
        rm.add_formal_attribute(p, "con", -10)
        self.assertEqual(p.formal_attributes["con"], 0)
        self.assertEqual(p.degradation_penalty_pending["con"], 6)

    def test_optional_night_holes_appear_only_when_entered(self):
        p = self.player
        rm.start_day(p)
        self.assertEqual(rm.action_clock_progress(p), (6, 0))
        rm.start_turn(p, "sleep_decision")
        for number in range(1, 4):
            rm.continue_night(p)
            self.assertEqual(rm.action_clock_progress(p), (6 + number, 5 + number))
            rm.advance_time_slot(p)
        self.assertEqual(rm.action_clock_progress(p), (9, 9))

    def test_day_settlement_outside_on_time_sleep_does_not_award_routine(self):
        p = self.player
        rm.start_turn(p, "morning_1")
        for _ in range(7):
            rm.end_day(p, random.Random(7))
        self.assertFalse(p.good_routine)
        self.assertEqual(p.good_routine_streak, 0)

    def test_disease_repeated_night_actions_add_one_layer_without_extending_deadline(self):
        p = self.player
        rm.start_deep_fatigue(p)
        rm.start_turn(p, "sleep_decision")
        for _ in range(3):
            rm.continue_night(p)
            rm.advance_time_slot(p)
        self.assertEqual(p.deep_fatigue["layers"], 1)
        rm.begin_sleep(p, random.Random(7))
        rm.finish_wake(p, rm.RESULT_SUCCESS)
        self.assertEqual(p.deep_fatigue["layers"], 2)
        self.assertEqual(p.deep_fatigue["last_night"], 7)
        self.assertTrue(p.deep_fatigue["relapsed"])

    def sleep_night(self, late=0, rank=rm.RESULT_SUCCESS, draws=None):
        p = self.player
        rm.start_turn(p, "sleep_decision")
        for _ in range(late):
            rm.continue_night(p)
            rm.advance_time_slot(p)
        sleep = rm.begin_sleep(p, random.Random(7))
        rng = random.Random(0)
        if draws is not None:
            values = iter(draws)
            rng.random = lambda: next(values)
        wake = rm.finish_wake(p, rank, rng) if sleep["needs_wake_check"] else None
        return sleep, wake

    def test_three_receipts_start_disease_clear_history_and_keep_fatigue(self):
        p = self.player
        for _ in range(3):
            self.sleep_night(1)
        self.assertEqual(p.fatigue_layers, 3)
        self.assertEqual(p.fatigue_history, [])
        self.assertEqual(p.deep_fatigue["layers"], 1)
        self.assertEqual(p.deep_fatigue["first_day"], 4)
        self.assertEqual(p.deep_fatigue["last_night"], 10)
        self.assertEqual((p.current_attribute("pow"), p.current_attribute("con")), (6, 5))
        self.sleep_night(1)
        self.assertEqual(p.deep_fatigue["layers"], 2)
        self.assertEqual(p.deep_fatigue["last_night"], 10)
        self.assertEqual(p.fatigue_layers, 4)
        self.assertEqual(p.fatigue_history, [])

    def test_expired_layers_do_not_trigger_disease(self):
        p = self.player
        p.day = 9
        p.fatigue_history = [8, 9, 10]
        rm.gain_sleep_fatigue(p)
        self.assertIsNone(p.deep_fatigue)
        self.assertEqual(p.fatigue_history, [10, 16])

    def test_shield_blocks_fatigue_and_three_round_minimum_keeps_old_effects(self):
        p = self.player
        p.good_routine = True
        p.fatigue_layers = 1
        rm.add_emotion(p, rm.EMOTION_DISTRACTION, 1)
        p.fatigue_history = [8]
        _, wake = self.sleep_night(3, rm.RESULT_BIG_SUCCESS, [.9, .9, .9, .5])
        self.assertEqual(wake["fatigue"], 0)
        self.assertIn("good_routine_spent", wake["events"])
        self.assertFalse(p.good_routine)
        self.assertEqual(p.good_routine_streak, 0)
        self.assertEqual(p.fatigue_layers, 1)
        self.assertEqual(p.fatigue_history, [8])
        self.assertEqual(wake["distraction"], 0)
        self.assertIsNone(p.deep_fatigue)
        self.assertEqual(p.energy, rm.energy_max(p))
        self.assertEqual(p.energy, 5)
        self.assertEqual(rm.sleep_factor(p), .95)

    def test_sufficient_late_sleep_preserves_shield_and_old_fatigue(self):
        p = self.player
        p.good_routine = True
        p.fatigue_layers = 1
        _, wake = self.sleep_night(1, rm.RESULT_FAILURE, [.1])
        self.assertEqual(wake["fatigue"], 0)
        self.assertTrue(p.good_routine)
        self.assertEqual(p.fatigue_layers, 1)
        self.assertEqual(p.current_time_slot, "morning_2")
        self.assertEqual(p.time_slot_index, 1)

    def test_coma_sufficient_sleep_adds_fatigue_but_no_distraction(self):
        p = self.player
        _, wake = self.sleep_night(3, rm.RESULT_SUCCESS)
        self.assertEqual(wake["fatigue"], 1)
        self.assertEqual(wake["distraction"], 0)
        self.assertEqual(p.current_time_slot, "lunch")
        self.assertEqual(p.time_slot_index, 2)
        self.assertEqual(p.day, 2)
        self.assertFalse(p.night_snack_eaten)
        self.assertIsNone(p.sleep_pending)
        with self.assertRaises(ValueError):
            rm.finish_wake(p, rm.RESULT_BIG_SUCCESS)

    def test_seven_recovery_nights_then_seven_fresh_routine_nights(self):
        p = self.player
        rm.start_deep_fatigue(p)
        for night in range(1, 8):
            self.sleep_night()
            self.assertEqual((p.fatigue_layers, rm.emotion_layers(p, rm.EMOTION_DISTRACTION)), (0, 0))
            self.assertFalse(p.good_routine)
            self.assertEqual(p.good_routine_streak, 0)
            self.assertEqual(p.deep_fatigue is None, night == 7)
        self.assertEqual(p.formal_attributes["con"], 6)
        self.assertEqual(p.current_attribute("con"), 6)
        self.assertEqual(p.degradation_penalty_pending["con"], 0)
        for night in range(1, 8):
            self.sleep_night()
            self.assertEqual(p.good_routine_streak, night)
            self.assertEqual(p.good_routine, night == 7)
        self.assertEqual(p.day, 15)

    def test_sufficient_sleep_still_receives_fatigue_and_worsens_disease(self):
        p = self.player
        rm.start_deep_fatigue(p)
        _, wake = self.sleep_night(3, rm.RESULT_SUCCESS)
        self.assertEqual(wake["fatigue"], 1)
        self.assertEqual(wake["distraction"], 0)
        self.assertEqual(p.deep_fatigue["layers"], 2)
        self.assertEqual(p.current_attribute("con"), 4)
        for _ in range(5):
            self.sleep_night()
        self.assertIsNotNone(p.deep_fatigue)
        self.assertEqual(p.day, 7)
        sleep, _ = self.sleep_night()
        self.assertIn("deep_fatigue_permanent_loss:2", sleep["events"])
        self.assertIsNone(p.deep_fatigue)
        self.assertEqual((p.formal_attributes["con"], p.current_attribute("con")), (4, 4))
        self.assertEqual(p.degradation_penalty_pending["con"], 2)
        self.assertFalse(p.good_routine)

    def test_wake_big_failure_degrades_once_but_costs_no_energy(self):
        p = self.player
        rm.start_turn(p, "sleep_decision")
        rm.continue_night(p)
        rm.advance_time_slot(p)
        rm.begin_sleep(p, random.Random(7))
        p.energy = 0
        result = rm.CheckResult(attribute="pow", rank=rm.RESULT_BIG_FAILURE)
        rm.finish_wake(p, result)
        self.assertEqual(p.energy, 0)
        self.assertEqual(p.degradation_progress["pow"], 1)
        with self.assertRaises(ValueError):
            rm.finish_wake(p, result)
        self.assertEqual(p.degradation_progress["pow"], 1)

    def test_weekly_growth_precedes_disease_expiry_at_zero_floor(self):
        p = self.player
        p.day = p.weekday = 7
        p.formal_attributes["con"] = 1
        p.attribute_values["con"] = 1
        rm.start_deep_fatigue(p)
        p.deep_fatigue.update(layers=2, last_night=7, relapsed=True)
        rm.start_turn(p, "sleep_decision")
        rng = random.Random(7)
        rng.random = lambda: 0.0
        events = rm.begin_sleep(p, rng)["events"]
        self.assertLess(events.index("value_to_formal:con"), events.index("deep_fatigue_permanent_loss:2"))
        self.assertEqual(p.formal_attributes["con"], 0)
        self.assertEqual(p.degradation_penalty_pending["con"], 2)

    def test_on_time_sleep_clears_effects_not_history_and_third_receipt_triggers(self):
        p = self.player
        self.sleep_night(1, draws=[.1])
        history = list(p.fatigue_history)
        self.sleep_night()
        self.assertEqual((p.fatigue_layers, rm.emotion_layers(p, rm.EMOTION_DISTRACTION)), (0, 0))
        self.assertEqual(p.fatigue_history, history)
        self.sleep_night(1)
        self.sleep_night()
        self.sleep_night(1)
        self.assertEqual(p.fatigue_layers, 1)
        self.assertEqual(p.deep_fatigue["layers"], 1)
        self.assertEqual(p.fatigue_history, [])

    def test_sleepy_independent_half_probability_and_three_round_floor(self):
        for count in (1, 2, 3):
            for draws in itertools.product((.499, .5), repeat=count):
                self.player = rm.create_initial_character(rng=random.Random(7))
                _, wake = self.sleep_night(count, rm.RESULT_BIG_SUCCESS, draws)
                expected = sum(value < .5 for value in draws)
                if count == 3:
                    expected = max(1, expected)
                self.assertEqual(wake["distraction"], expected)
                self.assertEqual(wake["fatigue"], 1)
        self.player = rm.create_initial_character(rng=random.Random(7))
        _, wake = self.sleep_night(3, rm.RESULT_HARD_SUCCESS, [.9] * 3)
        self.assertEqual((wake["skip_morning"], wake["distraction"]), (1, 1))

    def test_healthy_routine_exact_boundaries_and_mutual_exclusion(self):
        for roll, blocked, retained in ((0, True, True), (.249, True, True),
                (.25, True, False), (.749, True, False), (.75, False, False), (.999, False, False)):
            self.player = rm.create_initial_character(rng=random.Random(7))
            p = self.player
            p.good_routine = True
            p.fatigue_history = [8, 9]
            _, wake = self.sleep_night(1, draws=[.1, roll])
            self.assertEqual(p.good_routine, retained)
            self.assertEqual((wake["fatigue"], wake["distraction"]), (0, 0) if blocked else (1, 1))
            self.assertEqual(p.deep_fatigue is None, blocked)
            self.assertEqual(p.fatigue_history, [8, 9] if blocked else [])
            self.assertFalse(p.deep_fatigue and p.good_routine)

    def test_healthy_shield_does_not_cancel_coma_or_skipped_rounds(self):
        p = self.player
        p.good_routine = True
        _, wake = self.sleep_night(3, rm.RESULT_FAILURE, [.1])
        self.assertEqual((wake["fatigue"], wake["distraction"]), (0, 0))
        self.assertEqual(p.current_time_slot, "lunch")
        self.assertFalse(p.meal_choices["breakfast"])
        spec = rm.CheckSpec("pow", 15, action_type=rm.ACTION_SCHEDULE, is_late_night=True)
        profile = rm.mood_check_profile(rm.mood_state(p))
        self.assertEqual(rm.total_energy_cost(p.dice_for("pow")[:1], spec, profile), 2)

    def test_coffee_rest_and_sleep_use_emotion_rules(self):
        p = self.player
        rm.add_emotion(p, rm.EMOTION_DISTRACTION, 5)
        p.fatigue_layers = 1
        p.fatigue_history = [8]
        rm.consume_coffee(p, random.Random(0))
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 4)
        self.assertTrue(rm.resolve_test_day_rest(p, random.Random(0))["available"])
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 3)
        self.assertEqual(rm.reduce_drowsiness(p, 2), 2)
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 1)
        self.assertEqual((p.fatigue_layers, p.fatigue_history), (1, [8]))
        self.sleep_night()
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 0)
        rm.consume_coffee(p, random.Random(0))
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_EXCITEMENT), 1)

    def test_distraction_is_two_die_final_multiplier_not_pow_penalty(self):
        p = self.player
        rm.add_emotion(p, rm.EMOTION_DISTRACTION, 2)
        for mood in (0, -100, 100):
            p.mood = mood
            for attr in ("pow", "str"):
                rm.add_emotion(p, rm.EMOTION_DISTRACTION, 1)
                p.energy = 100
                ids = [die.id for die in p.dice_for(attr)[:2]]
                result = rm.perform_check(p, rm.CheckSpec(attr, 5, ids, extra_modifier=4, check_context="story"), random.Random(0))
                self.assertEqual(result.extra_modifier, 4)
                if len(ids) >= 2:
                    self.assertEqual(result.final_multiplier, .75)
        self.assertEqual(p.current_attribute("pow"), 6)

    def test_final_disease_night_counts_receipt_before_expiry(self):
        p = self.player
        rm.start_deep_fatigue(p)
        for _ in range(6):
            self.sleep_night()
        self.assertEqual(p.day, 7)
        sleep, wake = self.sleep_night(1, rm.RESULT_FAILURE)
        self.assertNotIn("deep_fatigue_recovered", sleep["events"])
        self.assertIn("deep_fatigue_added:2", wake["events"])
        self.assertIn("deep_fatigue_permanent_loss:2", wake["events"])
        self.assertIsNone(p.deep_fatigue)
        self.assertEqual(p.formal_attributes["con"], 4)
        self.assertEqual(p.fatigue_history, [])
        self.sleep_night(1)
        self.assertIsNone(p.deep_fatigue)
        self.assertEqual(len(p.fatigue_history), 1)

    def test_legacy_save_migrates_once_without_inventing_fatigue_history(self):
        p = self.player
        del p.fatigue_layers, p.fatigue_history, p.drowsiness
        p.sleep_fatigue = [1, 8, 8]
        rm.ensure_second_stage_state(p)
        self.assertEqual((p.fatigue_layers, p.fatigue_history, p.drowsiness), (0, [], 0))
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 2)
        rm.ensure_second_stage_state(p)
        self.assertEqual(p.drowsiness, 0)
        self.assertEqual(rm.emotion_layers(p, rm.EMOTION_DISTRACTION), 2)
        self.assertEqual(p.sleep_fatigue, [])

    def test_hidden_counter_not_exposed_in_status_rows(self):
        p = self.player
        p.fatigue_history = [8, 9]
        self.assertEqual(rm.sleep_status_summary(p), [])
        p.good_routine = True
        self.assertEqual([r["label"] for r in rm.sleep_status_summary(p)],
                         ["健康作息", "精力充沛", "优质睡眠"])


if __name__ == "__main__":
    unittest.main()
