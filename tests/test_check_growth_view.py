import copy
import random
import unittest
from itertools import product

from game.systems import rm_core as core, rm_dice_view as view


def player_snapshot(player):
    state = copy.deepcopy(player.__dict__)
    state['dice_pool'] = [vars(die) for die in state['dice_pool']]
    return state


class CheckGrowthViewTests(unittest.TestCase):
    def test_exact_probability_matches_exhaustive_real_settlement(self):
        class FaceRng:
            def __init__(self, values=()):
                self.values = iter(values)
                self.draws = []

            def choice(self, faces):
                self.draws.append(tuple(faces))
                return next(self.values, faces[0])

        for mood, enchantment, confidence, disease in (
                (0, None, False, core.DISEASE_NONE),
                (-70, core.ENCHANT_SWIFT, False, core.DISEASE_NONE),
                (0, core.ENCHANT_SLUGGISH, True, core.DISEASE_NONE),
                (80, core.ENCHANT_SLUGGISH, False, core.DISEASE_MANIA)):
            player = core.create_initial_character(rng=random.Random(1))
            player.energy = 100
            player.mood = mood
            player.disease_state = disease
            player.long_emotions['confidence'] = confidence
            player.dice_pool = [core.RMDice('a','str',[1,1,3,4],enchantment),
                                core.RMDice('b','str',[1,2,2,4],core.ENCHANT_SWIFT)]
            core.add_emotion(player,core.EMOTION_EXCITEMENT)
            spec = core.CheckSpec('str',9,['a','b'],extra_modifier=1,
                                  bonus_die_ids=['b','b','b'])
            rng = random.Random(13)
            before = player_snapshot(player)
            rng_before = rng.getstate()
            preview = view.check_selection(player,spec,rng)
            probe = FaceRng()
            core.perform_check(copy.deepcopy(player),spec,probe)
            results = [core.perform_check(copy.deepcopy(player),spec,FaceRng(values))
                       for values in product(*probe.draws)]
            self.assertAlmostEqual(preview['success_probability'],sum(r.success for r in results)/len(results))
            self.assertEqual(preview['total_range'],(min(r.total for r in results),max(r.total for r in results)))
            self.assertEqual(player_snapshot(player),before)
            self.assertEqual(rng.getstate(),rng_before)

    def test_repeated_faces_rerolls_and_comparison(self):
        faces = (3,3,3,5,5,6)
        for mode, expected in (('normal',.5),('bonus',.75),('penalty',.25)):
            distribution = view.check_sum_distribution(((faces,mode),))
            self.assertEqual(sum(n for value,n in distribution if value>=5)/sum(n for _,n in distribution),expected)
        player = core.create_initial_character(rng=random.Random(1))
        player.energy = 6
        player.dice_pool = [core.RMDice('a','str',list(faces)),core.RMDice('b','str',[1,2,3,4])]
        spec = core.CheckSpec('str',8,['a'],action_type=core.ACTION_INSTANT)
        rng = random.Random(1)
        before = (player_snapshot(player),rng.getstate(),list(spec.dice_ids))
        current = view.check_selection(player,spec,rng)
        added = view.check_selection_change(player,spec,rng,'b')
        self.assertEqual((current['cost'],added['cost'],added['remaining']),(0,1,5))
        self.assertGreater(added['success_probability'],current['success_probability'])
        removed = view.check_selection_change(player,spec,rng,'a')
        self.assertIsNone(removed['success_probability'])
        self.assertEqual((player_snapshot(player),rng.getstate(),spec.dice_ids),before)
        player.energy = 0
        blocked = view.check_selection_change(player,spec,rng,'b')
        self.assertIsNone(blocked['success_probability'])
        self.assertIn('精力不足',blocked['reason'])
        self.assertEqual(view.probability_text(.99999),'>99.9%')
        self.assertEqual(view.probability_text(.00001),'<0.1%')

    def test_formula_matches_settlement_with_mood_and_total_factors(self):
        for mood in (0, -70):
            for count in (1, 3):
                player = core.create_initial_character(rng=random.Random(1))
                player.energy = 100
                player.mood = mood
                player.current_weather = core.WEATHER_FOG
                player.intoxication = 1
                player.palpitations = True
                core.add_emotion(player, core.EMOTION_CALM)
                core.add_emotion(player, core.EMOTION_EXCITEMENT)
                player.dice_pool = [core.RMDice(str(i),'str',[1,2,3,4]) for i in range(count)]
                spec = core.CheckSpec('str',6,[d.id for d in player.dice_pool],outdoors=True,extra_modifier=2)
                rng = random.Random(3)
                before_rng = rng.getstate()
                before_emotions = dict(player.emotions)
                preview = view.check_selection(player,spec,rng)
                self.assertEqual(rng.getstate(),before_rng)
                self.assertEqual(dict(player.emotions),before_emotions)
                self.assertEqual(player.energy,100)
                result = core.perform_check(player,spec,rng)
                self.assertEqual(preview['target'],result.requirement)
                self.assertEqual(preview['final_multiplier'],result.final_multiplier)
                self.assertEqual((result.dice_total*preview['dice_multiplier']+preview['attribute_modifier']+preview['extra_modifier'])*preview['final_multiplier'],result.total)

    def test_preview_preserves_rng_and_matches_real_cost_and_pool(self):
        for mood in (0, -70):
            player = core.create_initial_character(rng=random.Random(1))
            player.mood = mood
            player.energy = 100
            player.current_time_slot = 'morning_1'
            player.time_habits['morning:training'] = True
            player.dice_pool = [core.RMDice(str(i), 'str', [1, 2, 3, 4], core.ENCHANT_SHACKLE) for i in range(5)]
            spec = core.CheckSpec('str', 6, ['0'], schedule_category='training')
            rng = random.Random(4)
            state = rng.getstate()
            before = [(d.id, list(d.faces), d.enchantment) for d in player.dice_pool]
            preview = view.check_selection(player, spec, rng)
            self.assertEqual(rng.getstate(), state)
            self.assertEqual(player.energy, 100)
            self.assertEqual(before, [(d.id, list(d.faces), d.enchantment) for d in player.dice_pool])
            result = core.perform_check(player, spec, rng)
            self.assertEqual([d.id for d in preview['dice']], result.dice_ids)
            self.assertEqual(preview['cost'], result.energy_cost)

    def test_deterministic_comparisons_match_rewards_without_applying(self):
        player = core.create_initial_character(rng=random.Random(1))
        die = player.find_die('str_1')
        die.faces = [6, 6, 5, 6, 6, 6]
        card = dict(type='increase_chosen_face', increase_amount=2, die_id=die.id, face_index=2)
        before = copy.deepcopy(die.faces)
        self.assertIn('5 → 6', view.growth_comparison(die, card, 2))
        self.assertEqual(die.faces, before)
        core.apply_growth_reward(player, 'str', card)
        self.assertEqual(die.faces, [6]*6)
        self.assertIn('D6 → D8', view.growth_comparison(die, dict(type='upgrade_chosen_die_type')))
        self.assertIn('随机', view.growth_comparison(die, dict(type='increase_random_face_chosen_die')))


if __name__ == '__main__':
    unittest.main()
