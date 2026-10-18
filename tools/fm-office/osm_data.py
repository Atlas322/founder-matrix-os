"""Мини хот = бодит гудамж: OSM (Overpass)-аас гэрийн орчмын барилга, зам, цэцэрлэг, ус, модыг татаж
локал метр координат руу хөрвүүлж, жижиг JSON болгоно. Төв цэг нь ub-map.local.json-оос (vault/_system/fm/ эсвэл энэ хавтасны gitignore хуулбар).

Татсан түүхий өгөгдөл, хөрвүүлсэн JSON хоёул ~/.fmos/fm-office/-д (repo, vault-д биш — гэрийн байршил).
build(center, radius) → {"center", "radius", "buildings":[[h, x0,z0,x1,z1,...]], "roads":[[w, ...]], "areas":{kind:[[...]]}, "trees":[x,z,...]}
"""
import json, math, time, urllib.parse, urllib.request
from pathlib import Path

CACHE = Path.home() / ".fmos" / "fm-office"
OVERPASS = "https://overpass-api.de/api/interpreter"
ROAD_W = {"motorway": 16, "trunk": 14, "primary": 12, "secondary": 10, "tertiary": 8, "residential": 6, "unclassified": 6,
          "living_street": 5, "service": 4, "pedestrian": 4, "footway": 2, "path": 1.6, "cycleway": 2}
AREA = {("leisure", "park"): "park", ("leisure", "garden"): "park", ("landuse", "grass"): "park", ("leisure", "pitch"): "pitch",
        ("landuse", "forest"): "park", ("natural", "wood"): "park", ("natural", "water"): "water", ("waterway", "riverbank"): "water",
        ("leisure", "playground"): "playground", ("amenity", "parking"): "plaza", ("place", "square"): "plaza", ("highway", "pedestrian"): "plaza"}


def query(lat, lon, r):
    a = f"(around:{r},{lat},{lon})"
    return f"""[out:json][timeout:180];
(way["building"]{a};way["highway"]{a};way["leisure"]{a};way["landuse"~"grass|forest"]{a};way["natural"~"water|wood"]{a};
 way["waterway"]{a};relation["natural"="water"]{a};way["amenity"="parking"]{a};node["natural"="tree"]{a};);
out tags geom;"""


def fetch(lat, lon, r):
    req = urllib.request.Request(OVERPASS, data=urllib.parse.urlencode({"data": query(lat, lon, r)}).encode(),
                                 headers={"User-Agent": "fm-office/1.0"})
    with urllib.request.urlopen(req, timeout=240) as resp:
        return json.loads(resp.read())


def height(tags):
    try:
        if "height" in tags:
            return max(3.0, min(250.0, float(str(tags["height"]).split()[0].replace(",", "."))))
        if "building:levels" in tags:
            return max(3.0, min(250.0, float(tags["building:levels"]) * 3.1 + 1.0))
    except ValueError:
        pass
    b = tags.get("building", "yes")
    return {"apartments": 27.0, "commercial": 15.0, "office": 24.0, "house": 6.0, "detached": 6.0, "garage": 3.0,
            "shed": 3.0, "retail": 8.0, "school": 12.0, "hospital": 18.0, "industrial": 10.0}.get(b, 9.0)


def to_local(raw, lat, lon):
    kx, kz = 111320 * math.cos(math.radians(lat)), 110540
    P = lambda g: [v for p in g for v in (round((p["lon"] - lon) * kx, 1), round(-(p["lat"] - lat) * kz, 1))]
    out = {"center": [lat, lon], "buildings": [], "roads": [], "areas": {}, "trees": [], "rivers": []}
    for e in raw.get("elements", []):
        t = e.get("tags", {})
        if e["type"] == "node":
            out["trees"] += [round((e["lon"] - lon) * kx, 1), round(-(e["lat"] - lat) * kz, 1)]
            continue
        g = e.get("geometry")
        if not g:
            continue
        if "building" in t:
            out["buildings"].append([round(height(t), 1)] + P(g))
        elif t.get("highway") in ROAD_W and t.get("area") != "yes":
            out["roads"].append([ROAD_W[t["highway"]]] + P(g))
        elif t.get("waterway") in ("river", "stream", "canal"):
            out["rivers"].append([30 if t["waterway"] == "river" else 4] + P(g))
        else:
            for (k, v), kind in AREA.items():
                if t.get(k) == v and len(g) > 2:
                    out["areas"].setdefault(kind, []).append(P(g))
                    break
    return out


def build(center, radius=5000, max_age_days=30):
    """Cache-тай: ~/.fmos/fm-office/osm-<r>.json. 30 хоногоос хуучин бол дахин татна."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"osm-{int(radius)}.json"
    if f.exists() and time.time() - f.stat().st_mtime < max_age_days * 86400:
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("center") == [center[1], center[0]] or d.get("src") == list(center):
            return d
    lon, lat = center
    d = to_local(fetch(lat, lon, radius), lat, lon)
    d["radius"], d["src"] = radius, list(center)
    f.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
    return d


if __name__ == "__main__":
    import sys
    loc = json.loads((Path(__file__).parent / "ub-map.local.json").read_text(encoding="utf-8"))
    d = build(loc["office"], int(sys.argv[1]) if len(sys.argv) > 1 else 5000)
    print({k: len(v) if isinstance(v, list) else {a: len(b) for a, b in v.items()} if isinstance(v, dict) else v for k, v in d.items()})
