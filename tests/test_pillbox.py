import pickle
import random
import unittest
from game.systems import rm_core as core, rm_pillbox as box


class PillboxTests(unittest.TestCase):
    def player(self, slots=box.INITIAL_SLOTS):
        state = core.create_initial_character(rng=random.Random(2))
        core.ensure_second_stage_state(state)
        box.set_prescription(state, slots, {})
        for drug in core.PSYCHIATRIC_MEDICINES:
            core.add_medicine_stock(state, drug, 12)
        return state

    def test_all_eight_rotations_shortest_path_and_empty_slots(self):
        for step in range(8):
            for slot in range(8):
                turn = box.shortest_turn(step, slot)
                self.assertLessEqual(abs(turn), 4)
                self.assertEqual(box.selected_slot((step+turn) % 8), slot)
        for count in (0, 1, 3, 8):
            slots = [core.PSYCHIATRIC_MEDICINES[i % 6] if i < count else None for i in range(8)]
            state = self.player(slots)
            for step in range(8):
                state.current_rotation_step = step
                self.assertEqual(box.selection(state, "manual")["drug"], slots[(-step)%8])

    def test_venlafaxine_two_tablets_are_one_dose(self):
        state = self.player()
        state.medicine_counts["venlafaxine"] = 3
        result = box.take_selected(state, "morning")
        self.assertTrue(result["available"])
        self.assertEqual(state.medicine_counts["venlafaxine"], 1)
        self.assertEqual(state.medicine_taken_today["venlafaxine"], 1)
        self.assertEqual(box.take_selected(state, "morning", True)["reason"], "out_of_stock")
        self.assertEqual(state.medicine_counts["venlafaxine"], 1)

    def test_last_tablet_and_multi_medicine_session(self):
        state = self.player()
        state.current_rotation_step = 7
        state.medicine_counts["trazodone"] = 1
        self.assertTrue(box.take_selected(state, "evening")["available"])
        self.assertEqual(box.selection(state, "evening")["count"], 0)
        self.assertFalse(box.take_selected(state, "evening", True)["available"])
        state.current_rotation_step = 6
        core.add_emotion(state, core.EMOTION_ANXIETY)
        self.assertTrue(box.take_selected(state, "manual")["available"])
        self.assertEqual(core.emotion_layers(state, core.EMOTION_ANXIETY), 0)
        session = box.finish_session(state, "evening", {})
        self.assertEqual(session["taken"], dict(trazodone=1, alprazolam=1))

    def test_repeat_confirmation_no_mutation_and_diminishing_effect(self):
        state = self.player()
        first = box.take_selected(state, "morning")
        before = pickle.dumps(state)
        self.assertEqual(box.take_selected(state, "morning")["reason"], "repeat_confirmation_required")
        self.assertEqual(pickle.dumps(state), before)
        second = box.take_selected(state, "morning", True)
        self.assertLess(second["mood_delta"], first["mood_delta"])
        self.assertIn("repeat_medicine_event_hook:venlafaxine", second["events"])
        self.assertEqual(state.medicine_taken_today["venlafaxine"], 2)

    def test_bipolar_repeat_never_rerolls_or_rearms_consumed_effect(self):
        class Always:
            calls = 0
            def random(self):
                self.calls += 1
                return 0
        for drug in ("lithium", "aripiprazole", "lamotrigine"):
            state = self.player([drug] + [None]*7)
            rng = Always()
            box.take_selected(state, "manual", rng=rng)
            expected = rng.calls
            state.pending_bipolar_medications.clear()
            result = box.take_selected(state, "manual", True, rng)
            self.assertTrue(result["repeat"])
            self.assertEqual(rng.calls, expected + 1)  # Repeated dose rolls poisoning risk.
            self.assertEqual(state.pending_bipolar_medications, {})

    def test_recommendations_are_advisory_and_finish_never_penalizes(self):
        state = self.player()
        box.set_prescription(state, box.INITIAL_SLOTS, box.INITIAL_RECOMMENDATIONS)
        self.assertTrue(box.selection(state, "morning")["recommended"])
        self.assertFalse(box.selection(state, "manual")["recommended"])
        state.drug_dependence = True
        state.mood = -100
        core.start_turn(state, "breakfast")
        self.assertEqual(box.due_context(state), "morning")
        box.finish_session(state, "morning", {})
        self.assertIsNone(box.due_context(state))
        self.assertEqual(state.mood, -100)
        core.start_turn(state, "sleep_decision")
        self.assertEqual(box.due_context(state), "evening")

    def test_dependency_seven_distinct_days_and_seven_withdrawal_days(self):
        state = self.player()
        for day in range(1, 8):
            state.day = day
            state.medicine_taken_today.clear()
            core.take_medicine(state, "alprazolam")
            core.settle_medication_day(state)
            self.assertEqual(state.drug_dependence, day >= 7)
        self.assertTrue(state.drug_dependence)
        for day in range(8, 15):
            state.day = day
            state.medicine_taken_today.clear()
            state.mood = -100
            events = core.settle_medication_day(state)
            self.assertIn("withdrawal:alprazolam", events)
            self.assertLess(state.mood, -100)
            self.assertEqual(core.settle_medication_day(state), [])
            self.assertEqual(state.drug_dependence, day < 14)
        self.assertEqual(state.drug_free_days["alprazolam"], 7)

    def test_medication_any_time_avoids_daily_penalty(self):
        state = self.player()
        state.drug_dependences["alprazolam"] = True
        box.finish_session(state, "morning", {})
        box.finish_session(state, "evening", {})
        core.take_medicine(state, "alprazolam")
        state.mood = 100
        core.settle_medication_day(state)
        self.assertEqual(state.mood, 100)

    def test_legacy_stock_migration_and_persistence(self):
        state = core.create_initial_character()
        state.medicine_counts.update(venlafaxine=0, lithium=17)
        box.ensure_state(state)
        self.assertEqual(state.pillbox_slots[:2], ["venlafaxine", "lithium"])
        state.current_rotation_step = 6
        state.pending_bipolar_medications["lithium"] = True
        loaded = pickle.loads(pickle.dumps(state))
        box.ensure_state(loaded)
        self.assertEqual(loaded.pillbox_slots, state.pillbox_slots)
        self.assertEqual(loaded.current_rotation_step, 6)
        self.assertTrue(loaded.pending_bipolar_medications["lithium"])


if __name__ == "__main__":
    unittest.main()
