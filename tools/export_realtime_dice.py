"""Export the approved Blender dice's convex faces for runtime projection."""
import json
import math
from pathlib import Path
import bpy
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from game.systems import rm_dice_motion as motion
models = {}
for sides in (4, 6, 8, 10, 12, 20):
    bpy.ops.wm.open_mainfile(filepath=str(root / 'art_exports/D20_SAMPLE_20260920/obsidian_models' / ('d%d.blend' % sides)))
    die = next(obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
    scale = .82 / max(vertex.co.length for vertex in die.data.vertices)
    vertices = [list(vertex.co * scale) for vertex in die.data.vertices]
    faces = []
    for face in die.data.polygons:
        corners = [die.data.vertices[index].co for index in face.vertices]
        up = (max(corners, key=lambda v: (v.z, v.y)) - face.center).normalized()
        right = up.cross(face.normal).normalized()
        # A centered square within the nearest edge, with 10% breathing room.
        # This is the complete label footprint, not a radius for the shader
        # to multiply again. It works for triangular and kite faces too.
        inset = min((b-a).cross(face.center-a).length / (b-a).length
                    for a,b in zip(corners,corners[1:]+corners[:1]))
        faces.append(dict(vertices=list(face.vertices), normal=list(face.normal),
            center=list(face.center*scale), up=list(up), right=list(right),
            span=inset*scale*math.sqrt(2)*.9))
    model = dict(vertices=vertices, faces=faces)
    if sides == 4:
        # Outcome slot i is the vertex opposite physical face i. Preserve the
        # four rule slots; each vertex repeats its value on three faces.
        model['outcome_vertices'] = [next(v for v in range(4) if v not in f['vertices']) for f in faces]
        for face in faces:
            face['labels'] = []
            for vertex in face['vertices']:
                up = motion.unit([vertices[vertex][j]-face['center'][j] for j in range(3)])
                face['labels'].append(dict(slot=model['outcome_vertices'].index(vertex),
                    center=[face['center'][j]+.40*(vertices[vertex][j]-face['center'][j]) for j in range(3)],
                    up=up,right=motion.cross(up,face['normal']),span=face['span']*.60))
    # A rigid symmetry changes initial orientation without changing the world
    # vertex set. Runtime uses it before release, never to correct a landing.
    symmetries = []
    source = faces[0]
    source_vertex = vertices[source['vertices'][0]]
    for target in faces:
        base = motion.align(source['normal'],target['normal'])
        a = motion.rotate(base,[source_vertex[j]-source['center'][j] for j in range(3)])
        for vertex in target['vertices']:
            b = [vertices[vertex][j]-target['center'][j] for j in range(3)]
            angle = math.atan2(motion.dot(target['normal'],motion.cross(a,b)),motion.dot(a,b))
            q = motion.multiply(motion.axis_angle(target['normal'],angle),base)
            mapped = [motion.rotate(q,v) for v in vertices]
            if any(min(math.dist(v,w) for w in vertices)>1e-4 for v in mapped):
                continue
            permutation = [min(range(sides),key=lambda j: math.dist(motion.rotate(q,f['normal']),faces[j]['normal'])) for f in faces]
            symmetries.append(dict(q=q,permutation=permutation))
    assert len(symmetries) == {4:12,6:24,8:24,10:10,12:60,20:60}[sides], (sides,len(symmetries))
    model['symmetries'] = symmetries
    models[str(sides)] = model
out = root / 'game/gui/dice_obsidian/realtime.json'
out.write_text(json.dumps(models, separators=(',', ':')), encoding='utf-8')
print('EXPORTED', out, flush=True)
