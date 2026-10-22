"""Өдөр бүрийн идэвх (Spiral): лог мөр (дүрээр), шинэ атом, дууссан task, өдрийн тэмдэглэл. Зөвхөн уншина.

days(vault)       → [{date, counts:{domain:n}, total, daily}]  (хамгийн эртний логоос өнөөдөр хүртэл)
day(vault, date)  → {date, log:[{t,actor,domain,text}], atoms:[…], tasks:[…], daily:{title,lines}}
full(vault)       → [{date, log, atoms, tasks, daily(bool)}] — спиралийн бүх цэг нэг удаа (Ross маягийн спираль)
Хувийн (`private: true`) task, санхүүгийн хэсэг тоологдохгүй.
"""
import re
from datetime import date, timedelta
from pathlib import Path

DOMAINS = ["architect", "gtd", "creative", "wiki", "project", "atom", "task", "other"]
LOG = re.compile(r"^- \*\*(\d\d:\d\d)\*\* · ([^→\n]+?)\s*→\s*(.*)$")
DAY = re.compile(r"^(\d{4}-\d\d-\d\d)")


def domain_of(actor):
    a = actor.lower()
    if "harvester" in a:
        return None                                   # атомыг файлаар нь тоолно (давхардахгүй)
    for key, d in (("architect", "architect"), ("gtd", "gtd"), ("creative", "creative"), ("wiki", "wiki"),
                   ("research", "wiki"), ("📁", "project"), ("project", "project")):
        if key in a:
            return d
    return "other"


def _private(text):
    return "private: true" in text[:600]


def _log_lines(vault, d):
    p = Path(vault) / "_system/logs" / f"{d}.md"
    out = []
    if p.is_file():
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = LOG.match(line.strip())
            if m:
                dom = domain_of(m.group(2))
                if dom:
                    out.append({"t": m.group(1), "actor": m.group(2).strip(), "domain": dom, "text": m.group(3).strip()[:300]})
    return out


def _atoms_by_day(vault):
    res, root = {}, Path(vault) / "04-Resources/Atomic"
    for p in root.rglob("*.md") if root.is_dir() else []:
        m = DAY.match(p.stem)
        if m and not _private(p.read_text(encoding="utf-8", errors="ignore")):
            res.setdefault(m.group(1), []).append(p.stem)
    return res


def _tasks_by_day(vault):
    res, root = {}, Path(vault) / "01-GTD/Tasks"
    for p in root.glob("*.md") if root.is_dir() else []:
        text = p.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"^completed:\s*(\d{4}-\d\d-\d\d)", text[:1500], re.M)
        if m and not _private(text):
            res.setdefault(m.group(1), []).append(p.stem)
    return res


def _daily(vault, d):
    p = Path(vault) / "01-GTD/Daily" / f"{d}.md"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="ignore")
    if _private(text):
        return None
    body = text.split("\n---", 1)[1] if text.startswith("---") else text
    lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith(("```", "|---"))]
    title = next((l.lstrip("# ") for l in lines if l.startswith("#")), d)
    return {"title": title, "lines": [l for l in lines if not l.startswith("#")][:40]}


def days(vault, today=None):
    today = today or date.today()
    logs = Path(vault) / "_system/logs"
    dates = sorted(m.group(1) for f in logs.glob("*.md") if (m := DAY.match(f.stem))) if logs.is_dir() else []
    start = date.fromisoformat(dates[0]) if dates else today
    atoms, tasks = _atoms_by_day(vault), _tasks_by_day(vault)
    out, d = [], start
    while d <= today:
        ds = d.isoformat()
        c = {k: 0 for k in DOMAINS}
        for l in _log_lines(vault, ds):
            c[l["domain"]] += 1
        c["atom"] = len(atoms.get(ds, []))
        c["task"] = len(tasks.get(ds, []))
        out.append({"date": ds, "counts": c, "total": sum(c.values()),
                    "daily": (Path(vault) / "01-GTD/Daily" / f"{ds}.md").is_file()})
        d += timedelta(days=1)
    return {"domains": DOMAINS, "days": out}


def day(vault, ds):
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", ds or ""):
        raise ValueError("огноо буруу")
    return {"date": ds, "log": _log_lines(vault, ds), "atoms": sorted(_atoms_by_day(vault).get(ds, [])),
            "tasks": sorted(_tasks_by_day(vault).get(ds, [])), "daily": _daily(vault, ds)}


PROJ = re.compile(r"02-Projects/([^/\]|]+)")


def full(vault, today=None):
    """Өдөр бүрийн бүх лог мөр + атом + task. Мөр бүрт `project` (утас холбох) тодорхойлно."""
    out, atoms, tasks = [], _atoms_by_day(vault), _tasks_by_day(vault)
    for d in days(vault, today=today)["days"]:
        ds = d["date"]; log = _log_lines(vault, ds)
        for it in log:
            m = PROJ.search(it["text"]) or (re.search(r"📁\s*([^·(]+)", it["actor"]))
            it["project"] = (m.group(1).strip() if m else "")
            if it["project"].lower() in ("project", "projects"): it["project"] = ""
        out.append({"date": ds, "log": log, "atoms": sorted(atoms.get(ds, [])), "tasks": sorted(tasks.get(ds, [])), "daily": d["daily"]})
    return out


WIKI = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")


def _targets(text):
    return {Path(m.group(1).strip()).name for m in WIKI.finditer(text)}


def life(vault, today=None):
    """Амьдралын спираль: өдөр бүрийн бүх цэг + «өнгөрснөөс → өнөөдөр» холбоос.

    items: [{id, date, kind: log|atom|task, domain, t, text, project}]
    edges: [[src_id, dst_id, days]] — dst (шинэ) нь src (хуучин) руу [[wikilink]]-ээр холбогдсон, days = хугацааны зөрүү.
    Хувийн (`private: true`) note-ууд орохгүй.
    """
    root = Path(vault)
    items, by_name = [], {}
    for d in full(vault, today=today):
        ds = d["date"]
        for i, l in enumerate(d["log"]):
            items.append({"id": f"L{ds}:{i}", "date": ds, "kind": "log", "domain": l["domain"], "t": l["t"], "actor": l["actor"],
                          "text": l["text"], "project": l.get("project", ""), "_links": _targets(l["text"])})
        for a in d["atoms"]:
            it = {"id": f"A:{a}", "date": ds, "kind": "atom", "domain": "atom", "t": "", "text": re.sub(r"^\d{4}-\d\d-\d\d - ", "", a), "project": "", "_links": set()}
            items.append(it); by_name[a] = it
        for tk in d["tasks"]:
            it = {"id": f"T:{tk}", "date": ds, "kind": "task", "domain": "task", "t": "", "text": tk, "project": "", "_links": set()}
            items.append(it); by_name[tk] = it
    atom_files = {p.stem: p for p in (root / "04-Resources/Atomic").rglob("*.md")} if (root / "04-Resources/Atomic").is_dir() else {}
    for name, it in by_name.items():
        p = atom_files.get(name) or (root / "01-GTD/Tasks" / f"{name}.md")
        if p.is_file():
            txt = p.read_text(encoding="utf-8", errors="ignore")
            it["_links"] = _targets(txt) - {name}
            m = re.search(r"^projects?:.*?02-Projects/([^/\]|]+)", txt[:1500], re.M)
            if m:
                it["project"] = m.group(1).strip()
    edges = []
    for it in items:
        for tg in it.pop("_links"):
            src = by_name.get(tg)
            if src and src["date"] < it["date"]:
                gap = (date.fromisoformat(it["date"]) - date.fromisoformat(src["date"])).days
                edges.append([src["id"], it["id"], gap])
    return {"items": items, "edges": edges}
