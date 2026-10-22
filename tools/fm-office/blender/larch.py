"""Хөвсгөлийн алтан шинэс — stylized, сэвсгэр (навчны карт), гэрэл/AO-г vertex color-д «bake» хийсэн.

Ажиллуулах:  blender -b -P blender/larch.py -- <out.glb> [preview.png] [seed]
Гаралт: GLB (Three.js-д шууд), сонголтоор EEVEE preview.
Хэв маяг: E2 палитр — алтан шар (#E8A93A) → улбар шар (#C9702A), дотор тал бараан (хуурамч AO), их бие хар хүрэн.
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "larch.glb"
PNG = argv[1] if len(argv) > 1 else None
SEED = int(argv[2]) if len(argv) > 2 else 3
rnd = random.Random(SEED)

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def srgb(h):                                                   # hex → linear RGBA (glTF COLOR_0 шугаман)
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c) + (1.0,)


GOLD, AMBER, DEEP, BARK, BARK2 = srgb("#F2BE4E"), srgb("#D9822B"), srgb("#7A3A1C"), srgb("#4A2C1E"), srgb("#6B4330")

bm = bmesh.new()
col = bm.loops.layers.color.new("Col")

# ── их бие: бага зэрэг муруй, дээшээ нарийсна ──
H, segs, sides = 7.5, 10, 7
rings = []
for s in range(segs + 1):
    t = s / segs
    r = .32 * (1 - t) ** 1.1 + .03
    off = Vector((math.sin(t * 2.3) * .12, math.cos(t * 1.7) * .08, 0))
    rings.append([bm.verts.new(Vector((math.cos(a) * r, math.sin(a) * r, t * H)) + off) for a in [i / sides * math.tau for i in range(sides)]])
for s in range(segs):
    for i in range(sides):
        f = bm.faces.new((rings[s][i], rings[s][(i + 1) % sides], rings[s + 1][(i + 1) % sides], rings[s + 1][i]))
        for lp in f.loops:
            lp[col] = lerp(BARK, BARK2, lp.vert.co.z / H)

# ── навч: давхаргатай конус дагуу «бөөгнөрөл» (карт) — салаа бүрт 3 ширхэг огтлолцсон карт ──
def card(center, size, normal_hint, shade):
    # огтлолцсон хоёр квад (X хэлбэр) — ямар ч өнцгөөс сэвсгэр харагдана
    for rot in (0, math.pi / 2, math.pi / 4):
        ang = rnd.random() * math.tau + rot
        u = Vector((math.cos(ang), math.sin(ang), rnd.uniform(-.25, .25))).normalized() * size
        v = Vector((0, 0, size * .8))
        q = [center - u - v * .5, center + u - v * .5, center + u + v * .5, center - u + v * .5]
        f = bm.faces.new([bm.verts.new(p) for p in q])
        for k, lp in enumerate(f.loops):
            top = 1.0 if k >= 2 else .0
            c = lerp(AMBER, GOLD, min(1, shade * .85 + top * .3))   # гадна/дээд = алтан, дотор/доод = улбар
            c = lerp(DEEP, c, .35 + .65 * shade)                      # хуурамч AO
            lp[col] = c


tiers = 9
for ti in range(tiers):
    t = ti / (tiers - 1)
    z = 1.8 + t * (H - 1.6)
    R = 2.1 * (1 - t) ** 1.05 + .25
    n = int(10 + 14 * (1 - t))
    for k in range(n):
        a = k / n * math.tau + rnd.uniform(-.25, .25) + ti * .7
        rr = R * rnd.uniform(.55, 1.0)
        c = Vector((math.cos(a) * rr, math.sin(a) * rr, z + rnd.uniform(-.35, .25) - rr * .18))
        shade = min(1, .25 + .75 * (rr / (R + .01)) * (.6 + .4 * t))
        card(c, rnd.uniform(.38, .62) * (1.1 - t * .3), None, shade)
# оройн гоо
card(Vector((0, 0, H + .1)), .35, None, 1)

me = bpy.data.meshes.new("larch")
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("larch", me)
scn.collection.objects.link(ob)

mat = bpy.data.materials.new("larch_vc")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = .9
ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Col"
nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
mat.use_backface_culling = False
me.materials.append(mat)
for p in me.polygons:
    p.use_smooth = False

bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=False, export_apply=True,
                          **({"export_vertex_color": "ACTIVE"} if "export_vertex_color" in bpy.ops.export_scene.gltf.get_rna_type().properties else {}))
print("GLB:", OUT, len(me.polygons), "faces")

if PNG:
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam)
    cam.location = (11, -11, 7.5); cam.rotation_euler = (math.radians(68), 0, math.radians(45)); scn.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scn.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.data.color = (1, .82, .66); sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = srgb("#3B3F7A"); w.node_tree.nodes["Background"].inputs[1].default_value = .9
    scn.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
    scn.render.resolution_x, scn.render.resolution_y = 900, 900
    scn.render.filepath = PNG
    bpy.ops.render.render(write_still=True)
    print("PNG:", PNG)
