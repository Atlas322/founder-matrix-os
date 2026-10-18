"""FM Office — vault-ийг 3D оффис болгон localhost дээр харуулна (зөвхөн уншина).

Ажиллуулах:  python server.py [--vault "<vault хавтас>"] [--port 5191]
GET /            → index.html
GET /main.js     → 3D scene
GET /api/state   → floors, rooms, agents, conversations (office_state.py)
"""
import argparse, json, os, re, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from office_state import build_state, load_config  # noqa: E402
import room_info, sender, calendar_data, home_data, hall_data, ref_data, days_data, osm_data, weather_data, map_data  # noqa: E402

STATIC = {"/": ("landing.html", "text/html; charset=utf-8"),           # нүүр хуудас (Second Brain)
          "/office2d": ("office2d.html", "text/html; charset=utf-8"),   # 2.5D зурагт оффис (хуучин үндсэн)
          "/nav.js": ("nav.js", "text/javascript; charset=utf-8"),      # бүх хуудасны нийтийн цэс
          "/diagram.js": ("diagram.js", "text/javascript; charset=utf-8"),  # axonometric диаграмын дизайн систем
          "/office2d.js": ("office2d.js", "text/javascript; charset=utf-8"),
          "/tokens.css": ("tokens.css", "text/css; charset=utf-8"),
          "/calendar": ("calendar.html", "text/html; charset=utf-8"),          # 📅 Цаглабар модуль
          "/calendar.js": ("calendar.js", "text/javascript; charset=utf-8"),
          "/util.js": ("util.js", "text/javascript; charset=utf-8"),
          "/3d": ("index.html", "text/html; charset=utf-8"),             # хуучин Three.js хувилбар
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/main.js": ("main.js", "text/javascript; charset=utf-8"),
          "/campus": ("campus.html", "text/html; charset=utf-8"),            # Оффисын кампус (барилгын түвшин, v02)
          "/home": ("home.html", "text/html; charset=utf-8"),                # Second Brain мини хот (гэр)
          "/xr": ("gallery-xr.html", "text/html; charset=utf-8"),           # Spatial Gallery (WebXR, шил)
          "/hall": ("hall.html", "text/html; charset=utf-8"),
          "/gallery": ("gallery.html", "text/html; charset=utf-8"),         # Gallery: Neuform маягийн bento тор
          "/fpv": ("fpv.html", "text/html; charset=utf-8"),                 # Gallery FPV: хулгана түгжээд алхана
          "/spiral": ("spiral.html", "text/html; charset=utf-8"),           # өдөр бүр = спиралийн блок               # Gallery hall: хавтас, YouTube, highlight → атом
          "/map": ("home.html", "text/html; charset=utf-8"),                 # хот = мини хоттой нэг хөдөлгүүр (Three.js, «Хот» харагдац)
          "/map-old": ("ub-map.html", "text/html; charset=utf-8"),           # хуучин MapLibre хувилбар (globe)
          }
LOCAL_MAP = "ub-map.local.json"   # бодит байршил: vault/_system/fm/ (Drive-аар хоёр машинд) → эсвэл repo-гийн gitignore хуулбар


def local_map(vault):
    """Байршил: vault-ийн note-уудаас (map_data: гэр = people/is-vault-owner `home:`, харилцагч = companies `locations:`); хоосон бол хуучин JSON файл."""
    d = map_data.build(vault)
    if d.get("office"):
        return d
    for f in (Path(vault) / "_system" / "fm" / LOCAL_MAP, HERE / LOCAL_MAP):
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    return None
ASSET_TYPES = {".glb": "model/gltf-binary", ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json; charset=utf-8"}


def _default_vault():
    v = os.environ.get("FM_VAULT") or os.environ.get("FMOS_VAULT")
    if not v:
        cfg = Path(os.environ.get("FMOS_CONFIG", Path.home() / ".fmos" / "config.json"))
        try:
            v = json.loads(cfg.read_text(encoding="utf-8")).get("vault")
        except (OSError, ValueError):
            v = None
    return v


def room_context(vault, room_id):
    st = build_state(vault, discord=False)
    room = next((r for r in st["rooms"] if r["id"] == room_id), None)
    if not room:
        return None, None, None
    ags = [a for a in st["agents"] if a["room"] == room_id]
    cfg = load_config(Path(vault))
    slugs = {a["project"] for a in ags if not a.get("human")} | {k for k, v in (cfg.get("aliases") or {}).items() if v == room["project"]}
    return st, room, (ags, slugs)


def room_payload(vault, room_id):
    st, room, ctx = room_context(vault, room_id)
    if not room:
        return None
    ags, slugs = ctx
    if room["kind"] == "project":
        info = room_info.project_info(vault, room, ags, st["agents"], slugs)
    elif room["kind"] == "workshop":
        info = room_info.workshop_info(vault, room, st["rooms"])
    else:
        info = {"room": room}
    info["send_channels"] = sorted({a["channel"] for a in ags if a.get("channel")} | {"gtd"})
    return info


def make_handler(vault):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *a):
            pass

        def do_GET(self):
            path = self.path.split("?")[0]
            try:
                if path == "/" + LOCAL_MAP:
                    loc = local_map(vault)
                    return self._send(200, loc) if loc else self._send(404, {"error": LOCAL_MAP + " алга"})
                if path in STATIC:
                    f, ct = STATIC[path]
                    return self._send(200, (HERE / f).read_bytes(), ct)
                if path.startswith("/assets/"):
                    f = (HERE / path.lstrip("/")).resolve()
                    if (HERE / "assets").resolve() in f.parents and f.is_file() and f.suffix in ASSET_TYPES:
                        return self._send(200, f.read_bytes(), ASSET_TYPES[f.suffix])
                    return self._send(404, {"error": "not found"})
                if path == "/api/room":
                    from urllib.parse import parse_qs, urlparse
                    rid = (parse_qs(urlparse(self.path).query).get("id") or [""])[0]
                    info = room_payload(vault, rid)
                    return self._send(200 if info else 404, info or {"error": "өрөө алга"})
                if path == "/api/calendar":
                    from urllib.parse import parse_qs, urlparse
                    from datetime import date, timedelta
                    q = parse_qs(urlparse(self.path).query)
                    t0 = date.today()
                    a = (q.get("from") or [str(t0 - timedelta(days=t0.weekday()))])[0][:10]
                    b = (q.get("to") or [str(date.fromisoformat(a) + timedelta(days=6))])[0][:10]
                    st = build_state(vault, discord=False)
                    data = calendar_data.build(vault, st, a, b)
                    data["agents"] = st["agents"]
                    return self._send(200, data)
                if path == "/api/hall":
                    from urllib.parse import parse_qs, urlparse
                    q = parse_qs(urlparse(self.path).query)
                    rel = (q.get("path") or [""])[0]
                    try:
                        if q.get("topics"):                             # Gallery: сэдвийн өрөөнүүд
                            return self._send(200, hall_data.topics(vault))
                        if q.get("topic"):
                            return self._send(200, hall_data.topic_refs(vault, q["topic"][0]))
                        return self._send(200, hall_data.list_dir(vault, rel))
                    except hall_data.HallError as e:
                        return self._send(400, {"error": str(e)})
                if path == "/api/thumb":                                # самбарын thumbnail (same-origin → WebGL texture)
                    from urllib.parse import parse_qs, urlparse
                    rel = (parse_qs(urlparse(self.path).query).get("path") or [""])[0]
                    try:
                        t = ref_data.thumb(vault, rel, hall_data._safe)
                    except (hall_data.HallError, ValueError):
                        t = None
                    return self._send(200, t[0], t[1]) if t else self._send(404, {"error": "зураг алга"})
                if path == "/api/ref":                                  # нэг reference-ийн үзэгчийн өгөгдөл
                    from urllib.parse import parse_qs, urlparse
                    rel = (parse_qs(urlparse(self.path).query).get("path") or [""])[0]
                    try:
                        return self._send(200, ref_data.fetch_ref(vault, rel, hall_data._safe))
                    except (hall_data.HallError, ValueError) as e:
                        return self._send(400, {"error": str(e)})
                if path == "/api/art":                                  # vault-ийн generative зураг (Research/*/Output/generative)
                    from urllib.parse import parse_qs, urlparse
                    arts = {p.name: p for p in Path(vault).glob("04-Resources/Research/*/Output/generative/*") if p.suffix.lower() in (".png", ".jpg", ".webp")}
                    f = (parse_qs(urlparse(self.path).query).get("f") or [""])[0]
                    if not f:
                        return self._send(200, sorted(arts))
                    p = arts.get(f)
                    return self._send(200, p.read_bytes(), ASSET_TYPES[p.suffix.lower()]) if p else self._send(404, {"error": "зураг алга"})
                if path == "/api/weather":                              # Улаанбаатарын одоогийн цаг агаар (Open-Meteo, 10 мин cache)
                    loc = local_map(vault) or {"office": [106.9176, 47.9188]}
                    try:
                        return self._send(200, weather_data.current(loc["office"][1], loc["office"][0]))
                    except Exception as e:
                        return self._send(502, {"error": type(e).__name__})
                if path == "/api/dem":                                  # газрын өндөр (Terrarium tiles, AWS open data) — ~/.fmos cache
                    from urllib.parse import parse_qs, urlparse
                    import urllib.request
                    q = parse_qs(urlparse(self.path).query)
                    try:
                        z, x, y = (int(q[k][0]) for k in ("z", "x", "y"))
                        assert 0 <= z <= 14
                    except Exception:
                        return self._send(400, {"error": "z,x,y"})
                    f = Path.home() / ".fmos" / "fm-office" / "dem" / f"{z}-{x}-{y}.png"
                    if not f.exists():
                        f.parent.mkdir(parents=True, exist_ok=True)
                        with urllib.request.urlopen(f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png", timeout=20) as r:
                            f.write_bytes(r.read())
                    return self._send(200, f.read_bytes(), "image/png")
                if path == "/api/osm":                                  # мини хот = гэрийн орчмын бодит гудамж (cache ~/.fmos)
                    import gzip
                    loc = local_map(vault)
                    if not loc:
                        return self._send(404, {"error": "ub-map.local.json алга"})
                    body = json.dumps(osm_data.build(loc["office"], 5000), separators=(",", ":")).encode()
                    if "gzip" in (self.headers.get("Accept-Encoding") or ""):
                        z = gzip.compress(body, 6)
                        self.send_response(200); self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_header("Content-Encoding", "gzip"); self.send_header("Content-Length", str(len(z)))
                        self.send_header("Cache-Control", "max-age=3600"); self.end_headers(); self.wfile.write(z); return
                    return self._send(200, body, "application/json; charset=utf-8")
                if path == "/api/days":                                 # өдрийн спираль
                    return self._send(200, days_data.days(vault))
                if path == "/api/day":
                    from urllib.parse import parse_qs, urlparse
                    try:
                        return self._send(200, days_data.day(vault, (parse_qs(urlparse(self.path).query).get("d") or [""])[0]))
                    except ValueError as e:
                        return self._send(400, {"error": str(e)})
                if path == "/api/home":
                    return self._send(200, home_data.build(vault))
                if path == "/api/state":
                    return self._send(200, build_state(vault))
                if path == "/favicon.ico":
                    return self._send(204, b"", "image/x-icon")
                self._send(404, {"error": "not found"})
            except Exception as e:
                self._send(500, {"error": str(e)})
        def do_POST(self):
            route = self.path.split("?")[0]
            if route not in ("/api/send", "/api/schedule", "/api/atom"):
                return self._send(404, {"error": "not found"})
            origin = self.headers.get("Origin") or ""
            if origin and not re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
                return self._send(403, {"error": "зөвхөн localhost-оос"})
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._send(415, {"error": "JSON хэрэгтэй"})
            if route == "/api/atom":                                   # Gallery hall → шинэ атом (байгааг дарахгүй)
                try:
                    n = min(int(self.headers.get("Content-Length", 0)), 40000)
                    return self._send(200, hall_data.write_atom(vault, json.loads(self.rfile.read(n) or b"{}")))
                except hall_data.HallError as e:
                    return self._send(400, {"error": str(e)})
                except Exception as e:
                    return self._send(500, {"error": type(e).__name__})
            if route == "/api/schedule":
                try:
                    n = min(int(self.headers.get("Content-Length", 0)), 4000)
                    req = json.loads(self.rfile.read(n) or b"{}")
                    return self._send(200, calendar_data.set_due(vault, req.get("task_path"), req.get("due"), req.get("confirm")))
                except calendar_data.ScheduleError as e:
                    return self._send(400, {"error": str(e)})
                except Exception as e:
                    return self._send(500, {"error": type(e).__name__})
            try:
                n = min(int(self.headers.get("Content-Length", 0)), 20000)
                req = json.loads(self.rfile.read(n) or b"{}")
                info = room_payload(vault, str(req.get("room") or ""))
                if not info:
                    return self._send(404, {"error": "өрөө алга"})
                sess = info.get("sessions") or []
                self._send(200, sender.handle(vault, req, set(info["send_channels"]), sess))
            except sender.SendError as e:
                self._send(400, {"error": str(e)})
            except Exception as e:
                self._send(502, {"error": "илгээж чадсангүй: " + type(e).__name__})
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=_default_vault())
    ap.add_argument("--port", type=int, default=5191)
    a = ap.parse_args()
    if not a.vault or not Path(a.vault).is_dir():
        sys.exit("Vault олдсонгүй: --vault өг эсвэл ~/.fmos/config.json тохируул")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"FM Office → http://localhost:{a.port}  (vault: {a.vault})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(Path(a.vault))).serve_forever()


if __name__ == "__main__":
    main()
