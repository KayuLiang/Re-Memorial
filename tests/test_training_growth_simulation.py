import copy
from contextlib import closing
import random
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
from tools import simulate_training_growth as sim

rm = sim.rm


class FixedRandom(random.Random):
    def __init__(self, value):
        super().__init__(1)
        self.value = value

    def random(self):
        return self.value


class TrainingGrowthTests(unittest.TestCase):
    def test_wake_fit_keeps_anchor_and_75_percent_floor(self):
        rows=[]
        for value in (6,7,10,15,20):
            survival=np.clip(1-(np.arange(sim.MAX_TOTAL+1)-15-1.5*(value-6))/20,0,1)
            rows.append(dict(formal_attribute=value,n=40 if value==7 else 200,
                             survival=survival.tolist(),se=[0]*(sim.MAX_TOTAL+1)))
        result=dict(trials=200,rows=rows)
        fit=sim.fit_wake(result)
        self.assertIsNotNone(fit)
        self.assertEqual(fit['target_probability'],.75)
        self.assertEqual(fit['rows'][0]['target'],15)
        self.assertFalse(fit['rows'][0]['used_for_fit'])
        self.assertFalse(fit['rows'][1]['used_for_fit'])
        self.assertEqual(len(fit['rows']),5)
        for row in fit['rows']:
            if row['used_for_fit']:
                self.assertGreaterEqual(row['success'],.75)
            self.assertEqual(row['target'],int(np.floor(15+fit['a']*(row['pow']-6)**2+fit['b']*(row['pow']-6)+.5)))
        self.assertGreaterEqual(fit['b'],0)
        self.assertGreaterEqual(fit['b']+28*fit['a'],-1e-12)
        for row in rows:
            row['survival']=[.74]*(sim.MAX_TOTAL+1)
        self.assertIsNone(sim.fit_wake(result))

    def test_anchor_and_actual_intermediate_modifier(self):
        state = sim.initial_state('pow',6,1)
        pmf, modifier, available = sim.total_pmf(state,'pow')
        self.assertTrue(available)
        self.assertEqual(modifier,3)
        self.assertAlmostEqual(pmf[15:].sum(),.725)
        rm.add_attribute_bonus(state,'pow',2)
        rm.add_attribute_value(state,'pow',2)
        changed, modifier, _ = sim.total_pmf(state,'pow')
        self.assertEqual(modifier,5)
        self.assertAlmostEqual(changed[17:].sum(),.725)

    def test_all_three_counters_and_weekly_reward_delay(self):
        state = sim.initial_state('pow',6,1)
        rm.add_attribute_bonus(state,'pow',4)
        self.assertEqual(state.dice_growth_progress['pow'],0)
        self.assertEqual(state.growth_reward_pending['pow'],1)
        rm.process_small_rest(state,FixedRandom(.99))
        self.assertEqual(state.attribute_values['pow'],4)
        self.assertEqual(state.growth_reward_pending['pow'],3)
        rm.process_large_rest(state,FixedRandom(0.))
        self.assertEqual(state.formal_attributes['pow'],10)
        self.assertEqual(state.growth_reward_pending['pow'],7)
        self.assertEqual(state.dice_growth_progress['pow'],0)
        rm.process_small_rest(state,FixedRandom(.5))
        self.assertEqual(state.growth_reward_pending['pow'],7)

    def test_sealed_and_forced_dice_change_exact_pmf(self):
        state = sim.initial_state('pow',6,1)
        for die in state.dice_for('pow'):
            die.enchantment = rm.ENCHANT_SEAL
        pmf, _, available = sim.total_pmf(state,'pow')
        self.assertFalse(available)
        self.assertEqual(pmf.sum(),0.)
        self.assertIsNone(sim.target_for(np.cumsum(pmf[::-1])[::-1],.2))
        dice = [rm.RMDice(str(i),'str',[v]*6,rm.ENCHANT_SHACKLE if i<2 else None)
                for i,v in enumerate((1,1,6,6,6))]
        self.assertEqual(sim.pool_mean(dice),8.)
        for d in dice:
            d.enchantment=rm.ENCHANT_SHACKLE
        self.assertAlmostEqual(sim.pool_mean(dice),12.)

    def test_pow_proxy_uses_strength_opportunity_table_without_mutation(self):
        for rank in (rm.RESULT_FAILURE,rm.RESULT_SUCCESS,rm.RESULT_HARD_SUCCESS):
            strength=sim.initial_state('str',6,1)
            power=sim.initial_state('pow',6,1)
            result=rm.CheckResult(available=True,rank=rank)
            for _ in range(8):
                rm.apply_strength_training_str_bonus(strength,result,random.Random(24))
                sim.proxy_strength_bonus(power,'pow',result,random.Random(24))
            if rank == rm.RESULT_FAILURE:
                self.assertEqual(len(power.attribute_bonuses['pow']), 0)
            else:
                self.assertGreater(len(power.attribute_bonuses['pow']), 0)
            self.assertEqual(len(power.attribute_bonuses['str']), 0)
            self.assertEqual(power.dice_growth_progress['pow'], 0)

    def test_card_scoring_matches_core_for_chosen_faces_and_negative_clear(self):
        state=sim.initial_state('pow',6,1)
        state.dice_for('pow')[0].enchantment=rm.ENCHANT_SLUGGISH
        state.dice_for('pow')[1].enchantment=rm.ENCHANT_SEAL
        cards=[{'type':'clear_negative_enchant'},
               {'type':'increase_chosen_face','increase_amount':2},
               {'type':'replace_chosen_face_chosen_die','new_face_values':{'20':8}}]
        before=copy.deepcopy(state.__dict__)
        for card in cards:
            for selected in sim.card_options(state,'pow',card):
                clone=copy.deepcopy(state)
                self.assertTrue(rm.apply_growth_reward(clone,'pow',selected,random.Random(1))['applied'])
                self.assertAlmostEqual(sim.card_score(state,'pow',selected),sim.pool_mean(clone.dice_for('pow')))
        self.assertEqual(state.energy,before['energy'])
        self.assertEqual([d.faces for d in state.dice_pool],[d.faces for d in before['dice_pool']])

    def test_random_penalty_scoring_averages_targets_and_faces(self):
        state=sim.initial_state('str',3,1)
        state.dice_pool.append(rm.RMDice('extra','str',[1]*6))
        for kind in ('seal_die','add_sluggish_enchant','decrease_random_face'):
            card={'type':kind}
            outcomes=[]
            for die in state.dice_for('str'):
                indices=range(len(die.faces)) if kind=='decrease_random_face' else (None,)
                means=[]
                for i in indices:
                    clone=copy.deepcopy(state)
                    target=clone.find_die(die.id)
                    if i is not None:
                        target.faces[i]=max(1,target.faces[i]-1)
                    else:
                        target.enchantment=rm.ENCHANT_SEAL if kind=='seal_die' else rm.ENCHANT_SLUGGISH
                    means.append(sim.pool_mean(clone.dice_for('str')))
                outcomes.append(sum(means)/len(means))
            self.assertAlmostEqual(sim.card_score(state,'str',card),sum(outcomes)/len(outcomes))

    def test_random_player_choice_selects_die_before_face(self):
        state=sim.initial_state('str',3,1)
        state.dice_pool.append(rm.RMDice('large','str',[1]*12))
        card={'type':'replace_chosen_face_chosen_die','new_face_values':{'6':3,'12':6}}
        rng=random.Random(83)
        large=sum(sim.choose_card(state,'str',[card],'random',rng)['die_id']=='large' for _ in range(4000))
        self.assertLess(abs(large/4000-.5),.03)

    def test_training_progress_not_direct_dice_reward_and_sleep_conversion(self):
        state=sim.initial_state('dex',1,1)
        result=rm.CheckResult(available=True,rank=rm.RESULT_BIG_SUCCESS)
        rm.apply_test_training_result(state,'dex',result,random.Random(1))
        self.assertEqual(state.test_growth_progress['dex'],6)
        self.assertEqual(state.dice_growth_progress['dex'],6)
        self.assertEqual(state.growth_reward_pending['dex'],1)
        rm.start_turn(state,'sleep_decision')
        sleep=rm.begin_sleep(state,FixedRandom(.5))
        self.assertEqual(sleep['events'].count('test_training_bonus:dex'),1)
        self.assertEqual(state.test_growth_progress['dex'],0)
        self.assertEqual(len(state.attribute_bonuses['dex']),1)
        self.assertEqual(state.attribute_bonus_gain_counters['dex'],1)

    def test_skipped_formal_values_are_not_filled_and_day_limit_is_reported(self):
        def jump(state, attr, policy, rng, counts):
            state.formal_attributes[attr] += 2
        with patch.object(sim,'training_day',jump):
            result=sim.simulate(('pow','pow',6),'random',3,10,10,12)
        self.assertEqual([r['n'] for r in result['rows']],[3,0,3,0,3])
        self.assertEqual(result['stopped'],{'reached_or_crossed_max':3})
        self.assertIsNone(sim.fit_wake(dict(result, trials=1000)))
        capped=sim.simulate(('pow','pow',6),'random',3,20,1,12)
        self.assertEqual(capped['stopped'],{'day_limit':3})

    def test_complete_training_preserves_dice_limits_and_normal_sleep(self):
        for attr,initial in (('pow',6),('con',6),('str',3),('dex',3)):
            for policy in sim.base.POLICIES:
                state=sim.initial_state(attr,initial,13)
                rng=random.Random(65)
                counts=sim.Counter()
                for day in range(50):
                    completed = sim.training_day(state,attr,policy,rng,counts)
                    self.assertLessEqual(abs(state.mood),200)
                    self.assertEqual(state.sleep_fatigue,[])
                    if completed:
                        self.assertEqual(state.training_load,0)
                    for attribute in rm.ATTRIBUTES:
                        dice=state.dice_for(attribute)
                        self.assertLessEqual(len(dice),rm.DICE_POOL_LIMITS[attribute])
                        allowed=(20,) if attribute=='pow' else (4,) if attribute=='con' else (6,8,10,12)
                        for die in dice:
                            self.assertIn(len(die.faces),allowed)
                            self.assertTrue(all(1<=v<=len(die.faces) for v in die.faces))
                    if not completed:
                        break
                self.assertLessEqual(counts['training_actions']+counts['rest_actions'],300)

    def test_complete_run_reproducibility_sampling_and_database(self):
        for policy in sim.base.POLICIES:
            result=sim.simulate(('pow','pow',6),policy,6,10,90,100)
            repeated=sim.simulate(('pow','pow',6),policy,6,10,90,100)
            self.assertEqual(result,repeated)
            self.assertEqual(sum(result['stopped'].values()),6)
            self.assertGreater(result['outcomes']['reward:pow'],6*(10-6))
            for row in result['rows']:
                self.assertEqual(row['n'],len(result['samples'][row['formal_attribute']]))
                if row['n']:
                    self.assertAlmostEqual(sum(row['pmf']),row['mean_available'])
                    for p,t in row['thresholds'].items():
                        if t is not None:
                            self.assertGreaterEqual(row['survival'][t]+1e-12,float(p))
                            if t<70:
                                self.assertLess(row['survival'][t+1],float(p)+1e-12)
            scratch=Path('E:/ChatGPT/Temp/rememorial-training-growth')
            scratch.mkdir(parents=True,exist_ok=True)
            with tempfile.TemporaryDirectory(dir=scratch) as folder:
                sim.write_results(Path(folder),[result],{'max_attribute':10})
                with closing(sqlite3.connect(str(Path(folder)/'dice-growth.sqlite'))) as db:
                    self.assertEqual(db.execute('SELECT count(*) FROM samples').fetchone()[0],sum(r['n'] for r in result['rows']))
                    self.assertAlmostEqual(db.execute('SELECT pass_probability FROM distribution WHERE formal_attribute=6 AND total_score=15').fetchone()[0],.725)


if __name__=='__main__':
    unittest.main()
