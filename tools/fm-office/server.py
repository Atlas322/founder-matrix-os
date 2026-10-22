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
import room_info, sender, calendar_data, home_data, hall_data, ref_data, days_data, osm_data, weather_data, map_data, control_state, desk_data  # noqa: E402

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
          "/control": ("control.html", "text/html; charset=utf-8"),
          "/office25d": ("office25d.html", "text/html; charset=utf-8"),      # Агентын оффис 2.5D (Three.js, Kenney)          # Удирдлагын өрөө (agent office, шат 1)
          "/campus": ("campus.html", "text/html; charset=utf-8"),            # Оффисын кампус (барилгын түвшин, v02)
          "/home": ("home.html", "text/html; charset=utf-8"),                # Second Brain мини хот (гэр)
          "/xr": ("gallery-xr.html", "text/html; charset=utf-8"),           # Spatial Gallery (WebXR, шил)
          "/hall": ("hall.html", "text/html; charset=utf-8"),
          "/gallery": ("gallery.html", "text/html; charset=utf-8"),         # Gallery: Neuform маягийн bento тор
          "/fpv": ("fpv.html", "text/html; charset=utf-8"),                 # Gallery FPV: хулгана түгжээд алхана
          "/khuvsgul": ("khuvsgul.html", "text/html; charset=utf-8"),       # Хөвсгөлийн ертөнц (Blender → вэб): алхаж, vault-тай
          "/garden": ("garden.html", "text/html; charset=utf-8"),           # Миний цэцэрлэг: өвс, салхи, ажлын ширээ
          # /spiral устгав (2026-10-20): өдрийн спираль одоо /khuvsgul-ийн тэнгэрт (#spiral)
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
ASSET_TYPES = {".glb": "model/gltf-binary", ".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json; charset=utf-8", ".hdr": "application/octet-stream"}


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
                    from urllib.parse import parse_qs, urlparse
                    if (parse_qs(urlparse(self.path).query).get("at") or [""])[0] == "khuvsgul":
                        loc = {"office": [100.16, 50.45]}                   # Хатгал, Хөвсгөл (нийтийн газар)
                    else:
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
                if path == "/api/garden":                               # zen цэцэрлэгийн барилгууд = PARA
                    import garden_data
                    return self._send(200, garden_data.build(vault))
                if path == "/api/days":                                 # өдрийн спираль
                    from urllib.parse import parse_qs, urlparse
                    if (parse_qs(urlparse(self.path).query).get("life") or [""])[0] == "1":
                        return self._send(200, days_data.life(vault))
                    if (parse_qs(urlparse(self.path).query).get("full") or [""])[0] == "1":
                        return self._send(200, {"days": days_data.full(vault)})
                    return self._send(200, days_data.days(vault))
                if path == "/api/day":
                    from urllib.parse import parse_qs, urlparse
                    try:
                        return self._send(200, days_data.day(vault, (parse_qs(urlparse(self.path).query).get("d") or [""])[0]))
                    except ValueError as e:
                        return self._send(400, {"error": str(e)})
                if path == "/api/feed":                                 # төслийн HUD: сүүлийн task + Output зураг/бичлэг
                    import feed_data
                    return self._send(200, feed_data.feed(vault))
                if path == "/api/feed/file":                            # HUD-ийн зураг/бичлэг (Range дэмжинэ)
                    import feed_data
                    from urllib.parse import parse_qs, urlparse
                    try:
                        fp, ct = feed_data.media_file(vault, (parse_qs(urlparse(self.path).query).get("p") or [""])[0])
                    except feed_data.FeedError as e:
                        return self._send(404, {"error": str(e)})
                    size = fp.stat().st_size; a, b = 0, size - 1
                    m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range") or "")
                    if m:
                        a = int(m.group(1) or 0); b = min(int(m.group(2)) if m.group(2) else size - 1, size - 1)
                    with open(fp, "rb") as f:
                        f.seek(a); body = f.read(b - a + 1)
                    self.send_response(206 if m else 200); self.send_header("Content-Type", ct); self.send_header("Accept-Ranges", "bytes")
                    if m:
                        self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
                    self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "max-age=600"); self.end_headers(); self.wfile.write(body); return
                if path == "/api/books":                                # Хөвсгөлийн номын сан: 04-Resources → тавиур, ном
                    import library_data
                    return self._send(200, library_data.books(vault))
                if path.startswith("/nl/"):                            # newsletter-ийн html ба түүний зураг (дугаарын хавтас дотроос л)
                    import library_data
                    from urllib.parse import unquote
                    parts = unquote(path[4:]).split("/", 1)
                    try:
                        body, ct = library_data.issue_asset(vault, parts[0], parts[1] if len(parts) > 1 else "")
                    except library_data.LibraryError as e:
                        return self._send(404, {"error": str(e)})
                    self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
                if path == "/api/nl":                                   # INAI Newsletter дугаарын html / нүүр зураг
                    import library_data
                    from urllib.parse import parse_qs, urlparse
                    q = parse_qs(urlparse(self.path).query)
                    try:
                        body, ct = library_data.issue_file(vault, (q.get("no") or [""])[0], (q.get("f") or ["html"])[0])
                    except library_data.LibraryError as e:
                        return self._send(404, {"error": str(e)})
                    self.send_response(200); self.send_header("Content-Type", ct); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
                if path == "/api/backlinks":                            # энэ note руу заасан note-ууд (wiki «Энд холбогдсон»)
                    import library_data
                    from urllib.parse import parse_qs, urlparse
                    return self._send(200, {"links": library_data.backlinks(vault, (parse_qs(urlparse(self.path).query).get("path") or [""])[0])})
                if path == "/api/book":                                 # нэг номыг унших (private-гүй, 04-Resources дотор)
                    import library_data
                    from urllib.parse import parse_qs, urlparse
                    rel = (parse_qs(urlparse(self.path).query).get("path") or [""])[0]
                    try:
                        return self._send(200, library_data.read(vault, rel))
                    except library_data.LibraryError as e:
                        return self._send(404, {"error": str(e)})
                if path == "/api/home":
                    return self._send(200, home_data.build(vault))
                if path == "/api/control":                              # Claude Code сешнүүдийн төлөв, agent tree
                    d = control_state.build()
                    d["desks"] = desk_data.desks(vault, d["sessions"]); d["meeting"] = desk_data.meeting(vault)
                    return self._send(200, d)
                if path == "/api/state":
                    return self._send(200, build_state(vault))
                if path == "/favicon.ico":
                    return self._send(204, b"", "image/x-icon")
                self._send(404, {"error": "not found"})
            except Exception as e:
                self._send(500, {"error": str(e)})
        def do_POST(self):
            route = self.path.split("?")[0]
            if route not in ("/api/send", "/api/schedule", "/api/atom", "/api/meeting"):
                return self._send(404, {"error": "not found"})
            origin = self.headers.get("Origin") or ""
            if origin and not re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
                return self._send(403, {"error": "зөвхөн localhost-оос"})
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._send(415, {"error": "JSON хэрэгтэй"})
            if route == "/api/meeting":                                # Удирдлагын өрөө → хурлын ширээнд асуудал нэмэх (append)
                try:
                    n = min(int(self.headers.get("Content-Length", 0)), 4000)
                    return self._send(200, desk_data.add_issue(vault, json.loads(self.rfile.read(n) or b"{}")))
                except desk_data.DeskError as e:
                    return self._send(400, {"error": str(e)})
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
