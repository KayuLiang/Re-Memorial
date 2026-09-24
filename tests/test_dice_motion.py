import copy
import json
import math
from pathlib import Path
import unittest

from game.systems import rm_dice_motion as motion

MODELS = json.loads((Path(__file__).resolve().parents[1] / 'game/gui/dice_obsidian/realtime.json').read_text())


class DiceMotionTests(unittest.TestCase):
    def test_camera_starts_at_selection_pose_and_finishes_overhead(self):
        selected = motion.camera(0,selection=True)
        initial = motion.camera(0)
        for point in ((0,0,0),(2.5,-1,.7),(-2.5,1,.8)):
            a,b = motion.project(point,selected),motion.project(point,initial)
            self.assertAlmostEqual(a[0],b[0])
            self.assertAlmostEqual(a[1]+310,b[1]+145)
        overhead = motion.camera(1)
        self.assertAlmostEqual(overhead['view'][2],1)
        self.assertEqual(motion.project((1,1,0),overhead),motion.project((1,1,1),overhead))
        self.assertEqual(sorted(motion.camera(t/20)['view'][2] for t in range(21)),[motion.camera(t/20)['view'][2] for t in range(21)])

    def test_raised_rails_match_table_collision_envelope(self):
        tray = json.loads((Path(__file__).resolve().parents[1]/'game/gui/dice_obsidian/tabletop.json').read_text())
        self.assertEqual(set(tray['parts']),{'deck','north','south','west','east'})
        self.assertEqual(tuple(tray['play_limits']),motion.TABLE_LIMITS)
        for name,axis,sign in [('north',1,1),('south',1,-1),('west',0,-1),('east',0,1)]:
            vertices = tray['parts'][name]['vertices']
            self.assertAlmostEqual(min(sign*v[axis] for v in vertices),motion.TABLE_LIMITS[axis]+tray['die_radius'],places=5)
            self.assertAlmostEqual(max(v[2] for v in vertices),tray['rail_height'],places=5)
            self.assertGreater(tray['rail_height'],.1)
        self.assertAlmostEqual(max(v[2] for v in tray['parts']['deck']['vertices']),0,places=5)
        # The rendered convex dice stay inside these walls at every orientation.
        self.assertLessEqual(max(math.sqrt(motion.dot(v,v)) for m in MODELS.values() for v in m['vertices']),tray['die_radius']+.00001)

    def test_contacts_bounce_from_all_four_table_sides(self):
        for axis in (0,1):
            for sign in (-1,1):
                world = motion.make_world(self.rows((6,)),MODELS,3)
                body = world['bodies'][0]
                body['p'] = [0,0,1]
                body['p'][axis] = sign*(motion.TABLE_LIMITS[axis]+.03)
                body['v'][axis] = sign*3
                world['phase'] = 'rolling'
                motion.step(world)
                self.assertLess(body['v'][axis]*sign,0)
                self.assertLessEqual(abs(body['p'][axis]),motion.TABLE_LIMITS[axis])
                self.assertGreater(world['contacts'],0)

    def test_label_square_is_inside_each_original_model_face(self):
        for model in MODELS.values():
            for face in model['faces']:
                for u,v in ((-1,-1),(-1,1),(1,-1),(1,1)):
                    point = [face['center'][i]+face['span']*.5*(u*face['up'][i]+v*face['right'][i]) for i in range(3)]
                    for plane in model['faces']:
                        self.assertLessEqual(motion.dot(point,plane['normal']),motion.dot(plane['center'],plane['normal'])+1e-5)

    def test_mutating_input_after_construction_does_not_change_this_throw(self):
        faces = [3,3,3,5,5,6]
        rows = [dict(faces=faces,value=5)]
        world = motion.make_world(rows,MODELS,8)
        faces[:] = [16]*8
        body = world['bodies'][0]
        self.assertEqual(body['faces'], (3,3,3,5,5,6))
        self.assertEqual(body['faces'][body['result_face']],5)
        motion.throw(world,reduced=True)
        self.assertEqual(body['q'],body['target'])

    def rows(self, sides=(4,6,8)):
        return [dict(faces=tuple(range(1,n+1)),value=n) for n in sides]

    def test_every_result_face_is_visible_and_model_rests_on_table(self):
        for sides, model in MODELS.items():
            for face_index, face in enumerate(model['faces']):
                q = motion.landing_pose(model,face_index)
                self.assertEqual(motion.outcome(model,q),face_index)
                heights = [motion.rotate(q,v)[2] for v in model['vertices']]
                # A real face supports the model, not an edge or a vertex.
                self.assertGreaterEqual(sum(abs(h-min(heights))<.00001 for h in heights),3)

    def test_fixed_step_motion_bounds_landing_and_single_throw(self):
        for sides in ((4,6,8),(10,12,20)):
            for seed, direction in ((1,(-500,-250)),(2,(300,250)),(8,(0,-80))):
                rows = self.rows(sides)
                before = copy.deepcopy(rows)
                world = motion.make_world(rows,MODELS,seed)
                self.assertEqual(world['phase'],'ready')
                self.assertTrue(motion.throw(world,*direction))
                self.assertFalse(motion.throw(world,*direction))
                for _ in range(360):
                    motion.advance(world,1/60)
                self.assertEqual(world['phase'],'settled')
                self.assertGreater(world['contacts'],0)
                self.assertEqual(world['throws'],1)
                self.assertEqual(rows,before)
                for body,row in zip(world['bodies'],rows):
                    self.assertEqual(body['faces'][body['result_face']],row['value'])
                    self.assertEqual(motion.outcome(body['model'],body['q']),body['result_face'])
                    self.assertAlmostEqual(body['p'][2],motion.floor_height(body),places=3)
                    self.assertLessEqual(abs(body['p'][0]),motion.TABLE_LIMITS[0])
                    self.assertLessEqual(abs(body['p'][1]),motion.TABLE_LIMITS[1])
                    self.assertTrue(all(math.isfinite(x) for x in body['p']))

    def test_gesture_changes_trajectory_but_not_faces_or_outcome(self):
        rows = self.rows()
        worlds = [motion.make_world(rows,MODELS,19) for _ in range(3)]
        for world, direction in zip(worlds,((-500,-200),(500,-200),(500,-200))):
            motion.throw(world,*direction)
        for _ in range(60):
            motion.advance(worlds[0],1/60)
            motion.advance(worlds[1],1/60)
        for _ in range(120):
            motion.advance(worlds[2],1/120)
        self.assertNotEqual(worlds[0]['bodies'][0]['p'],worlds[1]['bodies'][0]['p'])
        self.assertEqual(worlds[1]['bodies'],worlds[2]['bodies'])
        for world in worlds:
            self.assertEqual([b['faces'][b['result_face']] for b in world['bodies']],[4,6,8])

    def test_throw_leaves_table_instead_of_losing_launch_to_rotating_corner(self):
        world = motion.make_world(self.rows(),MODELS,2)
        motion.throw(world,300,-400)
        start = [body['p'][0] for body in world['bodies']]
        for _ in range(42):
            motion.advance(world,1/120)
        for body,x in zip(world['bodies'],start):
            self.assertGreater(body['p'][2]-motion.floor_height(body),.2)
            self.assertGreater(body['p'][0]-x,.15)

    def test_reduced_motion_settles_only_after_input(self):
        world = motion.make_world(self.rows(),MODELS,1)
        motion.advance(world,5)
        self.assertEqual(world['phase'],'ready')
        motion.throw(world,reduced=True)
        self.assertEqual(world['phase'],'settled')
        self.assertEqual(world['throws'],1)

    def test_pair_impulse_and_collision_with_settled_die(self):
        for resting in (False,True):
            world = motion.make_world(self.rows((6,6)),MODELS,1)
            motion.throw(world)
            a,b = world['bodies']
            for body in (a,b):
                body['q'] = body['target']
                body['omega'] = [0,0,0]
                body['p'][1] = 0
                body['p'][2] = motion.floor_height(body)
            a['p'][0],b['p'][0] = -.5,.5
            a['v'],b['v'] = [0 if resting else 2,0,0],[-2,0,0]
            a['settled'] = resting
            before = copy.deepcopy(a['p'])
            motion.step(world)
            self.assertGreaterEqual(b['p'][0]-a['p'][0],1.65-1e-6)
            self.assertGreater(b['v'][0]-a['v'][0],0)
            if resting:
                self.assertEqual(a['p'],before)

    def test_d4_corner_labels_repeat_one_value_around_each_vertex(self):
        model = MODELS['4']
        slots = []
        for face in model['faces']:
            self.assertEqual(len(face['labels']),3)
            for vertex,label in zip(face['vertices'],face['labels']):
                self.assertEqual(model['outcome_vertices'][label['slot']],vertex)
                slots.append(label['slot'])
                for u,v in ((-1,-1),(-1,1),(1,-1),(1,1)):
                    point = [label['center'][j]+label['span']*.5*(u*label['up'][j]+v*label['right'][j]) for j in range(3)]
                    for plane in model['faces']:
                        self.assertLessEqual(motion.dot(point,plane['normal']),motion.dot(plane['center'],plane['normal'])+1e-5)
        self.assertEqual([slots.count(i) for i in range(4)],[3]*4)

    def test_initial_symmetries_preserve_geometry_and_cover_all_outcomes(self):
        for model in MODELS.values():
            count = len(model['faces'])
            for i in range(count):
                self.assertEqual({s['permutation'][i] for s in model['symmetries']},set(range(count)))
            for symmetry in model['symmetries']:
                self.assertEqual(sorted(symmetry['permutation']),list(range(count)))
                for vertex in model['vertices']:
                    transformed = motion.rotate(symmetry['q'],vertex)
                    self.assertLess(min(math.dist(transformed,v) for v in model['vertices']),1e-4)

    def test_natural_rest_matches_result_for_100_seeds_and_all_six_shapes(self):
        for seed in range(100):
            for shapes in ((4,6,8),(10,12,20)):
                rows = [dict(faces=tuple(range(1,n+1)),value=seed%n+1) for n in shapes]
                world = motion.make_world(rows,MODELS,seed)
                motion.throw(world,(-1 if seed%2 else 1)*(seed*43%600),-(80+seed*19%500))
                for _ in range(540):
                    motion.advance(world,1/120)
                    if world['phase'] == 'settled':
                        break
                self.assertEqual(world['phase'],'settled',(seed,shapes,world['elapsed']))
                for body in world['bodies']:
                    self.assertEqual(motion.outcome(body['model'],body['q']),body['result_face'])
                    pose = body['q']
                    motion.advance(world,.1)
                    self.assertEqual(body['q'],pose)

    def test_changing_chosen_result_does_not_change_unlabelled_trajectory(self):
        worlds = [motion.make_world([dict(faces=tuple(range(1,21)),value=value)],MODELS,42) for value in (1,20)]
        for world in worlds:
            motion.throw(world,350,-420)
        for _ in range(480):
            for world in worlds:
                motion.advance(world,1/120)
            a,b = [world['bodies'][0] for world in worlds]
            if worlds[0]['elapsed']:
                self.assertEqual(a['p'],b['p'])
                self.assertEqual(a['physics_q'],b['physics_q'])


if __name__ == '__main__':
    unittest.main()
