"""Хөвсгөлийн ертөнцийн hero asset-ууд: дүнзэн байшин · хүслийн хад · алтан спираль.

Ажиллуулах:  blender -b -P blender/heroes.py -- <cabin|wishrock|spiral> <out.glb> [preview.png]
Хэв маяг: charter — бодит + нэг ид шид. Low-poly, flat shading, палитр: мод #7A4E33, шифер #3A3D47, хад #6F6C68, хадаг #3D7BE0, алт #FFC45A.
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:]
KIND, OUT = argv[0], argv[1]
PNG = argv[2] if len(argv) > 2 else None
rnd = random.Random(5)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene
parts = []


def mat(name, h, rough=.9, emit=0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]; c = [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c] + [1]
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = c; b.inputs["Emission Strength"].default_value = emit
    return m


def keep(o, m=None):
    if m: o.data.materials.clear(); o.data.materials.append(m)
    parts.append(o); return o


def box(m, loc, size, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.active_object; o.scale = size; return keep(o, m)


def cyl(m, loc, r, d, rot=(0, 0, 0), v=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc, rotation=rot); return keep(bpy.context.active_object, m)


# ── Дүнзэн байшин: 6×4.5 м, дүнз давхарлаж, булангаар нь цухуйлгана ──
def cabin():
    LOG, LOG2, ROOF = mat("log", "#7A4E33"), mat("log_dark", "#5E3B27"), mat("roof", "#3A3D47")
    WIN, FRAME, DOOR, STONE = mat("window", "#FFC27A", .5, 3), mat("frame", "#F0E6D2"), mat("door", "#C8432F"), mat("stone", "#8C867A")
    W, D, LR, H = 6.0, 4.5, .17, 12
    for k in range(H):
        z = .25 + LR + k * LR * 1.9
        m = LOG if k % 2 else LOG2
        for y in (-D / 2, D / 2):                                              # урд/ар хана (X тэнхлэгийн дагуу)
            cyl(m, (0, y, z + (LR * .95 if k % 2 else 0)), LR, W + .7, rot=(0, math.pi / 2, 0))
        for x in (-W / 2, W / 2):                                              # хажуу (Y тэнхлэгийн дагуу)
            cyl(m, (x, 0, z + (0 if k % 2 else LR * .95)), LR, D + .7, rot=(math.pi / 2, 0, 0))
    top = .25 + LR + H * LR * 1.9
    # налуу дээвэр (хоёр хавтан) + гурвалжин нүүр
    pitch, ov = math.radians(32), .6
    half = (D / 2 + ov) / math.cos(pitch)
    for s in (-1, 1):
        box(ROOF, (0, s * (D / 4 + ov / 2), top + math.tan(pitch) * (D / 4 + ov / 2) - .05), (W + 1.2, half, .14), rot=(s * -pitch, 0, 0))
    gh = math.tan(pitch) * D / 2
    for x in (-W / 2, W / 2):
        bm = bmesh.new(); vs = [bm.verts.new(p) for p in ((x, -D / 2, top), (x, D / 2, top), (x, 0, top + gh))]
        bm.faces.new(vs); me = bpy.data.meshes.new("gable"); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("gable", me); scn.collection.objects.link(o); keep(o, LOG2)
    box(LOG2, (0, 0, top + gh + .05), (W + 1.3, .25, .2))                       # нуруу
    # хаалга (урд, -Y), цонх 2, яндан, үүдний шат
    box(FRAME, (1.2, -D / 2 - .2, 1.2), (1.15, .1, 2.0)); box(DOOR, (1.2, -D / 2 - .26, 1.15), (.95, .06, 1.85))
    for x in (-1.4,):
        box(FRAME, (x, -D / 2 - .2, 1.6), (1.3, .1, 1.0)); box(WIN, (x, -D / 2 - .24, 1.6), (1.1, .04, .8))
        box(FRAME, (x, -D / 2 - .26, 1.6), (.06, .06, .8)); box(FRAME, (x, -D / 2 - .26, 1.6), (1.1, .06, .06))
    box(FRAME, (W / 2 + .2, 0, 1.6), (.1, 1.3, 1.0)); box(WIN, (W / 2 + .24, 0, 1.6), (.04, 1.1, .8))
    box(STONE, (-W / 2 + .9, D / 4, top + gh * .5 + .9), (.7, .7, 2.6))
    box(STONE, (0, 0, .12), (W + .9, D + .9, .25))
    for i in range(3):
        box(LOG2, (1.2, -D / 2 - .6 - i * .35, .08 + (2 - i) * .1), (1.6, .35, .16))


# ── Хүслийн хад: нуурын дундах арал, хадаг уясан хад, ганц мод, жижиг овоо ──
def wishrock():
    ROCK, ROCK2, MOSS, PINE, BARK = mat("rock", "#6F6C68"), mat("rock_light", "#8E8A84"), mat("moss", "#5F7F3E"), mat("pine", "#2F4A35"), mat("bark", "#4A2C1E")
    BLUE, BLUE2, WHITE = mat("khadag", "#3D7BE0"), mat("khadag_light", "#7FB2F0"), mat("khadag_white", "#F2EEE6")
    # хад: icosphere-ийг noise-оор эвдэж, доод хэсгийг усанд оруулна
    for (x, y, r, h, m) in ((0, 0, 4.2, 6.5, ROCK), (2.6, 1.8, 2.4, 3.2, ROCK2), (-2.8, 1.2, 2.0, 2.4, ROCK), (1.2, -2.8, 1.6, 1.8, ROCK2)):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, h * .35))
        o = bpy.context.active_object; o.scale.z = h / (2 * r)
        for v in o.data.vertices:
            n = noise.noise(v.co * .9 + Vector((x, y, 0))) * .45
            v.co += v.co.normalized() * n
        keep(o, m)
    bpy.ops.mesh.primitive_cylinder_add(vertices=14, radius=5.6, depth=.5, location=(0, 0, .05)); keep(bpy.context.active_object, MOSS)
    # мод: хазайсан их бие, давхар навч
    top = Vector((0, 0, 4.4))
    cyl(BARK, (top.x + .2, top.y, top.z + 1.4), .18, 3.2, rot=(0, .18, 0), v=6)
    for k, (r, z) in enumerate(((1.9, 3.4), (1.5, 4.3), (1.0, 5.1), (.55, 5.8))):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=r, depth=1.2, location=(top.x + .5 + k * .05, top.y, top.z + z - 1.6)); keep(bpy.context.active_object, PINE)
    # овоо: чулуу давхарлаад тулгуур мод
    for k in range(9):
        a = k * 2.4
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.32 - k * .02, location=(-1.6 + math.cos(a) * .3 * (1 - k / 9), 1.4 + math.sin(a) * .3 * (1 - k / 9), 3.3 + k * .18))
        keep(bpy.context.active_object, ROCK2)
    cyl(BARK, (-1.6, 1.4, 4.6), .05, 1.4, v=5)
    # хадаг: хад, модонд уясан туузнууд (бага зэрэг мушгирсан урт хавтгай)
    def ribbon(p0, direction, length, m, w=.22):
        bm = bmesh.new(); prev = None; d = Vector(direction).normalized()
        side = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < .9 else Vector((1, 0, 0))
        for i in range(7):
            t = i / 6
            c = Vector(p0) + d * length * t + Vector((0, 0, -t * t * length * .5)) + side * math.sin(t * 5) * .15
            a, b = bm.verts.new(c - side * w / 2), bm.verts.new(c + side * w / 2)
            if prev: bm.faces.new((prev[0], prev[1], b, a))
            prev = (a, b)
        me = bpy.data.meshes.new("khadag"); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("khadag", me); scn.collection.objects.link(o); keep(o, m)
    for i in range(16):
        a = i / 16 * math.tau
        p0 = (math.cos(a) * 2.8, math.sin(a) * 2.8, 3.0 + rnd.uniform(-.6, .8))
        ribbon(p0, (math.cos(a + .6), math.sin(a + .6), -.2), rnd.uniform(1.2, 2.0), (BLUE, BLUE2, WHITE)[i % 3])
    for i in range(8):
        ribbon((top.x + .4, top.y, top.z + 2 + i * .25), (math.cos(i), math.sin(i), .1), rnd.uniform(.9, 1.4), (BLUE, BLUE2, WHITE)[i % 3], .16)


# ── Алтан спираль: Фибоначчийн тоо (233) цаас + гэрлийн тууз, 60 м өндөр ──
def spiral():
    GOLD, GOLD2, RIB = mat("note", "#FFD27A", .6, 5), mat("note_warm", "#FFB04A", .6, 6), mat("ribbon", "#FFE3A3", .3, 9)
    phi = (1 + 5 ** .5) / 2; N = 233; turns = 4.0
    path = []
    for i in range(N):
        t = i / (N - 1)
        a = t * turns * math.tau
        r = .8 * phi ** (a / (math.pi / 2)) * .2                                # nautilus: дээшлэх тусам phi-ээр өргөснө
        r = min(r, 18)
        p = Vector((math.cos(a) * r, math.sin(a) * r, t * 60))
        path.append(p)
        jitter = Vector((rnd.uniform(-.4, .4), rnd.uniform(-.4, .4), rnd.uniform(-.3, .3))) * (1 + t * 2)
        s = .35 + t * .55
        bpy.ops.mesh.primitive_plane_add(size=1, location=p + jitter)
        o = bpy.context.active_object; o.scale = (s, s * 1.3, 1)
        o.rotation_euler = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), a + math.pi / 2)
        keep(o, GOLD if i % 3 else GOLD2)
    # гэрлийн тууз (хавтгай туузаар замыг дагуулна)
    bm = bmesh.new(); prev = None
    for i in range(0, N, 2):
        p = path[i]; w = .06 + i / N * .2
        a, b = bm.verts.new(p - Vector((0, 0, w))), bm.verts.new(p + Vector((0, 0, w)))
        if prev: bm.faces.new((prev[0], prev[1], b, a))
        prev = (a, b)
    me = bpy.data.meshes.new("ribbon"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("ribbon", me); scn.collection.objects.link(o); keep(o, RIB)


{"cabin": cabin, "wishrock": wishrock, "spiral": spiral}[KIND]()
for o in parts:
    if o.type == "MESH":
        for p in o.data.polygons: p.use_smooth = False
bpy.ops.object.select_all(action="DESELECT")
for o in parts: o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join(); hero = bpy.context.active_object; hero.name = KIND
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True)
print("GLB:", OUT, len(hero.data.polygons), "faces")

if PNG:
    bb = [hero.matrix_world @ Vector(c) for c in hero.bound_box]
    ctr = sum(bb, Vector()) / 8; size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    bpy.ops.mesh.primitive_plane_add(size=size * 8, location=(0, 0, -.05))
    g = bpy.context.active_object; g.data.materials.append(mat("ground", "#2FB7C2" if KIND == "wishrock" else "#6E8F45", .2 if KIND == "wishrock" else .9))
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scn.collection.objects.link(cam)
    cam.location = ctr + Vector((1, -.8, .55)).normalized() * size * 1.9
    cam.rotation_euler = (ctr - cam.location).to_track_quat('-Z', 'Y').to_euler(); cam.data.lens = 40; scn.camera = cam
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scn.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.data.color = (1, .88, .72); sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
    w = bpy.data.worlds.new("w"); scn.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (.25, .45, .85, 1) if KIND == "spiral" else (.35, .55, .9, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = .9
    scn.render.engine = "BLENDER_EEVEE"; scn.render.resolution_x, scn.render.resolution_y = (900, 1200) if KIND == "spiral" else (1200, 800)
    scn.render.filepath = PNG; bpy.ops.render.render(write_still=True); print("PNG:", PNG)
