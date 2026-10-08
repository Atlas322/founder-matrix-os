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
import room_info, sender  # noqa: E402

STATIC = {"/": ("office2d.html", "text/html; charset=utf-8"),          # 2.5D зурагт оффис (үндсэн)
          "/office2d.js": ("office2d.js", "text/javascript; charset=utf-8"),
          "/tokens.css": ("tokens.css", "text/css; charset=utf-8"),
          "/3d": ("index.html", "text/html; charset=utf-8"),             # хуучин Three.js хувилбар
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/main.js": ("main.js", "text/javascript; charset=utf-8")}
ASSET_TYPES = {".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json; charset=utf-8"}


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
                if path == "/api/state":
                    return self._send(200, build_state(vault))
                if path == "/favicon.ico":
                    return self._send(204, b"", "image/x-icon")
                self._send(404, {"error": "not found"})
            except Exception as e:
                self._send(500, {"error": str(e)})
        def do_POST(self):
            if self.path.split("?")[0] != "/api/send":
                return self._send(404, {"error": "not found"})
            origin = self.headers.get("Origin") or ""
            if origin and not re.match(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", origin):
                return self._send(403, {"error": "зөвхөн localhost-оос"})
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return self._send(415, {"error": "JSON хэрэгтэй"})
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
