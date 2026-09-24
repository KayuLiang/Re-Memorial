"""Build the stylised dice tray and its four real raised rails in Blender."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from game.systems import rm_dice_motion as motion
source = root/'art_exports/check_table'
source.mkdir(parents=True,exist_ok=True)
out = root/'game/gui/dice_obsidian'
bpy.ops.wm.read_factory_settings(use_empty=True)

# One editable palette is exported for the runtime shader as well as Blender.
palette = dict(deck=[.56,.64,.60],shell=[.115,.17,.18],cap=[.73,.76,.68],
               accent=[.76,.60,.31],shadow=[.18,.26,.27])
materials = {}
for name,color in palette.items():
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color,1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = material.diffuse_color
    bsdf.inputs['Roughness'].default_value = .48 if name=='deck' else .32
    materials[name] = material

radius = .82
inner = [limit+radius for limit in motion.TABLE_LIMITS]
rail_width,rail_height = .34,.30
outer = [value+rail_width for value in inner]
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.12))
deck = bpy.context.object
deck.name = 'Inset_Deck'
deck.dimensions = (outer[0]*2,outer[1]*2,.24)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
bevel = deck.modifiers.new('Deck cut edge','BEVEL')
bevel.width,bevel.segments = .055,1
bpy.ops.object.modifier_apply(modifier=bevel.name)
deck.data.materials.append(materials['deck'])
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)

def rail(name,axis,sign,half_length):
    # Convex cross-section: inner cushion, sloped shoulder, cap and shell.
    profile = [(0,-.18),(rail_width,-.18),(rail_width,rail_height-.08),
               (rail_width-.06,rail_height),(.06,rail_height),(0,rail_height-.08)]
    vertices = []
    for end in (-half_length,half_length):
        for offset,z in profile:
            p = [0,0,z]
            p[axis] = sign*(inner[axis]+offset)
            p[1-axis] = end
            vertices.append(p)
    n = len(profile)
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for material in ('shell','cap','accent'):
        mesh.materials.append(materials[material])
    for face in mesh.polygons:
        face.material_index = 1 if face.normal.z > .5 else 0
    return obj

parts = {'deck':deck}
for name,axis,sign in [('north',1,1),('south',1,-1),('west',0,-1),('east',0,1)]:
    bpy.ops.object.select_all(action='DESELECT')
    parts[name] = rail('Rail_'+name,axis,sign,outer[0] if axis==1 else inner[1])
meshes = {}
for name,obj in parts.items():
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    filename = 'tabletop.glb' if name=='deck' else 'tabletop-'+name+'.glb'
    bpy.ops.export_scene.gltf(filepath=str(out/filename),export_format='GLB',use_selection=True,export_yup=False)
    meshes[name] = dict(file=filename,vertices=[list(v.co) for v in obj.data.vertices])
data = dict(parts=meshes,palette=palette,play_limits=list(motion.TABLE_LIMITS),
            die_radius=radius,wall_inner_planes=inner,rail_height=rail_height,rail_width=rail_width)
(out/'tabletop.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')

bpy.ops.object.camera_add(location=(7,-9,9))
camera = bpy.context.object
camera.rotation_euler = (Vector((0,0,0))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.type,camera.data.ortho_scale = 'ORTHO',12.4
bpy.context.scene.camera = camera
for position,energy,size in (((-3,-4,8),1100,5),((4,2,6),400,5)):
    bpy.ops.object.light_add(type='AREA',location=position)
    light = bpy.context.object
    light.data.energy,light.data.shape,light.data.size = energy,'DISK',size
    light.rotation_euler = (Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
scene = bpy.context.scene
scene.world = bpy.data.worlds.new('Studio')
scene.world.color = (.20,.20,.20)
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage = 1280,720,100
scene.render.film_transparent = True
scene.render.filepath = str(source/'tabletop-preview.png')
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(source/'check_table.blend'))
bpy.ops.render.render(write_still=True)
