import random
import unittest

from game.systems import rm_core as rm


class HealthTests(unittest.TestCase):
    def setUp(self):
        self.p = rm.create_initial_character(rng=random.Random(7))

    def test_initial_full_and_temporary_con_ignored(self):
        p = self.p
        self.assertEqual((p.health, rm.health_max(p)), (30, 30))
        p.attribute_values['con'] = 4
        rm.add_attribute_bonus(p, 'con', 3)
        rm.start_deep_fatigue(p)
        self.assertEqual((p.health, rm.health_max(p)), (30, 30))

    def test_formal_change_preserves_wounds_both_entry_points(self):
        for change in (rm.add_formal_attribute, rm.test_console_adjust_formal_attribute):
            p = rm.create_initial_character(rng=random.Random(7))
            rm.damage_health(p, 10)
            change(p, 'con', 1)
            self.assertEqual((p.health, rm.health_max(p)), (25, 35))
            change(p, 'con', -2)
            self.assertEqual((p.health, rm.health_max(p)), (15, 25))
            change(p, 'pow', 1)
            self.assertEqual(p.health, 15)

    def test_damage_heal_cap_fraction_and_validation(self):
        p = self.p
        self.assertEqual(rm.damage_health(p, .25), .25)
        self.assertEqual(p.health, 29.75)
        self.assertEqual(rm.heal_health(p, 5), .25)
        self.assertEqual(p.health, 30)
        for fn in (rm.damage_health, rm.heal_health):
            for amount in (-1, float('inf'), float('nan')):
                with self.assertRaises(ValueError):
                    fn(p, amount)

    def test_death_cannot_be_healed_or_grown_away(self):
        p = self.p
        rm.damage_health(p, 35)
        self.assertTrue(rm.is_dead(p))
        self.assertEqual(p.health, 0)
        self.assertEqual(rm.heal_health(p, 50), 0)
        rm.add_formal_attribute(p, 'con', 1)
        self.assertEqual((p.health, rm.health_max(p)), (0, 35))
        rm.end_day(p, random.Random(1), on_time=True)
        self.assertEqual(p.health, 0)

    def test_con_drop_kills_before_zero_con(self):
        rm.damage_health(self.p, 26)
        rm.add_formal_attribute(self.p, 'con', -1)
        self.assertEqual((self.p.health, rm.health_max(self.p)), (0, 25))
        self.assertTrue(rm.is_dead(self.p))

    def test_old_save_initialized_once_before_con_mutation(self):
        p = self.p
        del p.health
        rm.add_formal_attribute(p, 'con', -1)
        self.assertEqual((p.health, rm.health_max(p)), (25, 25))
        rm.damage_health(p, .75)
        rm.ensure_second_stage_state(p)
        self.assertEqual(p.health, 24.25)

    def test_night_only_fractional_recovery_once_and_cap(self):
        p = self.p
        rm.damage_health(p, 10)
        rm.resolve_test_day_rest(p, random.Random(1))
        rm.process_small_rest(p, random.Random(1))
        self.assertEqual(p.health, 20)
        rm.start_turn(p, 'sleep_decision')
        outcome = rm.begin_sleep(p, random.Random(1))
        self.assertEqual(p.health, 20.75)
        self.assertIn('health_restored:0.75', outcome['events'])
        self.assertFalse(rm.begin_sleep(p)['available'])
        self.assertEqual(p.health, 20.75)
        rm.heal_health(p, 9)
        rm.start_turn(p, 'sleep_decision')
        rm.begin_sleep(p, random.Random(1))
        self.assertEqual(p.health, 30)

    def test_late_sleep_heals_once_not_again_at_wake(self):
        p = self.p
        rm.damage_health(p, 10)
        rm.start_turn(p, 'sleep_decision')
        rm.continue_night(p)
        rm.advance_time_slot(p)
        rm.begin_sleep(p, random.Random(1))
        self.assertEqual(p.health, 20.75)
        rm.finish_wake(p, rm.RESULT_FAILURE, random.Random(1))
        self.assertEqual(p.health, 20.75)

    def test_disease_deadline_death_before_next_day(self):
        p = self.p
        rm.start_deep_fatigue(p)
        p.deep_fatigue['relapsed'] = True
        p.day = p.deep_fatigue['last_night']
        p.weekday = 1
        rm.damage_health(p, 26)
        rm.start_turn(p, 'sleep_decision')
        before_day = p.day
        outcome = rm.begin_sleep(p, random.Random(1))
        self.assertTrue(rm.is_dead(p))
        self.assertEqual(p.day, before_day)
        self.assertIn('death', outcome['events'])

    def test_late_deadline_kills_before_routing_to_morning(self):
        p = self.p
        rm.start_deep_fatigue(p)
        p.day = p.deep_fatigue['last_night']
        p.weekday = 1
        rm.damage_health(p, 22)
        rm.start_turn(p, 'sleep_decision')
        rm.continue_night(p)
        rm.advance_time_slot(p)
        rm.begin_sleep(p, random.Random(1))
        outcome = rm.finish_wake(p, rm.RESULT_FAILURE, random.Random(1))
        self.assertTrue(rm.is_dead(p))
        self.assertIn('death', outcome['events'])
        self.assertEqual(p.current_time_slot, 'wake_check')
        self.assertIsNone(p.sleep_pending)

    def test_tooltip_keeps_fraction(self):
        rm.damage_health(self.p, 9.25)
        self.assertIn('20.75 / 30', rm.health_tooltip(self.p))


if __name__ == '__main__':
    unittest.main()
