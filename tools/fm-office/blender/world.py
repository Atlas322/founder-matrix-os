"""Хөвсгөлийн ертөнц — greybox (байршил, хэмжээ, өнгөний эхний шат). world-map.png концептыг даган.

Ажиллуулах:  blender -b -P blender/world.py -- <out.blend> [preview.png]
Нээх:        Blender → File → Open → out.blend  (камер «MapCam» = газрын зураг, «HomeCam» = гэрийн ойр)
Нэгж: 1 = 1 м. Эрэг баруун тийш нуур руу. Collection: Terrain · Lake · Home · WishRock · Sky · Cameras
"""
import bpy, bmesh, math, random, sys
from mathutils import Vector, noise

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "khuvsgul_world.blend"
PNG = argv[1] if len(argv) > 1 else None
rnd = random.Random(11)
bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene


def coll(name):
    c = bpy.data.collections.new(name); scn.collection.children.link(c); return c


def mat(name, hexc, emit=0.0, rough=.85, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c] + [1]
    b.inputs["Base Color"].default_value = c; b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = c; b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def obj(name, me, c, m=None):
    o = bpy.data.objects.new(name, me); c.objects.link(o)
    if m: o.data.materials.append(m)
    return o


def prim(fn, c, m, name, **kw):
    fn(**kw); o = bpy.context.active_object; o.name = name
    for cc in o.users_collection: cc.objects.unlink(o)
    c.objects.link(o)
    if m: o.data.materials.clear(); o.data.materials.append(m)
    return o


M = dict(grass=mat("grass", "#6E8F45"), larch=mat("larch", "#9DAF45"), pine=mat("pine", "#2F4A35"),
         pebble=mat("pebble", "#9C968A"), rock=mat("rock", "#6F6C68"), shallow=mat("shallow", "#2FB7C2", rough=.05, alpha=.75),
         deep=mat("deep", "#123E8C", rough=.08), felt=mat("felt", "#F1ECE2"), red=mat("red", "#C8432F"),
         wood=mat("wood", "#7A4E33"), roof=mat("roof", "#3A3D47"), gold=mat("gold", "#FFC45A", emit=6), khadag=mat("khadag", "#3D7BE0"),
         cloud=mat("cloud", "#FFFFFF", rough=1), orange=mat("orange", "#E86A2A"), snow=mat("snow", "#E8EEF5"))

# ── Газар: зүүн тал хуурай (x<0), баруун тийш нуурын ёроол руу налж орно ──
T = coll("Terrain")
bm = bmesh.new(); N, S = 140, 3.0
vs = [[bm.verts.new((x * S - 240, y * S - 210, 0)) for x in range(N + 1)] for y in range(N + 1)]
for row in vs:
    for v in row:
        x, y = v.co.x, v.co.y
        shore = -20 + 12 * math.sin(y * .02) + 6 * math.sin(y * .07)          # эргийн шугам
        shore += 22 * math.exp(-(y / 16) ** 2) - 12 * math.exp(-((y + 36) / 11) ** 2)   # Тойлогтын хойг + өмнөд нам гүм булан
        d = x - shore
        h = (-min(d, 60) * .12 if d > 0 else (-d) * .08) + noise.noise(Vector((x * .02, y * .02, 0))) * 3
        if x < -95:                                                             # Хорьдол Сарьдагийн эгц бэл: хяр, жалга
            k = min(1, (-95 - x) / 40)
            ridge = 1 - abs(noise.noise(Vector((x * .018, y * .03, 1.3))))
            h += min(95, ((-95 - x) * .85) ** 1.18) * (.55 + .45 * ridge) + ridge ** 3 * 22 * k
        hd = math.hypot(x + 34, y + 2)                                          # гэр бүс: тэгш, хуурай тавцан
        if hd < 30: h = h + (1.6 - h) * min(1, (30 - hd) / 10)
        if math.hypot(x - 70, y + 10) < 10: h = 6 - math.hypot(x - 70, y + 10) * .55   # хүслийн хад
        v.co.z = h
for y in range(N):
    for x in range(N):
        bm.faces.new((vs[y][x], vs[y][x + 1], vs[y + 1][x + 1], vs[y + 1][x]))
me = bpy.data.meshes.new("terrain"); bm.to_mesh(me); bm.free()
ter = obj("Terrain", me, T, M["grass"]); ter.data.materials.append(M["pebble"]); ter.data.materials.append(M["rock"])
for p in ter.data.polygons:                                                     # эрэг = хайрга, ус доор = чулуу
    z = p.center.z
    p.material_index = 2 if z > 38 else (0 if z > 1.2 else (1 if z > -3 else 2))   # дээд хэсэг нүцгэн хад

# ── Нуур: гүехэн (turquoise) + гүн (cobalt) хоёр давхар ──
L = coll("Lake")
prim(bpy.ops.mesh.primitive_plane_add, L, M["shallow"], "Water", size=400, location=(0, 0, .2))
prim(bpy.ops.mesh.primitive_plane_add, L, M["deep"], "LakeDeep", size=400, location=(140, 0, -4))

# ── Мод: нарс (конус), шинэс (алтан конус) ──
for i in range(520):
    x, y = rnd.uniform(-200, -40), rnd.uniform(-190, 190)
    z = ter.ray_cast(Vector((x, y, 200)), Vector((0, 0, -1)))[1].z if False else None
    h = rnd.uniform(7, 14); larch = rnd.random() < .55                          # шинэс давамгай
    t = prim(bpy.ops.mesh.primitive_cone_add, T, M["larch" if larch else "pine"], "Tree", vertices=7, radius1=h * .22, depth=h,
             location=(x, y, 0))
    t["needs_ground"] = 1
    for k, (sr, sz) in enumerate(((.8, .28), (.6, .52))):                       # давхар мөчир (шатлалтай)
        u = prim(bpy.ops.mesh.primitive_cone_add, T, M["larch" if larch else "pine"], "Tree", vertices=7, radius1=h * .22 * sr, depth=h * .55,
                 location=(x, y, 0)); u["needs_ground"] = 1; u["lift"] = h * sz

# ── Гэр бүс ──
Hh = coll("Home")
def ger(x, y, r=3.5, name="Ger"):
    w = prim(bpy.ops.mesh.primitive_cylinder_add, Hh, M["felt"], name, vertices=24, radius=r, depth=2.2, location=(x, y, GZ + 1.1))
    prim(bpy.ops.mesh.primitive_cone_add, Hh, M["felt"], name + "_roof", vertices=24, radius1=r + .2, radius2=.6, depth=1.4, location=(x, y, GZ + 2.9))
    prim(bpy.ops.mesh.primitive_cube_add, Hh, M["red"], name + "_door", size=1, location=(x + r - .05, y, GZ + .9), scale=(.15, .8, 1.7))
    return w
def cabin(x, y, name):
    prim(bpy.ops.mesh.primitive_cube_add, Hh, M["wood"], name, size=1, location=(x, y, GZ + 1.5), scale=(6, 4.5, 3))
    r = prim(bpy.ops.mesh.primitive_cone_add, Hh, M["roof"], name + "_roof", vertices=4, radius1=4.6, depth=2.2, location=(x, y, GZ + 4.1))
    r.rotation_euler.z = math.pi / 4; r.scale = (1.3, 1, 1); r.data.materials.clear(); r.data.materials.append(M["red"])   # Тойлогтын лодж шиг улаан дээвэр
HOME = (-34, -2)
GZ = 1.6                                                                        # гэр бүсийн газрын өндөр
ger(HOME[0], HOME[1], 4, "Ger_MyRoom")
cabin(-46, 12, "Cabin_Projects"); cabin(-48, -16, "Cabin_Library")
for i in range(5):                                                              # задгай номын сан
    prim(bpy.ops.mesh.primitive_cube_add, Hh, M["wood"], "OpenLibrary", size=1, location=(-30 + i * 1.6, 16, GZ + 1.2), scale=(1.2, .45, 2.4))
prim(bpy.ops.mesh.primitive_cylinder_add, Hh, M["orange"], "Campfire", vertices=8, radius=.6, depth=.4, location=(-24, 6, GZ + .2))
prim(bpy.ops.mesh.primitive_cube_add, Hh, M["wood"], "Pier", size=1, location=(-6, -14, .6), scale=(14, 2.2, .3))
k = prim(bpy.ops.mesh.primitive_uv_sphere_add, Hh, M["orange"], "Kayak", segments=12, ring_count=6, radius=1, location=(-4, -18, .5)); k.scale = (2.4, .4, .25)

# ── Кэмпийн талбай: сийрэг хазайсан шинэс, морь бэлчих хашаа, булангийн зэгс ──
for i in range(14):
    a, rr = rnd.random() * math.tau, rnd.uniform(9, 21)
    x, y = HOME[0] + math.cos(a) * rr, HOME[1] + math.sin(a) * rr
    if math.hypot(x + 40, y - 12) < 6 or math.hypot(x + 48, y + 16) < 6: continue
    h = rnd.uniform(6, 10)
    t = prim(bpy.ops.mesh.primitive_cone_add, Hh, M["larch"], "LoneLarch", vertices=6, radius1=h * .16, depth=h, location=(x, y, GZ + h / 2))
    t.rotation_euler = (rnd.uniform(-.12, .12), rnd.uniform(.05, .18), 0)          # салхинд нэг тал руу хазайна
for k in range(14):                                                             # хашаа (кэмпээс хойд тал)
    prim(bpy.ops.mesh.primitive_cylinder_add, Hh, M["wood"], "Fence", vertices=5, radius=.08, depth=1.3, location=(-58 + k * 2.4, 34, GZ + .65))
prim(bpy.ops.mesh.primitive_cube_add, Hh, M["wood"], "FenceRail", size=1, location=(-42.4, 34, GZ + 1.0), scale=(31, .06, .08))
HORSE = mat("horse", "#6B4330"); HORSE2 = mat("horse_light", "#C9B8A0")
for i, (x, y, rz) in enumerate(((-50, 42, .4), (-44, 46, 2.2), (-38, 40, -.6), (-54, 48, 1.2))):
    m = HORSE if i % 2 == 0 else HORSE2
    body = prim(bpy.ops.mesh.primitive_cube_add, Hh, m, "Horse", size=1, location=(x, y, GZ + 1.35), scale=(1.9, .55, .7)); body.rotation_euler.z = rz
    for dx in (-.7, .7):
        for dy in (-.18, .18):
            o = Vector((dx, dy, 0)); o.rotate(body.rotation_euler)
            prim(bpy.ops.mesh.primitive_cube_add, Hh, m, "HorseLeg", size=1, location=(x + o.x, y + o.y, GZ + .5), scale=(.14, .14, 1.0))
    o = Vector((1.15, 0, 0)); o.rotate(body.rotation_euler)
    nk = prim(bpy.ops.mesh.primitive_cube_add, Hh, m, "HorseHead", size=1, location=(x + o.x, y + o.y, GZ + 1.25), scale=(.7, .3, .32))
    nk.rotation_euler = (0, .9, rz)                                                # толгой доош — бэлчиж байна
for i in range(120):                                                            # зэгс: өмнөд булангийн гүехэн усанд
    x, y = rnd.uniform(-34, -14), rnd.uniform(-46, -26)
    prim(bpy.ops.mesh.primitive_cone_add, L, M["larch"], "Reed", vertices=3, radius1=.06, depth=rnd.uniform(1.2, 2.2), location=(x, y, .7))

# ── Хүслийн хад ──
W = coll("WishRock")
for i in range(14):
    a = rnd.random() * math.tau
    prim(bpy.ops.mesh.primitive_cylinder_add, W, M["khadag"], "Khadag", vertices=4, radius=.12, depth=2.5,
         location=(70 + math.cos(a) * 3, -10 + math.sin(a) * 3, 3.5 + rnd.random()))
prim(bpy.ops.mesh.primitive_cone_add, W, M["pine"], "WishTree", vertices=7, radius1=1.6, depth=6, location=(70, -10, 9))

# ── Тэнгэр: алтан спираль (Фибоначчи) + үүл + хөвөгч арал ──
SK = coll("Sky")
phi = (1 + 5 ** .5) / 2
# алтан спираль: тэнхлэгээ тойрон эргэж, дээшлэх тусам phi-ээр өргөснө (nautilus дээш босгосон мэт)
for i in range(320):
    t = i / 319
    ang = t * 4 * math.pi
    r = 1.5 * phi ** (ang / (math.pi / 2)) * .45                                   # 1.5 м → ~30 м
    p = Vector((HOME[0] + 6 + math.cos(ang) * r, HOME[1] + math.sin(ang) * r, 6 + t * 110))
    p += Vector((rnd.uniform(-.6, .6), rnd.uniform(-.6, .6), rnd.uniform(-.8, .8)))
    n = prim(bpy.ops.mesh.primitive_plane_add, SK, M["gold"], "Note", size=.6 + t * .9, location=p)
    n.rotation_euler = (rnd.random(), rnd.random(), rnd.random())
for i in range(9):
    c = (rnd.uniform(-40, 220), rnd.uniform(-160, 160), rnd.uniform(130, 170))
    for j in range(6):
        prim(bpy.ops.mesh.primitive_ico_sphere_add, SK, M["cloud"], "Cloud", subdivisions=2,
             radius=rnd.uniform(8, 16), location=(c[0] + rnd.uniform(-14, 14), c[1] + rnd.uniform(-8, 8), c[2] + rnd.uniform(-4, 6)))
        bpy.context.active_object.visible_shadow = False                         # нуурыг сүүдрээр бүү халх
for (x, y, z) in ((-5, 50, 100), (45, 35, 85)):
    prim(bpy.ops.mesh.primitive_cone_add, SK, M["rock"], "FloatIsland", vertices=8, radius1=7, depth=9, location=(x, y, z), rotation=(math.pi, 0, 0))
    prim(bpy.ops.mesh.primitive_cylinder_add, SK, M["grass"], "FloatIsland_top", vertices=8, radius=7, depth=.8, location=(x, y, z + 4.8))
for i in range(5):                                                              # холын цаст уулс
    prim(bpy.ops.mesh.primitive_cone_add, T, M["snow"], "Mountain", vertices=6, radius1=60, depth=rnd.uniform(40, 70),
         location=(200 + rnd.uniform(0, 40), -150 + i * 75, 10))

# модыг газарт буулгах
deps = bpy.context.evaluated_depsgraph_get()
for o in list(scn.objects):
    if o.get("needs_ground"):
        hit, loc, *_ = ter.ray_cast(Vector((o.location.x, o.location.y, 300)), Vector((0, 0, -1)))
        if hit:
            o.location.z = loc.z + o.dimensions.z / 2 + o.get("lift", 0)
            if loc.z < 1.2 or loc.z > 38 or math.hypot(loc.x + 34, loc.y + 2) < 22: bpy.data.objects.remove(o)   # ус, хадан орой, кэмпийн талбайд модгүй

# ── Гэрэл, тэнгэр, камер ──
CA = coll("Cameras")
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); CA.objects.link(sun)
sun.data.energy = 4; sun.data.color = (1, .9, .75); sun.rotation_euler = (math.radians(45), math.radians(10), math.radians(-120))
w = bpy.data.worlds.new("Sky"); scn.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (.25, .5, .95, 1); w.node_tree.nodes["Background"].inputs[1].default_value = .8
def cam(name, loc, look, lens=35):
    c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); CA.objects.link(c); c.location = loc; c.data.lens = lens
    d = Vector(look) - Vector(loc); c.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler(); c.data.clip_end = 2000; return c
mapcam = cam("MapCam", (40, -120, 75), (-40, 5, 15), 26)   # нуураас эрэг, уул руу харсан
cam("HomeCam", (-12, -24, 8), HOME + (3,), 28)
scn.camera = mapcam

exec(open(__file__.replace('world.py', 'look.py'), encoding='utf-8').read())
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print("BLEND:", OUT)
if PNG:
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x, scn.render.resolution_y = 1600, 900
    for c in ("MapCam", "HomeCam"):
        scn.camera = scn.objects[c]; scn.render.filepath = PNG.replace(".png", f"_{c}.png")
        bpy.ops.render.render(write_still=True); print("PNG:", scn.render.filepath)
    scn.camera = mapcam
