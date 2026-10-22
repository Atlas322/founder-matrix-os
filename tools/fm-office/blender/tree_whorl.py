"""fir_sapling (Poly Haven CC0)-ийг дээрээс нь ortho камераар render → тунгалаг дэвсгэртэй «мөчрийн цагираг» (whorl) зураг.
Вэбэд мод = их бие + энэ зургаар хийсэн унжсан диск 8–10 давхар (эзэлхүүнтэй шилмүүст мод).
blender -b -P tree_whorl.py → assets/khuvsgul/real/fir_whorl.png"""
import bpy, os, math, mathutils
SRC = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/ph/fir_sapling/fir_sapling_1k.gltf'
OUT = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/real'
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE', 'CYCLES'):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 512
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs[0].default_value = (.8, .85, .95, 1); bg.inputs[1].default_value = 1.1
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3; sun.rotation_euler = (math.radians(20), 0, math.radians(40)); sc.collection.objects.link(sun)
meshes = [o for o in sc.objects if o.type == 'MESH']; tgt = meshes[0]
for o in meshes: o.hide_render = o is not tgt
# 4 удаа эргүүлж давхарлаад дүүрэн цагираг болгоно
for k in range(1, 4):
    d = tgt.copy(); d.data = tgt.data; sc.collection.objects.link(d); d.rotation_euler.z += k * math.pi / 2 + .3; d.hide_render = False
bb = [tgt.matrix_world @ mathutils.Vector(c) for c in tgt.bound_box]; cx = sum(v.x for v in bb) / 8; cy = sum(v.y for v in bb) / 8
r = max(max(abs(v.x - cx) for v in bb), max(abs(v.y - cy) for v in bb))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); cam.data.type = 'ORTHO'; cam.data.ortho_scale = r * 2.05; sc.collection.objects.link(cam); sc.camera = cam
cam.location = (cx, cy, max(v.z for v in bb) + 5); cam.rotation_euler = (0, 0, 0)
sc.render.filepath = os.path.join(OUT, 'fir_whorl.png'); bpy.ops.render.render(write_still=True); print('WHORL', round(r, 2))
