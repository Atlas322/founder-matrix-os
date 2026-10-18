"""Өдөр бүрийн идэвх (Spiral): лог мөр (дүрээр), шинэ атом, дууссан task, өдрийн тэмдэглэл. Зөвхөн уншина.

days(vault)       → [{date, counts:{domain:n}, total, daily}]  (хамгийн эртний логоос өнөөдөр хүртэл)
day(vault, date)  → {date, log:[{t,actor,domain,text}], atoms:[…], tasks:[…], daily:{title,lines}}
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
