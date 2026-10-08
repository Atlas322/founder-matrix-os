"""FM Office — vault-ийг 3D оффис болгон localhost дээр харуулна (зөвхөн уншина).

Ажиллуулах:  python server.py [--vault "<vault хавтас>"] [--port 5191]
GET /            → index.html
GET /main.js     → 3D scene
GET /api/state   → floors, rooms, agents, conversations (office_state.py)
"""
import argparse, json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from office_state import build_state  # noqa: E402

STATIC = {"/": ("index.html", "text/html; charset=utf-8"),
          "/index.html": ("index.html", "text/html; charset=utf-8"),
          "/main.js": ("main.js", "text/javascript; charset=utf-8")}


def _default_vault():
    v = os.environ.get("FM_VAULT") or os.environ.get("FMOS_VAULT")
    if not v:
        cfg = Path(os.environ.get("FMOS_CONFIG", Path.home() / ".fmos" / "config.json"))
        try:
            v = json.loads(cfg.read_text(encoding="utf-8")).get("vault")
        except (OSError, ValueError):
            v = None
    return v


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
                if path == "/api/state":
                    return self._send(200, build_state(vault))
                if path == "/favicon.ico":
                    return self._send(204, b"", "image/x-icon")
                self._send(404, {"error": "not found"})
            except Exception as e:
                self._send(500, {"error": str(e)})
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
