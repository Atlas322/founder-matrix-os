"""world.py-ийн төгсгөлд exec хийгдэнэ: «нүд алдам» look + live Weather удирдлага.

Weather (Outliner → «☀ Weather» empty → Object Properties → Custom Properties):
  time   0–24   цаг (нар, тэнгэр, гэрлийн өнгө)       clouds 0–1  үүлний нягт
  fog    0–1    агаарын манан (aerial perspective)    wind   0–1  усны долгион, гялбаа
Бүгд driver (simple expression) — Python auto-run шаардахгүй, slider хөдөлгөхөд viewport шууд өөрчлөгдөнө.
"""
import bpy, math
from mathutils import Vector

scn = bpy.context.scene
NT = lambda m: m.node_tree


def hexc(h, a=1):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c] + [a]


# ── Weather controller ──
W = bpy.data.objects.new("☀ Weather", None); scn.collection.objects.link(W); W.empty_display_type = "SPHERE"; W.location = (-34, -2, 30)
for k, v, lo, hi, d in (("time", 15.5, 0, 24, "цаг (0–24)"), ("clouds", .55, 0, 1, "үүл"), ("fog", .12, 0, 1, "манан"), ("wind", .4, 0, 1, "салхи")):
    W[k] = v
    ui = W.id_properties_ui(k); ui.update(min=lo, max=hi, soft_min=lo, soft_max=hi, description=d)


def drive(target, path, expr, idx=-1, vars=("time",)):
    fc = target.driver_add(path, idx) if idx >= 0 else target.driver_add(path)
    dr = fc.driver; dr.type = "SCRIPTED"; dr.expression = expr
    for name in vars:
        v = dr.variables.new(); v.name = name[0] if name != "clouds" else "c"; v.type = "SINGLE_PROP"
        v.targets[0].id = W; v.targets[0].data_path = f'["{name}"]'
    return fc


ELEV = "max(-0.2, 1.1*sin((t-6)*0.2618))"                                     # нарны өндөр (рад): 6ц мандана, 12ц оргил, 18ц шингэнэ

# ── Нар ──
sun = scn.objects["Sun"]; sun.data.angle = math.radians(1.2)
drive(sun, "rotation_euler", f"1.5708 - {ELEV}", 0)
drive(sun, "rotation_euler", "-2.6 + (t-12)*0.12", 2)                          # баруун уулын ард шингэнэ
drive(sun.data, "energy", f"max(0.0, 5.0*sin((t-6)*0.2618)) + 0.15")
drive(sun.data, "color", "1.0", 0)
drive(sun.data, "color", f"0.62 + 0.33*min(1, max(0, {ELEV})/0.6)", 1)        # бага өндөрт улбар
drive(sun.data, "color", f"0.40 + 0.52*min(1, max(0, {ELEV})/0.6)", 2)

# ── Тэнгэр (физик) + агаарын манан ──
w = scn.world; nt = w.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground"); sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING"
for attr, val in (("sun_disc", True), ("air_density", 1.0), ("dust_density", 1.6), ("ozone_density", 1.0)):
    if hasattr(sky, attr): setattr(sky, attr, val)
nt.links.new(sky.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs["Surface"])
bg.inputs[1].default_value = .32
if hasattr(sky, "sun_elevation"): drive(sky, "sun_elevation", ELEV)
if hasattr(sky, "sun_rotation"): drive(sky, "sun_rotation", "1.2 + (t-12)*0.12")
# манан: хязгааргүй world volume нь EEVEE-д нарыг шингээдэг тул нуурын дээгүүр 0–70 м өндөр хязгаартай хайрцаг
bpy.ops.mesh.primitive_cube_add(size=1, location=(40, 0, 32)); haze = bpy.context.active_object; haze.name = "Haze"; haze.scale = (520, 520, 70)
haze.visible_shadow = False
hm = bpy.data.materials.new("haze"); hm.use_nodes = True; hn = NT(hm).nodes; hn.remove(hn["Principled BSDF"])
vol = hn.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = hexc("#C9DCF0")
NT(hm).links.new(vol.outputs[0], hn["Material Output"].inputs["Volume"]); haze.data.materials.append(hm)
drive(vol.inputs["Density"], "default_value", "f*0.004", vars=("fog",))

# ── Газар: налуу/өндрөөр хад-ногоо-цас, хайрган эрэг, өнгөний noise ──
ter = scn.objects["Terrain"]
m = bpy.data.materials.new("terrain_look"); m.use_nodes = True; n = NT(m).nodes; L = NT(m).links
bs = n["Principled BSDF"]; bs.inputs["Roughness"].default_value = .95
geo = n.new("ShaderNodeNewGeometry"); sep = n.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
nz = n.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], nz.inputs[0])
noi = n.new("ShaderNodeTexNoise"); noi.inputs["Scale"].default_value = .05; noi.inputs["Detail"].default_value = 6
def ramp(stops):
    r = n.new("ShaderNodeValToRGB"); el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], hexc(stops[0][1]); el[1].position, el[1].color = stops[-1][0], hexc(stops[-1][1])
    for pos, c in stops[1:-1]:
        e = el.new(pos); e.color = hexc(c)
    return r
grass = ramp([(0, "#4F7337"), (.5, "#6E9145"), (1, "#9DAF55")]); L.new(noi.outputs["Fac"], grass.inputs[0])
rock = ramp([(0, "#5E5A57"), (.6, "#7F7A73"), (1, "#A39B8E")]); L.new(noi.outputs["Fac"], rock.inputs[0])
# налуу: normal.z бага = хад
slope = n.new("ShaderNodeMapRange"); slope.inputs[1].default_value, slope.inputs[2].default_value = .42, .62   # зөвхөн эгц хад нь саарал, бэл нь ногоон; L.new(nz.outputs["Z"], slope.inputs[0])
mix1 = n.new("ShaderNodeMix"); mix1.data_type = "RGBA"; L.new(slope.outputs[0], mix1.inputs["Factor"]); L.new(rock.outputs[0], mix1.inputs[6]); L.new(grass.outputs[0], mix1.inputs[7])
# өндөр: 38м-ээс дээш хад, 80м-ээс дээш цас
hi = n.new("ShaderNodeMapRange"); hi.inputs[1].default_value, hi.inputs[2].default_value = 34, 46; L.new(sep.outputs["Z"], hi.inputs[0])
mix2 = n.new("ShaderNodeMix"); mix2.data_type = "RGBA"; L.new(hi.outputs[0], mix2.inputs["Factor"]); L.new(mix1.outputs[2], mix2.inputs[6]); L.new(rock.outputs[0], mix2.inputs[7])
sn = n.new("ShaderNodeMapRange"); sn.inputs[1].default_value, sn.inputs[2].default_value = 78, 92; L.new(sep.outputs["Z"], sn.inputs[0])
mix3 = n.new("ShaderNodeMix"); mix3.data_type = "RGBA"; L.new(sn.outputs[0], mix3.inputs["Factor"]); L.new(mix2.outputs[2], mix3.inputs[6]); mix3.inputs[7].default_value = hexc("#EEF2F6")
# эрэг: z < 1.6 бол хайрга (ус доор ч гэсэн ёроол)
pb = n.new("ShaderNodeMapRange"); pb.inputs[1].default_value, pb.inputs[2].default_value = 1.0, 2.2; L.new(sep.outputs["Z"], pb.inputs[0])
vor = n.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.4
peb = ramp([(0, "#7D776E"), (1, "#B4ADA2")]); L.new(vor.outputs["Distance"], peb.inputs[0])
mix4 = n.new("ShaderNodeMix"); mix4.data_type = "RGBA"; L.new(pb.outputs[0], mix4.inputs["Factor"]); L.new(peb.outputs[0], mix4.inputs[6]); L.new(mix3.outputs[2], mix4.inputs[7])
L.new(mix4.outputs[2], bs.inputs["Base Color"])
ter.data.materials.clear(); ter.data.materials.append(m)
for p in ter.data.polygons: p.material_index = 0; p.use_smooth = True
sub = ter.modifiers.new("smooth", "SUBSURF"); sub.levels = sub.render_levels = 1

# ── Ус: тунгалаг (ёроол харагдана), салхиар долгион, гялбаа ──
wm = bpy.data.materials.new("water_look"); wm.use_nodes = True; n = NT(wm).nodes; L = NT(wm).links
b = n["Principled BSDF"]; b.inputs["Base Color"].default_value = hexc("#1E8FA8"); b.inputs["Roughness"].default_value = .03
b.inputs["Alpha"].default_value = .62; b.inputs["IOR"].default_value = 1.33
if "Specular IOR Level" in b.inputs: b.inputs["Specular IOR Level"].default_value = .9
wn = n.new("ShaderNodeTexNoise"); wn.inputs["Scale"].default_value = 1.6; wn.inputs["Detail"].default_value = 8
bump = n.new("ShaderNodeBump"); L.new(wn.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs["Normal"], b.inputs["Normal"])
drive(bump.inputs["Strength"], "default_value", "0.04 + w*0.35", vars=("wind",))
wm.surface_render_method = "BLENDED" if hasattr(wm, "surface_render_method") else None
water = scn.objects["Water"]; water.data.materials.clear(); water.data.materials.append(wm)
deep = scn.objects["LakeDeep"]; deep.data.materials[0] = bpy.data.materials.get("deep")
dm = deep.data.materials[0]; dm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = hexc("#0B3A86")

# ── Үүл: зөөлөн (smooth) cumulus бөмбөлөг — «clouds» slider нь ил тод байдлыг удирдана ──
for o in [o for o in scn.objects if o.name.startswith("Cloud")]: bpy.data.objects.remove(o)
cm = bpy.data.materials.new("cloud_soft"); cm.use_nodes = True; cb = NT(cm).nodes["Principled BSDF"]
cb.inputs["Base Color"].default_value = (1, 1, 1, 1); cb.inputs["Roughness"].default_value = 1
cb.inputs["Emission Color"].default_value = hexc("#FFF4E6"); cb.inputs["Emission Strength"].default_value = .35
if "Subsurface Weight" in cb.inputs: cb.inputs["Subsurface Weight"].default_value = .3
drive(cb.inputs["Alpha"], "default_value", "min(1, c*1.4)", vars=("clouds",))
if hasattr(cm, "surface_render_method"): cm.surface_render_method = "BLENDED"
SK = bpy.data.collections["Sky"]
import random; r2 = random.Random(3)
for i in range(10):
    cx, cy, cz = r2.uniform(-40, 240), r2.uniform(-180, 180), r2.uniform(125, 160)
    for j in range(7):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=r2.uniform(9, 17),
                                             location=(cx + r2.uniform(-22, 22), cy + r2.uniform(-10, 10), cz + r2.uniform(-3, 7) + (6 if j < 3 else 0)))
        c = bpy.context.active_object; c.name = "Cloud"; c.scale.z = .62
        bpy.ops.object.shade_smooth()
        for cc in c.users_collection: cc.objects.unlink(c)
        SK.objects.link(c); c.data.materials.append(cm); c.visible_shadow = False

# ── Алтан цаас: илүү гэрэлтэнэ (glare-д) ──
g = bpy.data.materials.get("gold")
if g: g.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 14

# ── Render: EEVEE ray tracing, volumetric, зөөлөн сүүдэр ──
ee = scn.eevee
for attr, val in (("use_raytracing", True), ("use_shadows", True), ("use_volumetric_shadows", True), ("volumetric_samples", 64),
                  ("volumetric_end", 900.0), ("use_fast_gi", True), ("shadow_ray_count", 2), ("taa_render_samples", 64)):
    if hasattr(ee, attr): setattr(ee, attr, val)
for vt in ("AgX", "Filmic", "Standard"):
    try: scn.view_settings.view_transform = vt; break
    except Exception: pass
try: scn.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
scn.view_settings.exposure = -.6

# ── Compositor: glare (алтан цаас, нар), бага зэрэг vignette ──
try:
    tree = bpy.data.node_groups.new("Khuvsgul Look", "CompositorNodeTree"); scn.compositing_node_group = tree
    ci = tree.nodes.new("CompositorNodeRLayers"); go = tree.nodes.new("NodeGroupOutput")
    tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    gl = tree.nodes.new("CompositorNodeGlare")
    for name, val in (("Type", "Bloom"), ("Type", "BLOOM"), ("Quality", "High"), ("Threshold", 1.5), ("Strength", .6), ("Size", .6)):
        try: gl.inputs[name].default_value = val
        except Exception: pass
    tree.links.new(ci.outputs["Image"], gl.inputs[0]); tree.links.new(gl.outputs[0], go.inputs[0])
except Exception as e:
    print("compositor алгасав:", e)
print("LOOK: ok")
