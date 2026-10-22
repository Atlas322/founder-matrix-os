"""Poly Haven fir_sapling (CC0, бүрэн нарийвчлал) → тунгалаг дэвсгэртэй impostor зураг (cross-billboard мод).
blender -b -P tree_impostor.py → assets/khuvsgul/real/fir_card_{a,b,c}.png"""
import bpy, os, math
SRC = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/ph/fir_sapling/fir_sapling_1k.gltf'
OUT = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/real'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    try: sc.render.engine = 'BLENDER_EEVEE'
    except TypeError: sc.render.engine = 'CYCLES'
sc.render.film_transparent = True; sc.render.resolution_x = 512; sc.render.resolution_y = 768
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (.75, .82, .95, 1); bg.inputs[1].default_value = .9
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.2; sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sc.collection.objects.link(sun)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.type = 'ORTHO'; sc.collection.objects.link(cam); sc.camera = cam
meshes = [o for o in sc.objects if o.type == 'MESH']
# бүтэн титэм: хувилбар бүрийг 3 удаа (72°, 144°) эргүүлж давхарлана → сийрэг биш, дүүрэн мод
import mathutils
for o in list(meshes):
    for k, rz in enumerate((math.radians(72), math.radians(144))):
        d = o.copy(); d.data = o.data; sc.collection.objects.link(d); d.rotation_euler.z += rz; d.scale = (o.scale.x * (.92 - k * .06),) * 3; d.parent = None; d['src'] = o.name

allm = [o for o in sc.objects if o.type == 'MESH']
for tgt in meshes:
    grp = [o for o in allm if o is tgt or o.get('src') == tgt.name]
    for o in allm: o.hide_render = o not in grp
    bb = [tgt.matrix_world @ __import__('mathutils').Vector(c) for c in tgt.bound_box]
    xs = [v.x for v in bb]; ys = [v.y for v in bb]; zs = [v.z for v in bb]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2; h = max(zs) - min(zs); wd = max(max(xs) - min(xs), max(ys) - min(ys))
    cam.data.ortho_scale = max(h * 1.02, wd * 1.02 * 768 / 512)
    cam.location = (cx, cy - 20, min(zs) + cam.data.ortho_scale / 2 * 1.0 - (cam.data.ortho_scale - h) / 2 + 0)
    cam.location.z = min(zs) + cam.data.ortho_scale / 2  # доод ирмэг = модны ёроол
    cam.rotation_euler = (math.radians(90), 0, 0)
    tag = tgt.name.split('_')[-1]
    sc.render.filepath = os.path.join(OUT, f'fir_dense_{tag}.png'); bpy.ops.render.render(write_still=True)
    print('CARD', tag, round(h, 2), round(wd, 2), round(cam.data.ortho_scale, 2))
