import copy
import random
import unittest
from game.systems import rm_core, rm_dice_view as view

class DiceViewTests(unittest.TestCase):
    def test_distribution_and_physical_faces(self):
        self.assertEqual(view.distribution([1,1,2,4]), [(1,2,.5),(2,1,.25),(3,0,0),(4,1,.25)])
        for n in (4,6,8,10,12,20):
            faces = [1]*n
            preview = view.preview_indices(faces)
            self.assertEqual(len(preview),n if n<=6 else 6)
            self.assertEqual(preview.count(None),0 if n<=6 else 1)
            reached = set()
            for offset in range(n): reached.update(view.visible_faces(faces,offset))
            self.assertEqual(reached,set(range(n)))
            self.assertEqual(sum(row[1] for row in view.distribution(faces)),n)
            self.assertAlmostEqual(sum(row[2] for row in view.distribution(faces)),1)

    def test_read_only_live_data_and_filtering(self):
        player = rm_core.create_initial_character({'str':3,'dex':3,'int':2}, rng=random.Random(7))
        player.dice_pool.append(rm_core.RMDice('new_d12','int',list(range(1,13)),rm_core.ENCHANT_LIGHT))
        before = copy.deepcopy(player.__dict__)
        rows = view.rows(player)
        self.assertEqual(next(d for d in rows if d['id']=='new_d12')['label'],'智力')
        self.assertEqual(view.rows(player,'int','mean','enchanted')[0]['id'],'new_d12')
        self.assertEqual(view.growth(player)[0][2],0)
        self.assertEqual(before['dice_growth_progress'],player.dice_growth_progress)
        self.assertEqual([d.faces for d in before['dice_pool']],[d.faces for d in player.dice_pool])
        player.find_die('new_d12').faces[0]=12
        self.assertEqual(next(d for d in view.rows(player) if d['id']=='new_d12')['faces'][0],12)

if __name__ == '__main__': unittest.main()
