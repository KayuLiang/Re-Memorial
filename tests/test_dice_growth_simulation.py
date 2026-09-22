import copy
from itertools import product
import random
import unittest

import numpy as np
from tools import simulate_dice_growth as sim

rm = sim.rm


class GrowthSimulationTests(unittest.TestCase):
    def test_initial_pow_distribution_reproduces_725_percent_and_attribute_modifier(self):
        state = sim.initial_state('pow', 6, 1)
        pmf = sim.pool_pmf(state.dice_for('pow'))
        shift = rm.attribute_modifier(state, 'pow', rm.mood_check_profile(rm.get_mood_state(state)))
        self.assertEqual(shift, 3)
        self.assertAlmostEqual(float(pmf[15-shift:].sum()), .725)
        self.assertAlmostEqual(float(pmf @ np.arange(61))+shift, 19.)

    def test_exact_pmf_and_mean_match_exhaustive_bonus_rolls(self):
        faces = [1, 1, 3, 4]
        for enchant, pick in ((rm.ENCHANT_SWIFT, max), (rm.ENCHANT_SLUGGISH, min)):
            values = [pick(a,b) for a,b in product(faces,repeat=2)]
            die = rm.RMDice('test','str',faces,enchant)
            expected = np.bincount(values, minlength=5)/16
            np.testing.assert_allclose(sim.die_pmf(die), expected, atol=1e-14)
            self.assertAlmostEqual(sim.roll_mean(faces,enchant), sum(values)/16)

    def test_greedy_does_not_mutate_state_and_values_random_effects_before_reveal(self):
        state = sim.initial_state('pow',6,2)
        before = copy.deepcopy(state.__dict__)
        cards = [{'type':'add_light_enchant'}, {'type':'add_swift_enchant'}]
        card, value = sim.greedy_choice(state,'pow',cards)
        means = [sim.roll_mean(d.faces) for d in state.dice_for('pow')]
        expected = sum(means) + sum(sim.roll_mean(d.faces,rm.ENCHANT_SWIFT)-m
                                   for d,m in zip(state.dice_for('pow'),means))/2
        self.assertEqual(card['type'],'add_swift_enchant')
        self.assertAlmostEqual(value,expected)
        self.assertEqual([d.faces for d in state.dice_pool], [d.faces for d in before['dice_pool']])
        self.assertTrue(all(d.enchantment is None for d in state.dice_pool))

    def test_chosen_face_and_die_choices_match_exhaustive_core_settlement(self):
        state = sim.initial_state('pow',6,3)
        card = {'type':'increase_chosen_face','increase_amount':2}
        chosen, expected = sim.greedy_choice(state,'pow',[card])
        outcomes = []
        for die in state.dice_for('pow'):
            for face_index in rm.growth_reward_face_indices(die, card):
                clone = copy.deepcopy(state)
                applied = dict(card,die_id=die.id,face_index=face_index)
                self.assertTrue(rm.apply_growth_reward(clone,'pow',applied)['applied'])
                outcomes.append((sim.top_three([sim.roll_mean(d.faces,d.enchantment) for d in clone.dice_for('pow')]), applied))
        best = max(outcomes,key=lambda item:item[0])
        self.assertAlmostEqual(expected,best[0])
        self.assertEqual(chosen,best[1])

    def test_random_face_card_score_matches_all_core_random_outcomes(self):
        state = sim.initial_state('con',6,4)
        state.dice_for('con')[0].enchantment = rm.ENCHANT_SWIFT
        card = {'type':'replace_random_face_random_die','new_face_value':3}
        _, expected = sim.greedy_choice(state,'con',[card])
        scores = []
        for die in state.dice_for('con'):
            for face_index in range(len(die.faces)):
                clone = copy.deepcopy(state)
                actual = dict(card,type='replace_chosen_face_chosen_die',die_id=die.id,face_index=face_index)
                rm.apply_growth_reward(clone,'con',actual)
                scores.append(sim.top_three([sim.roll_mean(d.faces,d.enchantment) for d in clone.dice_for('con')]))
        self.assertAlmostEqual(expected,sum(scores)/len(scores))

    def test_mixed_type_replacements_and_capped_faces_match_core_scoring(self):
        state = sim.initial_state('str', 3, 4)
        state.dice_for('str')[0].faces = [6, 6, 6, 6, 6, 5]
        state.dice_pool.append(rm.RMDice('str_d12', 'str', [12]*12))
        card = {'type':'increase_random_face_random_die','increase_amount':2}
        _, expected = sim.greedy_choice(state, 'str', [card])
        clone = copy.deepcopy(state)
        rm.apply_growth_reward(clone, 'str', card, random.Random(1))
        self.assertAlmostEqual(expected, sum(sim.roll_mean(d.faces) for d in clone.dice_for('str')))
        replace = {'type':'replace_random_face_random_die','new_face_values':{'6':2,'12':9}}
        _, expected = sim.greedy_choice(state, 'str', [replace])
        scores = []
        for die in state.dice_for('str'):
            by_face = []
            for i in range(len(die.faces)):
                clone = copy.deepcopy(state)
                selected = dict(replace, type='replace_chosen_face_chosen_die', die_id=die.id, face_index=i)
                rm.apply_growth_reward(clone, 'str', selected)
                by_face.append(sum(sim.roll_mean(d.faces) for d in clone.dice_for('str')))
            scores.append(sum(by_face)/len(by_face))
        self.assertAlmostEqual(expected, sum(scores)/len(scores))

    def test_formal_attribute_axis_uses_current_modifier_and_actual_growth_counter(self):
        for scenario in (('pow','pow',6), ('allocated_1','str',1)):
            r = sim.simulate(scenario, 'random', 4, 10, 100)
            np.testing.assert_array_equal(r['attributes'], np.arange(scenario[2], 11))
            np.testing.assert_array_equal(r['modifiers'], r['attributes']//2)
            self.assertEqual(r['pmf'].shape[0], 11-scenario[2])
            settled = sum(n for key,n in r['outcomes'].items() if key.startswith('selected:'))
            self.assertEqual(settled, 4*(10-scenario[2]))

    def test_reproducibility_probability_order_and_legal_long_growth(self):
        for policy in sim.POLICIES:
            result = sim.simulate(('pow','pow',6),policy,8,8,12)
            repeated = sim.simulate(('pow','pow',6),policy,8,8,12)
            np.testing.assert_array_equal(result['pmf'],repeated['pmf'])
            np.testing.assert_allclose(result['pmf'].sum(axis=1),1.)
            for survival in result['survival']:
                targets = [sim.threshold(survival,p) for p in sim.PROBABILITIES]
                self.assertEqual(targets,sorted(targets,reverse=True))
                for p,t in zip(sim.PROBABILITIES,targets):
                    self.assertGreaterEqual(survival[t]+1e-12,p)
                    if t<60:
                        self.assertLess(survival[t+1],p+1e-12)
            for attr in ('pow','con','str'):
                state = sim.initial_state(attr,6 if attr!='str' else 3,22)
                rng = random.Random(7)
                for _ in range(100):
                    cards = rm.draw_growth_reward_cards(state,attr,3,rng)
                    card = sim.random_choice(state,attr,cards,rng) if policy=='random' else sim.greedy_choice(state,attr,cards)[0]
                    self.assertTrue(rm.apply_growth_reward(state,attr,card,rng)['applied'])
                    dice = state.dice_for(attr)
                    self.assertLessEqual(len(dice),rm.DICE_POOL_LIMITS[attr])
                    allowed = (20,) if attr=='pow' else (4,) if attr=='con' else (6,8,10,12)
                    for die in dice:
                        self.assertIn(len(die.faces),allowed)
                        self.assertTrue(all(1<=v<=len(die.faces) for v in die.faces))


if __name__ == '__main__':
    unittest.main()
