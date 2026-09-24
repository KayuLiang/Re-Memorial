"""Export a tumbling/landing clip from the existing dice, with live-number projection.

Blender --background --python tools/render_dice_roll.py -- 4 6 8 10 12 20
No game rule, RNG, or baked example numeral is involved.
"""
from pathlib import Path
import json
import math
import sys

import bpy
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'game/gui/dice_obsidian/roll'
OUT.mkdir(parents=True, exist_ok=True)
SIDES = [int(arg) for arg in sys.argv[sys.argv.index('--')+1:]] if '--' in sys.argv else [4,6,8,10,12,20]
FRAMES = 42

for sides in SIDES:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'art_exports/D20_SAMPLE_20260920/obsidian_models' / ('d%d.blend' % sides)))
    scene = bpy.context.scene
    die = next(obj for obj in scene.objects if obj.type == 'MESH')
    die.rotation_mode = 'QUATERNION'
    die.rotation_quaternion = Quaternion()
    axes = []
    for face in die.data.polygons:
        center, normal = face.center.copy(), face.normal.copy()
        corners = [die.data.vertices[i].co for i in face.vertices]
        up = (max(corners, key=lambda v:(v.z,v.y))-center).normalized()
        right = up.cross(normal).normalized()
        span = max((v-center).length for v in corners)*.74
        axes.append((center+normal*.018, normal, right, up, span))
    # One physical supporting face is horizontal at rest. D4 is read from its
    # visible side; the other dice expose an upward result face.
    rest = die.data.polygons[0].normal.rotation_difference(Vector((0,0,-1)))
    camera = scene.camera
    camera.rotation_euler = (Vector((0,0,.25))-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale = 5.2
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.color_mode = 'RGBA'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'OPTIX'
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == 'OPTIX'
    scene.cycles.device = 'GPU'
    scene.render.use_persistent_data = True
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-1.65))
    bpy.context.object.is_shadow_catcher = True
    metadata = []

    def project(point):
        p = world_to_camera_view(scene, camera, die.matrix_world @ point)
        # Match RMDiceArt's existing 800-unit projection convention.
        return Vector((p.x*800,(1-p.y)*800))

    for index in range(FRAMES):
        t = index/(FRAMES-1)
        u = min(1,t/.88)
        remaining = (1-u)**2
        tumble = (Quaternion((1,0,0), remaining*math.pi*3.4)
                  @ Quaternion((0,1,0), remaining*math.pi*2.6)
                  @ Quaternion((0,0,1), remaining*math.pi*1.2))
        if t > .88:
            settle = (t-.88)/.12
            tumble = Quaternion((1,0,0), .06*math.sin(settle*math.pi*2)*(1-settle))
        die.rotation_quaternion = tumble @ rest
        if t < .42:
            hop = 1.15*(1-(t/.42)**2)
        elif t < .71:
            hop = .46*math.sin(math.pi*(t-.42)/.29)
        elif t < .88:
            hop = .15*math.sin(math.pi*(t-.71)/.17)
        else:
            hop = 0
        bottom = min((die.rotation_quaternion @ vertex.co).z for vertex in die.data.vertices)
        die.location = (-.55*remaining,0,-1.65-bottom+hop)
        bpy.context.view_layer.update()
        entries = []
        for face_index,(center,normal,right,up,span) in enumerate(axes):
            world_normal = die.rotation_quaternion @ normal
            if world_normal.dot(camera.location.normalized()) <= .12:
                continue
            c = project(center)
            dx,dy = project(center+right*span)-c,project(center-up*span)-c
            entries.append(dict(index=face_index,center=list(c),basis=[dx.x,dy.x,dx.y,dy.y]))
        metadata.append(entries)
        scene.render.filepath = str(OUT / ('d%d-%02d.png' % (sides,index)))
        bpy.ops.render.render(write_still=True)
    result_face = max(metadata[-1], key=lambda entry: (rest @ axes[entry['index']][1]).z + .2*(rest @ axes[entry['index']][1]).dot(camera.location.normalized()))['index']
    (OUT / ('d%d.json' % sides)).write_text(json.dumps(dict(frames=metadata,result_face=result_face)),encoding='utf-8')
    print('ROLL_COMPLETE',sides,flush=True)
