"""Хотын газрын зургийн байршлууд — vault-аас (PC, Mac ижил уншина; repo-д хаяг бичихгүй).

гэр      : 03-Areas/people/*.md — `is-vault-owner: true` + `home: {"name","place","lng","lat"}`
харилцагч: 03-Areas/Business/*/companies/*.md — `status: active` + `locations: [{"name","project","lng","lat","addr"}]`
           lng/lat-гүй байршил (жишээ нь өөр хот) → unplaced. `status: declined|lost|...` бол огт орохгүй.
Гаралт нь ub-map.local.json-тай ижил хэлбэр: {"office":[lng,lat],"name","clients":[...],"unplaced":[...]}
"""
import json, re
from pathlib import Path


def _fm(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    out = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _json(v):
    try:
        return json.loads(v)
    except (ValueError, TypeError):
        return None


def build(vault):
    v = Path(vault)
    out = {"office": None, "name": "Гэр", "clients": [], "unplaced": []}
    for p in (v / "03-Areas/people").glob("*.md"):
        fm = _fm(p.read_text(encoding="utf-8", errors="ignore")[:4000])
        if fm.get("is-vault-owner") == "true" and (h := _json(fm.get("home"))) and h.get("lng") is not None:
            out["office"], out["name"] = [h["lng"], h["lat"]], h.get("name", "Гэр")
            out["home_place"] = h.get("place", "")
    for p in sorted(v.glob("03-Areas/Business/*/companies/*.md")):
        fm = _fm(p.read_text(encoding="utf-8", errors="ignore")[:6000])
        if fm.get("status", "").strip('"') != "active":
            continue
        for loc in _json(fm.get("locations")) or []:
            item = {"org": p.stem, "status": "active", **loc}
            if loc.get("lng") is not None and loc.get("lat") is not None:
                item["lngLat"] = [loc["lng"], loc["lat"]]
                out["clients"].append(item)
            else:
                out["unplaced"].append({"name": loc.get("name", p.stem), "org": p.stem, "why": loc.get("city") and f"{loc['city']} (Улаанбаатараас гадна)" or "координатгүй"})
    return out
