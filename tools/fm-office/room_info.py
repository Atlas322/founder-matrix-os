"""FM Office — нэг өрөөний (төслийн) дашбоард: шат, milestone, task, сешний baton, холбоос. Зөвхөн уншина.

Task: 01-GTD/Tasks/*.md (fallback 02-GTD/tasks/), frontmatter `type: task`, `project: [[…/<Name>/<Name>]]`.
Baton: _system/fm/state/<slug>.md-ийн «## ОДОО» хэсэг.
Нууцлал: төслийн frontmatter-оос зөвхөн цагаан жагсаалтын талбар (finance гэх мэт хэзээ ч биш).
"""
import re, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

TASK_DIRS = ["01-GTD/Tasks", "00-GTD/Tasks", "02-GTD/tasks"]  # шинэ, одоогийн, хуучин
OPEN = ["next-action", "waiting", "inbox", "someday"]
DONE = {"completed", "done"}
ACTIVITIES = ["Brief", "Бэлтгэл", "Дизайн", "Хөгжүүлэлт", "Контент"]
TEXT_MAX = 220


def _fm_block(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    return m.group(1) if m else ""


def flat_fm(text):
    out = {}
    for line in _fm_block(text).splitlines():
        k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if k:
            out[k.group(1)] = k.group(2).strip().strip('"').strip("'")
    return out


def milestones(text):
    """`milestones:` жагсаалт → [{label, date, done}]."""
    out, cur, inside = [], None, False
    for line in _fm_block(text).splitlines():
        if re.match(r"^milestones:\s*$", line):
            inside = True
            continue
        if inside:
            if re.match(r"^\S", line):
                break
            m = re.match(r"^\s*-\s*(\w+):\s*(.*)$", line)
            if m:
                cur = {}
                out.append(cur)
            m = m or re.match(r"^\s+(\w+):\s*(.*)$", line)
            if m and cur is not None and m.group(1) in ("label", "date", "done"):
                v = m.group(2).strip().strip('"').strip("'")
                cur[m.group(1)] = (v.lower() == "true") if m.group(1) == "done" else v
    return [{"label": x.get("label", ""), "date": x.get("date", ""), "done": bool(x.get("done"))} for x in out if x.get("label")]


def link_target(v):
    m = re.search(r"\[\[([^\]|#]+)", v or "")
    return m.group(1).strip() if m else (v or "").strip()


def tasks_for(vault, project, now=None):
    """Төслийн нээлттэй task-ууд (статусаар бүлэглэсэн) + энэ долоо хоногт дууссан тоо."""
    now = now or datetime.now()
    week0 = (now - timedelta(days=now.weekday())).date()
    groups = {s: [] for s in OPEN}
    done_week, seen = 0, set()
    for d in TASK_DIRS:
        base = Path(vault) / d
        if not base.is_dir():
            continue
        for f in base.rglob("*.md"):
            if f.name in seen:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            fm = flat_fm(text)
            if fm.get("type") != "task" or str(fm.get("private", "")).lower() == "true":
                continue
            if Path(link_target(fm.get("project"))).name != project:
                continue
            seen.add(f.name)
            st = fm.get("status", "inbox")
            if st in DONE:
                try:
                    if datetime.strptime((fm.get("completed") or fm.get("updated") or "")[:10], "%Y-%m-%d").date() >= week0:
                        done_week += 1
                except ValueError:
                    pass
                continue
            if st not in groups:
                continue
            h = re.search(r"^#\s+(.+)$", text, re.M)
            groups[st].append({"title": (h.group(1) if h else f.stem)[:140], "status": st,
                               "priority": fm.get("priority", ""), "due": fm.get("due", ""),
                               "owner": re.sub(r"\[\[|\]\]", "", fm.get("owner", ""))[:60]})
    for g in groups.values():
        g.sort(key=lambda t: (t["due"] or "9999", t["title"]))
    return {"groups": groups, "open": sum(len(g) for g in groups.values()), "done_week": done_week}


def _clip(s):
    s = re.sub(r"<[^>]+>.*?</[^>]+>", "", s or "", flags=re.S)  # cross-session блокуудыг хасна
    s = re.sub(r"\s+", " ", re.sub(r"[*_`#>]+", "", s)).strip()
    return s if len(s) <= TEXT_MAX else s[:TEXT_MAX - 1] + "…"


def baton(vault, slug):
    """state/<slug>.md «ОДОО» → {ts, by, next, stopped}. Хэрэглэгчийн хүсэлтийн мөрийг гаргахгүй."""
    f = Path(vault) / "_system" / "fm" / "state" / f"{slug}.md"
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    m = re.search(r"^## ОДОО · (\S+ \S+) · (.+?)\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return None
    body = m.group(3)
    nxt = re.search(r"^\*\*Дараагийн алхам[^*]*:\*\*\s*(.+)$", body, re.M)
    stop = re.search(r"\*\*Хаана зогссон[^*]*\*\*\s*\n+(.+?)(?:\n\n|\Z)", body, re.S)
    return {"ts": m.group(1), "by": re.sub(r"\s*\((?:PC|Mac)\)\s*$", "", m.group(2)).strip(),
            "next": _clip(nxt.group(1)) if nxt else "", "stopped": _clip(stop.group(1)) if stop else ""}


def project_note(vault, name):
    for root in ("02-Projects", "03-Projects"):  # шинэ, одоогийн layout
        for d in ("1-Active", "2-Planning", "3-On-hold"):
            p = Path(vault) / root / d / name / f"{name}.md"
            if p.is_file():
                return p
    return None


def project_info(vault, room, agents, all_agents, slugs):
    vault = Path(vault)
    name = room["project"]
    out = {"room": room, "stages": ACTIVITIES, "milestones": [], "due": "", "links": [], "tasks": None, "sessions": []}
    note = project_note(vault, name)
    vname = vault.name
    if note:
        text = note.read_text(encoding="utf-8", errors="ignore")
        fm = flat_fm(text)
        out["due"] = fm.get("due") or fm.get("deadline") or fm.get("end") or ""
        out["start"] = fm.get("start", "")
        out["milestones"] = milestones(text)
        rel = note.relative_to(vault).as_posix()
        q = lambda f: "obsidian://open?" + urllib.parse.urlencode({"vault": vname, "file": f}, quote_via=urllib.parse.quote)
        out["links"].append({"label": "📝 Төслийн note", "url": q(rel[:-3])})
        if (note.parent / "_BRAIN.md").is_file():
            out["links"].append({"label": "🧠 _BRAIN", "url": q(rel.rsplit("/", 1)[0] + "/_BRAIN")})
        for k, lbl in (("figma", "🎨 Figma"), ("repo", "💻 Repo"), ("url", "🌐 Сайт"), ("site", "🌐 Сайт")):
            v = fm.get(k, "")
            if v.startswith("http"):
                out["links"].append({"label": lbl, "url": v})
    out["tasks"] = tasks_for(vault, name)
    b = {s: baton(vault, s) for s in slugs}
    now = datetime.now()
    for a in agents:
        if a.get("human"):
            continue
        bt = b.get(a["project"])
        out["sessions"].append({**{k: a[k] for k in ("id", "name", "device", "device_name", "state", "last_seen", "channel")},
                                "baton": bt, "bound": True})
    # тусгай дүрийн агентууд энэ төсөл дээр сүүлийн 3 хоногт ажилласан бол (baton-д нэр нь гарсан)
    for a in all_agents:
        if a.get("human") or a in agents or a["room"].startswith("p:"):
            continue
        bt = baton(vault, a["project"])
        try:
            fresh = bt and now - datetime.strptime(bt["ts"], "%Y-%m-%d %H:%M") < timedelta(days=3)
        except ValueError:
            fresh = False
        if fresh and name.lower() in (bt["next"] + " " + bt["stopped"]).lower():
            out["sessions"].append({**{k: a[k] for k in ("id", "name", "device", "device_name", "state", "last_seen", "channel")},
                                    "baton": bt, "bound": False})
    return out


def workshop_info(vault, room, rooms):
    projs = [r for r in rooms if r["kind"] == "project" and r["stage"] == room["stage"]]
    return {"room": room, "projects": [{"id": r["id"], "project": r["project"], "status": r["status"],
                                        "tasks": tasks_for(vault, r["project"])} for r in projs]}
