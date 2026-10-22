"""Монгол гэр — hero asset (тоглоомын «Миний өрөө»). Low-poly, stylized, Ghibli-маягийн зөөлөн.

Ажиллуулах:  blender -b -P blender/ger.py -- <out.glb> [preview.png]
Бүтэц: эсгий бүрээс (ханан + дээвэр, бага зэрэг хотойсон) · гурван бүслүүр олс · тооно + хараач · улаан-улбар будсан хаалга, хүрээ · модон шал/суурь
Масштаб: диаметр 6 м, ханын өндөр 1.7 м, тооно 3.4 м. Хаалга +X тал руу.
"""
import bpy, bmesh, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "ger.glb"
PNG = argv[1] if len(argv) > 1 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
R, WALL, TOP, SEG = 3.0, 1.7, 3.4, 32


def mat(name, h, rough=.9, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c] + [1]
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = c; b.inputs["Emission Strength"].default_value = emit
    return m


FELT, FELT2, ROPE = mat("felt", "#F2EDE3"), mat("felt_shade", "#E2D9CA"), mat("rope", "#3B2E28")
DOOR, FRAME, GOLD = mat("door", "#D2502F"), mat("door_frame", "#E08A2E"), mat("ornament", "#F2C14E", .5)
WOOD, BASE, WARM = mat("wood", "#8A5A3B"), mat("base", "#8C867A"), mat("warm_light", "#FFB45C", 1, 4)
parts = []


def add(me, m, name):
    o = bpy.data.objects.new(name, me); scn.collection.objects.link(o); o.data.materials.append(m); parts.append(o); return o


def ring_mesh(name, profile, m, seg=SEG, gap=None):
    """profile: [(r, z), ...] доороос дээш. gap=(a0,a1) радиан — хаалганы нүх."""
    bm = bmesh.new(); rows = []
    angs = [i / seg * math.tau for i in range(seg + 1)]
    for r, z in profile:
        rows.append([bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)) for a in angs])
    for j in range(len(rows) - 1):
        for i in range(seg):
            mid = (angs[i] + angs[i + 1]) / 2
            if gap and gap[0] < (mid + math.pi) % math.tau - math.pi < gap[1] and j < gap[2]:
                continue
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return add(me, m, name)


# хана: доод хэсэг бага зэрэг тэлсэн, дээд ирмэг нь дугуйрсан
DOOR_W = .5                                                                     # хагас өнцөг (рад) биш — доор тооцно
gap_a = math.asin(.55 / R)
ring_mesh("wall", [(R + .04, 0), (R, .4), (R, 1.2), (R - .02, WALL)], FELT, gap=(-gap_a, gap_a, 2))
# дээвэр: хотойсон хэлбэр (ханын оройгоос тооно руу), захаараа бага зэрэг унжсан
roof = [(R + .18, WALL - .12), (R + .05, WALL + .05)]
for k in range(1, 8):
    t = k / 7
    roof.append((R + .05 - (R - .55) * t, WALL + .05 + (TOP - WALL - .05) * (t ** .85)))
ring_mesh("roof", roof, FELT2)
# тооно (цагираг) + хараач
ring_mesh("toono", [(.62, TOP - .05), (.62, TOP + .12), (.5, TOP + .12), (.5, TOP - .05)], WOOD, seg=16)
ring_mesh("toono_cap", [(.66, TOP + .1), (.45, TOP + .32), (.05, TOP + .4)], FELT, seg=16)
# бүслүүр олс: хананы дээр 3, дээврийн дээр загалмай
for z in (.35, .95, 1.5):
    ring_mesh(f"rope_{z}", [(R + .06, z - .03), (R + .07, z), (R + .06, z + .03)], ROPE, gap=(-gap_a, gap_a, 9))
for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
    bm = bmesh.new(); pts = [(R + .2, WALL - .1)] + roof[2:]
    vs = []
    for r, z in pts:
        for d in (-.04, .04):
            p = Vector((math.cos(a) * (r + .03), math.sin(a) * (r + .03), z + .02)) + Vector((-math.sin(a) * d, math.cos(a) * d, 0))
            vs.append(bm.verts.new(p))
    for i in range(0, len(vs) - 2, 2):
        bm.faces.new((vs[i], vs[i + 1], vs[i + 3], vs[i + 2]))
    me = bpy.data.meshes.new("rope_roof"); bm.to_mesh(me); bm.free(); add(me, ROPE, "rope_roof")

# хаалга: хүрээ + хоёр хавтас + алтан хээ (энгийн ромбо) — хаалгаар дотрын дулаан гэрэл харагдана
def box(name, m, loc, size, rot=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o = bpy.context.active_object; o.name = name
    o.scale = size; o.rotation_euler.z = rot; o.data.materials.append(m); parts.append(o); return o
X = R - .02
box("door_frame_l", FRAME, (X, -.6, .78), (.16, .1, 1.56)); box("door_frame_r", FRAME, (X, .6, .78), (.16, .1, 1.56))
box("door_frame_t", FRAME, (X, 0, 1.6), (.16, 1.3, .14)); box("door_sill", FRAME, (X + .02, 0, .06), (.2, 1.3, .12))
box("door_l", DOOR, (X + .02, -.27, .8), (.06, .52, 1.42)); box("door_r", DOOR, (X + .02, .27, .8), (.06, .52, 1.42))
for y in (-.27, .27):
    for z in (.45, 1.15):
        o = box("door_orn", GOLD, (X + .06, y, z), (.02, .2, .2)); o.rotation_euler.x = math.pi / 4
box("inside_glow", WARM, (X - .25, 0, .8), (.05, 1.0, 1.4))                     # хаалганы цаад шар гэрэл (bloom-д)
# суурь: модон шал, чулуун хүрээ
ring_mesh("floor_edge", [(R + .35, -.12), (R + .35, .02), (R + .1, .05)], BASE)
bpy.ops.mesh.primitive_cylinder_add(vertices=SEG, radius=R + .1, depth=.12, location=(0, 0, -.02)); o = bpy.context.active_object; o.data.materials.append(WOOD); parts.append(o)
box("step", BASE, (R + .55, 0, .04), (.6, 1.3, .12))

for o in parts:
    for p in o.data.polygons: p.use_smooth = False
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join(); ger = bpy.context.active_object; ger.name = "Ger"
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True)
print("GLB:", OUT, len(ger.data.polygons), "faces")

if PNG:
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -.08)); g = bpy.context.active_object; g.data.materials.append(mat("grass", "#6E8F45"))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam)
    cam.location = (10.5, -7.5, 5.2); d = Vector((0, 0, 1.4)) - cam.location; cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 40; scn.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scn.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.data.color = (1, .88, .72); sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.35, .55, .9, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .9
    scn.render.engine = "BLENDER_EEVEE"; scn.render.resolution_x, scn.render.resolution_y = 1200, 800
    scn.render.filepath = PNG; bpy.ops.render.render(write_still=True); print("PNG:", PNG)
