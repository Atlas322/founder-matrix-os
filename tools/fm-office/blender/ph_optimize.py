"""Poly Haven (CC0) glTF-ийг вэбэд тохируулна: нэгтгэх → decimate → бүтэц 512 → assets/khuvsgul/real/<name>.glb
Ажиллуулах: blender -b -P ph_optimize.py -- <name>:<tris> ..."""
import bpy, sys, os
SRC = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/ph'
OUT = r'D:/CodeBase/founder-matrix-os/tools/fm-office/assets/khuvsgul/real'
os.makedirs(OUT, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
for spec in args:
    name, tris = spec.split(':'); tris = int(tris)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    d = os.path.join(SRC, name); g = next(f for f in os.listdir(d) if f.endswith('.gltf'))
    bpy.ops.import_scene.gltf(filepath=os.path.join(d, g))
    obs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    n = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs)
    for o in obs:   # хувилбар бүрийг тусад нь (вэбэд child mesh = variant)
        k = sum(len(p.vertices) - 2 for p in o.data.polygons)
        if n > tris and k > 50:
            bpy.context.view_layer.objects.active = o; m = o.modifiers.new('dec', 'DECIMATE'); m.ratio = max(.005, tris / n)
            with bpy.context.temp_override(object=o, active_object=o): bpy.ops.object.modifier_apply(modifier='dec')
    o = obs[0]
    for img in bpy.data.images:
        if img.size[0] > 512: img.scale(512, 512 * img.size[1] // img.size[0])
    nn = sum(sum(len(p.vertices) - 2 for p in q.data.polygons) for q in obs); dim = [(q.name, tuple(round(x, 2) for x in q.dimensions)) for q in obs][:6]
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + '.glb'), export_format='GLB', export_image_format='JPEG', export_jpeg_quality=82, use_selection=False)
    print('OPT', name, n, '->', nn, 'dims', dim, os.path.getsize(os.path.join(OUT, name + '.glb')) // 1024, 'KB')
