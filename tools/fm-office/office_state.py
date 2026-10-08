"""FM Office — vault-аас /api/state-ийн JSON-ийг бүрдүүлнэ (зөвхөн уншина).

Эх сурвалж:
  03-Projects/{1-Active,2-Planning,3-On-hold}/<Name>/<Name>.md  → status, stage
  99-Archive/Projects/*                                         → харанхуй архивын өрөө
  _system/fm/registry.json                                      → агент (сешн)
  _system/fm/state/<project>.md  "## ОДОО · <ts> · <name> (<dev>)" → last_seen
  _system/fm/channels.json                                      → Discord суваг
  _system/logs/<өнөөдөр>.md  "- **HH:MM** · A → B: text"          → яриа

Нууцлал: 04-Areas/Business/finances/private-ийг огт уншихгүй; private: true төсөл/сешн,
Finance/санхүүгийн сешн, Personal/Home сешнийг алгасна.
"""
import json, re
import discord_feed
from names import Names, norm as _nnorm, clean as _clean
from datetime import datetime, timedelta
from pathlib import Path

ACTIVITIES = ["Brief", "Бэлтгэл", "Дизайн", "Хөгжүүлэлт", "Контент"]
STATUS_DIRS = {"1-Active": "active", "2-Planning": "planning", "3-On-hold": "on-hold"}
WORKING_MIN = 20  # энэ хугацаанд state шинэчлэгдсэн бол «ажиллаж байна»
FLOORS = [
    {"id": "projects", "label": "03 Projects"},
    {"id": "areas", "label": "04 Areas · Key Activity"},
    {"id": "resources", "label": "05 Resources"},
    {"id": "business", "label": "Business"},
    {"id": "archive", "label": "99 Archive"},
]
DEFAULT_CFG = {
    "aliases": {},  # registry-ийн project slug → төслийн хавтасны нэр (vault-ийн _system/fm/fm-office.json)
    "research": [],  # Research өрөөнд суух project slug-ууд
    "generic": ["project", "area", "creative", "developer", "content-writer", "command-center", "resource", "finance"],
}
PARKED_STATUS = {"on-hold", "someday"}


def load_config(vault):
    """Нэр, slug-ийн тааруулгыг repo-д биш vault-д хадгална (_system/fm/fm-office.json)."""
    cfg = dict(DEFAULT_CFG)
    try:
        cfg.update(json.loads((vault / "_system" / "fm" / "fm-office.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if k:
                out[k.group(1)] = k.group(2).strip().strip('"').strip("'")
    return out


def stage_of(val):
    m = re.search(r"activities/([^\]|]+)", val or "")
    s = m.group(1).strip() if m else None
    return s if s in ACTIVITIES else None


def is_private(v):
    return str(v).lower() in ("true", "yes", "1")


def _norm(s):
    return re.sub(r"[^\w]+", "", s.lower())


def read_projects(vault):
    rooms = []
    for d, status in STATUS_DIRS.items():
        base = vault / "03-Projects" / d
        if not base.is_dir():
            continue
        for p in sorted(base.iterdir()):
            if not p.is_dir():
                continue
            note = p / f"{p.name}.md"
            fm = {}
            if note.is_file():
                fm = frontmatter(note.read_text(encoding="utf-8", errors="ignore"))
            if is_private(fm.get("private")):
                continue
            stg, stt = stage_of(fm.get("stage")), (fm.get("status") or status)
            rooms.append({"id": "p:" + p.name, "floor": "projects", "kind": "project",
                          "project": p.name, "stage": stg, "status": stt,
                          "parked": (not stg) or stt in PARKED_STATUS})
    order = {a: i for i, a in enumerate(ACTIVITIES)}
    rooms.sort(key=lambda r: (r["parked"], order.get(r["stage"], 99), r["project"].lower()))
    arch = vault / "99-Archive" / "Projects"
    if arch.is_dir():
        for p in sorted(arch.iterdir()):
            if p.is_dir() and not p.name.startswith((".", "_")):
                note = p / f"{p.name}.md"
                if note.is_file() and is_private(frontmatter(note.read_text(encoding="utf-8", errors="ignore")).get("private")):
                    continue
                rooms.append({"id": "a:" + p.name, "floor": "archive", "kind": "archive",
                              "project": p.name, "stage": None, "status": "archived"})
    return rooms


def build_rooms(vault):
    rooms = read_projects(vault)
    load = {a: 0 for a in ACTIVITIES}
    for r in rooms:
        if r["kind"] == "project" and r["stage"]:
            load[r["stage"]] += 1
    for a in ACTIVITIES:
        rooms.append({"id": "w:" + a, "floor": "areas", "kind": "workshop", "project": a,
                      "stage": a, "status": "workshop", "load": load[a]})
    rooms.append({"id": "hq", "floor": "areas", "kind": "hq", "project": "Төв оффис",
                  "stage": None, "status": "area"})
    rooms.append({"id": "wiki", "floor": "resources", "kind": "library", "project": "Wiki",
                  "stage": None, "status": "resource"})
    rooms.append({"id": "research", "floor": "resources", "kind": "library", "project": "Research",
                  "stage": None, "status": "resource"})
    rooms.append({"id": "vault", "floor": "business", "kind": "vault", "project": "Санхүүгийн сан",
                  "stage": None, "status": "locked"})
    return rooms


def _skip_session(v):
    txt = " ".join(str(v.get(k, "")) for k in ("name", "group", "project", "role", "title")).lower()
    return (is_private(v.get("private")) or "finance" in txt or "санхүү" in txt
            or "personal" in txt or "home" in txt)


def last_seen_map(vault):
    """state/<project>.md-ийн «## ОДОО · ts · name (dev)» гарчгаас {(project, name): datetime}."""
    out = {}
    sd = vault / "_system" / "fm" / "state"
    if not sd.is_dir():
        return out
    for f in sd.glob("*.md"):
        if "(1)" in f.name:
            continue
        try:
            head = f.read_text(encoding="utf-8", errors="ignore")[:4000]
        except OSError:
            continue
        for m in re.finditer(r"^## ОДОО · (\d{4}-\d\d-\d\d \d\d:\d\d) · (.+?)(?: \((PC|Mac)\))?\s*$", head, re.M):
            try:
                ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            key = (f.stem, m.group(2).strip(), m.group(3) or "")
            if key not in out or ts > out[key]:
                out[key] = ts
    return out


def room_for(v, project_rooms, cfg=DEFAULT_CFG):
    proj, role = str(v.get("project", "")), str(v.get("role", ""))
    if proj in set(cfg["research"]):
        return "research"
    if proj == "resource" or role == "resource":
        return "wiki"
    if proj in set(cfg["generic"]):
        return "hq"
    target = cfg["aliases"].get(proj, proj)
    for r in project_rooms:
        if _norm(r["project"]) == _norm(target):
            return r["id"]
    for r in project_rooms:  # хагас таарц: «Maggod Website» ↔ «Maggod Artist Website»
        if _norm(proj) and (_norm(proj) in _norm(r["project"]) or _norm(r["project"]) in _norm(proj)):
            return r["id"]
    return "hq"


def build_agents(vault, rooms, now=None):
    now = now or datetime.now()
    reg_p = vault / "_system" / "fm" / "registry.json"
    try:
        reg = json.loads(reg_p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    try:
        chans = json.loads((vault / "_system/fm/channels.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        chans = {}
    try:
        guild = json.loads((vault / "_system/fm/discord.json").read_text(encoding="utf-8"))["guild"]["id"]
    except (OSError, ValueError, KeyError, TypeError):
        guild = None
    seen = last_seen_map(vault)
    cfg = load_config(vault)
    proj_rooms = [r for r in rooms if r["kind"] == "project"]
    room_name = {r["id"]: r["project"] for r in rooms}
    nm = Names(vault, cfg)
    merged = {}  # (одоогийн нэр, төхөөрөмж) → агент — хуучин нэртэй давхар сешнийг нэгтгэнэ
    for sid, v in (reg.get("sessions") or {}).items():
        if not isinstance(v, dict) or _skip_session(v):
            continue
        old = v.get("name") or v.get("title") or sid[:8]
        proj = str(v.get("project", ""))
        dev = v.get("device", "")
        ts = seen.get((proj, old, dev)) or seen.get((proj, old, ""))
        room = room_for(v, proj_rooms, cfg)
        name = nm.display(v, room_name.get(room) if room.startswith("p:") else None)
        keys = {_nnorm(x) for x in (name, _clean(name), old, _clean(old), v.get("title"), _clean(v.get("title")),
                                    v.get("old_title"), _clean(v.get("old_title")), v.get("role"), proj) if x}
        keys |= {k for k, title in nm.alias.items() if title == name}
        keys.discard("")
        a = merged.get((name, dev))
        if a:
            a["keys"] |= keys
            a["merged"] += 1
            if ts and (not a["_ts"] or ts > a["_ts"]):
                a["_ts"] = ts
            continue
        merged[(name, dev)] = {
            "id": sid[:8], "name": name, "title": name, "role": v.get("role") or v.get("group"),
            "project": proj, "room": room, "device": "🍎" if dev == "Mac" else "🖥️", "device_name": dev,
            "_ts": ts, "channel": chans.get(proj), "guild": guild, "keys": keys, "merged": 1,
        }
    agents = []
    for a in merged.values():
        ts = a.pop("_ts")
        a["state"] = "working" if ts and timedelta(0) <= now - ts < timedelta(minutes=WORKING_MIN) else "idle"
        a["last_seen"] = ts.strftime("%Y-%m-%d %H:%M") if ts else None
        agents.append(a)
    return agents


LOG_RE = re.compile(r"^- \*\*(\d\d:\d\d)\*\* · (.+?) → (.+?)(?::\s*|\s+·\s+|\s+)(.*)$")


def conversations(vault, agents, now=None, limit=12):
    now = now or datetime.now()
    f = vault / "_system" / "logs" / f"{now:%Y-%m-%d}.md"
    if not f.is_file():
        return []

    def match(label):
        return discord_feed.match_agent(label, agents)

    out = []
    for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = LOG_RE.match(line.strip())
        if not m:
            continue
        hhmm, src, dst, text = m.groups()
        if any(w in (src + dst + text).lower() for w in ("finance", "санхүү", "private")):
            continue
        typ = "✅" if text.startswith("✅") or dst.startswith("✅") else ("🙋" if "🙋" in text else "send_message")
        dst_clean = dst.lstrip("✅ ").strip()
        out.append({"id": f"log:{hhmm}:{len(out)}", "ts": f"{now:%Y-%m-%d} {hhmm}:00", "time": hhmm, "from": match(src), "to": match(dst_clean), "from_label": src,
                    "to_label": dst_clean, "type": typ,
                    "text": re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", text)[:140]})
    return out[-limit:]


HUMAN = {"id": discord_feed.HUMAN_ID, "name": "itge.e", "title": "itge.e", "role": "founder", "project": "",
         "room": "hq", "device": "🙂", "device_name": "", "state": "working", "last_seen": None,
         "channel": None, "guild": None, "human": True}


def build_state(vault, now=None, discord=True):
    vault = Path(vault)
    now = now or datetime.now()
    rooms = build_rooms(vault)
    agents = build_agents(vault, rooms, now)
    cfg = load_config(vault)
    conv = conversations(vault, agents, now)
    if discord:
        conv = conv + discord_feed.fetch(vault, agents + [HUMAN], cfg.get("aliases"))
    conv = [c for c in conv if c.get("from")]
    conv.sort(key=lambda c: c.get("ts") or "")
    public = [{k: v for k, v in a.items() if k != "keys"} for a in agents]
    return {"generated": now.strftime("%Y-%m-%d %H:%M:%S"), "floors": FLOORS, "rooms": rooms,
            "agents": public + [HUMAN], "conversations": conv[-60:],
            "working_window_min": WORKING_MIN}
