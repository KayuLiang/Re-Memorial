"""Build the approved plain tray; export asset-only GLB and actual Blender views.

Run: blender --background --python tools/build_simple_check_table.py
This authoring asset is separate from the older Ren'Py table renderer.
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'art_exports/check_table/simple_v3'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def material(name, color, roughness, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Roughness'].default_value = roughness
    node.inputs['Metallic'].default_value = metallic
    return mat


deck_mat = material('Deck | rigid sage composite', (.042, .054, .037), .64)
shell_mat = material('Body | graphite coating', (.025, .029, .027), .46)
cap_mat = material('Cap | warm ivory coating', (.68, .625, .51), .30, .12)
gold_mat = material('Corners | satin champagne alloy', (.49, .33, .145), .26, .72)
die_mat = material('Preview dice | blue graphite', (.034, .052, .073), .30, .16)
label_mat = material('Preview numerals | gold', (.62, .405, .14), .33, .48)
ground_mat = material('Studio | ivory', (.78, .747, .668), .8)

asset = bpy.data.collections.new('ASSET | plain rectangular tray')
scene.collection.children.link(asset)
preview = bpy.data.collections.new('PREVIEW ONLY | existing dice geometry')
scene.collection.children.link(preview)
studio = bpy.data.collections.new('STUDIO | cameras and lighting')
scene.collection.children.link(studio)


def mesh_object(name, vertices, faces, mat, collection=asset, bevel=.02):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    mesh.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new('Uniform edge radius', 'BEVEL')
        mod.width, mod.segments = bevel, 3
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(20)
        mod.harden_normals = True
        for face in mesh.polygons:
            face.use_smooth = True
        normal = obj.modifiers.new('Planar face normals', 'WEIGHTED_NORMAL')
        normal.keep_sharp = True
        normal.weight = 50
    return obj


def rounded_loop(hx, hy, radius, z, steps=20):
    return [(sx*(hx-radius)+radius*math.cos(a),
             sy*(hy-radius)+radius*math.sin(a), z)
            for corner, (sx, sy) in enumerate(((1,1),(-1,1),(-1,-1),(1,-1)))
            for i in range(steps+1)
            for a in [(corner+i/steps)*math.pi/2]]


def prism(name, outline, bottom, top, mat, bevel=.02):
    n = len(outline)
    vertices = [(x,y,z) for z in (bottom,top) for x,y in outline]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh_object(name, vertices, faces, mat, bevel=bevel)


# The four corner arcs share centers with the inner and outer rectangular loops.
# Nothing projects below this one constant bottom plane.
HX, HY, RADIUS, WIDTH = 5.26, 2.96, .68, .50
CX, CY = HX-RADIUS, HY-RADIUS
INNER_X, INNER_Y, INNER_R = HX-WIDTH, HY-WIDTH, RADIUS-WIDTH
BOTTOM, WALL_TOP, CAP_TOP = -.28, .48, .59
loops = [rounded_loop(HX,HY,RADIUS,BOTTOM),
         rounded_loop(HX,HY,RADIUS,WALL_TOP),
         rounded_loop(INNER_X,INNER_Y,INNER_R,WALL_TOP),
         rounded_loop(INNER_X,INNER_Y,INNER_R,BOTTOM)]
n = len(loops[0])
faces = [(row*n+i,row*n+(i+1)%n,((row+1)%4)*n+(i+1)%n,((row+1)%4)*n+i)
         for row in range(4) for i in range(n)]
body = mesh_object('Continuous body | no logo, feet or bottom cutouts',
                   sum(loops, []), faces, shell_mat, bevel=.025)
outline = [(x,y) for x,y,z in rounded_loop(INNER_X+.012,INNER_Y+.012,INNER_R+.012,0)]
deck = prism('Inset playing slab', outline, BOTTOM, 0, deck_mat, .009)

# Four simple straight caps; four corner pieces reuse EXACTLY the same mesh.
seam = .006
for name, x0,x1,y0,y1 in (
        ('North',-CX+seam,CX-seam,INNER_Y,HY),
        ('South',-CX+seam,CX-seam,-HY,-INNER_Y),
        ('West',-HX,-INNER_X,-CY+seam,CY-seam),
        ('East',INNER_X,HX,-CY+seam,CY-seam)):
    prism(name+' ivory cap',[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],
          WALL_TOP-.012,CAP_TOP,cap_mat,.028)
arc_steps = 20
angles = [seam/RADIUS+(math.pi/2-2*seam/RADIUS)*i/arc_steps for i in range(arc_steps+1)]
outline = [(RADIUS*math.cos(a),RADIUS*math.sin(a)) for a in angles]
outline += [(INNER_R*math.cos(a),INNER_R*math.sin(a)) for a in reversed(angles)]
corner = prism('Gold corner 1 | linked source',outline,WALL_TOP-.012,CAP_TOP,gold_mat,.025)
corners = []
for i, (x,y) in enumerate(((CX,CY),(-CX,CY),(-CX,-CY),(CX,-CY))):
    obj = corner if i == 0 else corner.copy()
    if i:
        asset.objects.link(obj)
        obj.name = 'Gold corner {} | linked'.format(i+1)
    obj.location = (x,y,0)
    obj.rotation_euler.z = i*math.pi/2
    corners.append(obj)

# Actual geometric checks, including the user's asymmetric-corner failure case.
assert len(asset.objects) == 10
assert len({obj.data.as_pointer() for obj in corners}) == 1
assert all(abs(v.co.z-CAP_TOP)<1e-6 or abs(v.co.z-(WALL_TOP-.012))<1e-6
           for v in corner.data.vertices)
for obj in asset.objects:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    assert all(e.is_manifold for e in bm.edges), obj.name
    bm.free()
    assert min(v.co.z for v in obj.data.vertices) >= BOTTOM-1e-6

bpy.ops.object.select_all(action='DESELECT')
for obj in asset.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=str(OUT/'check_table_simple.glb'),
    export_format='GLB',use_selection=True,export_apply=True,export_yup=True)

# Preview uses the existing Blender-derived dice and its real face-label layout.
# These are excluded from the tray GLB and keep editable text, not baked numbers.
models = json.loads((ROOT/'game/gui/dice_obsidian/realtime.json').read_text(encoding='utf-8'))
for sides, xy, yaw in ((6,(-2.20,.12),-.16),(4,(0,.48),.22),(8,(2.15,-.35),.16)):
    model = models[str(sides)]
    normal = Vector(model['faces'][0]['normal'])
    rotation = Quaternion((0,0,1),yaw) @ normal.rotation_difference(Vector((0,0,-1)))
    vertices = [rotation @ Vector(v) for v in model['vertices']]
    z = -min(v.z for v in vertices)+.003
    die = mesh_object('Preview D'+str(sides),[list(v) for v in vertices],
        [f['vertices'] for f in model['faces']],die_mat,preview,.022)
    die.location = (*xy,z)
    for i, face in enumerate(model['faces']):
        labels = face.get('labels',[dict(face,slot=i)])
        for label in labels:
            curve = bpy.data.curves.new('Mutable face preview','FONT')
            curve.body = str(label['slot']+1)
            curve.align_x,curve.align_y = 'CENTER','CENTER'
            curve.size = label['span']*.68
            curve.extrude = .0008
            curve.materials.append(label_mat)
            text = bpy.data.objects.new('D{} face {} slot {}'.format(sides,i,label['slot']),curve)
            preview.objects.link(text)
            right,up,norm = [rotation @ Vector(v) for v in (label['right'],label['up'],face['normal'])]
            text.rotation_euler = Matrix((right,up,norm)).transposed().to_euler()
            text.location = die.location + rotation @ Vector(label['center']) + norm*.004

floor = mesh_object('Studio ground',[(-200,-200,BOTTOM-.005),(200,-200,BOTTOM-.005),
    (200,200,BOTTOM-.005),(-200,200,BOTTOM-.005)],[(0,1,2,3)],ground_mat,studio,0)


def camera(name, pos, target, scale):
    data = bpy.data.cameras.new(name)
    data.type, data.ortho_scale = 'ORTHO',scale
    obj = bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj


hero = camera('Camera | hero',(8,-12,11),(0,0,0),13.8)
overhead = camera('Camera | overhead',(0,0,18),(0,0,0),12.4)
detail = camera('Camera | corner',(8.6,-8.2,5.4),(4.55,-2.28,.24),3.6)
for name,pos,power,size,color in (
        ('Key',(-3,-4,9),1900,5,(1,.92,.79)),
        ('Fill',(3,4,7),550,5,(.79,.87,1)),
        ('Softbox',(0,-1,10),350,4,(1,1,1))):
    data = bpy.data.lights.new(name,'AREA')
    data.energy,data.shape,data.size,data.color = power,'DISK',size,color
    obj = bpy.data.objects.new(name,data)
    studio.objects.link(obj)
    obj.location = pos
    obj.rotation_euler = (-obj.location).to_track_quat('-Z','Y').to_euler()
scene.world = bpy.data.worlds.new('Neutral studio world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.68,.72,.78,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .25
scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.camera = hero
scene.render.resolution_x,scene.render.resolution_y = 1600,1100
scene.render.filepath = str(OUT/'hero.png')
bpy.context.preferences.filepaths.save_version = 0
# Open the file already framed on the modeled asset.
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'check_table_simple.blend'))
for name,cam,size in (('hero',hero,(1600,1100)),('overhead',overhead,(1600,1000)),
                      ('corner',detail,(1100,1000))):
    scene.camera = cam
    scene.render.resolution_x,scene.render.resolution_y = size
    scene.render.filepath = str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
report = dict(objects=len(asset.objects),shared_corner_mesh=True,closed_meshes=True,
              dimensions=[HX*2,HY*2,CAP_TOP-BOTTOM],playing_surface_z=0,
              rail_height=CAP_TOP,base_z=BOTTOM,
              materials=[m.name for m in (deck_mat,shell_mat,cap_mat,gold_mat)])
(OUT/'model-info.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TRAY MODEL COMPLETE',json.dumps(report))
