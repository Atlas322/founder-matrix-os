"""Цаглабар — хуанлийн өгөгдөл (зөвхөн уншина) + task-ийн `due:`-г аюулгүй солих.

Эх сурвалж (vault_index — frontmatter `type:`-аар, хавтас hardcode хийхгүй):
  task  → `due` / `scheduled` (YYYY-MM-DD[ HH:MM]) → блок; due-гүй next-action → «Огноогүй тавиур»
  event/meeting → `scheduled` / `date` (+цаг) → блок
  project → `milestones` (label/date/done) → ромбо тэмдэг; `stage` → өнгө
  daily → өдрийн жижиг цэг
"""
import re
from datetime import date, datetime
from pathlib import Path

import vault_index
from room_info import link_target, milestones, ACTIVITIES

DONE = {"completed", "done", "cancelled"}
DATE_RE = re.compile(r"^(\d{4}-\d\d-\d\d)(?:[ T](\d\d:\d\d))?")
HUMAN = {"bd", "itge.e", "itgee", "itge"}
# task-ийн `due:`-г зөвхөн эдгээр хавтсанд бичнэ (шинэ + хуучин layout)
TASK_DIR_RE = re.compile(r"^(?:0[0-2]-GTD/Tasks|02-GTD/tasks|01-GTD/tasks)/[^/]+\.md$")


def parse_dt(v):
    m = DATE_RE.match(str(v or "").strip())
    if not m:
        return None, None
    try:
        date.fromisoformat(m.group(1))
    except ValueError:
        return None, None
    return m.group(1), m.group(2)


def owner_agent(owner, project_name, agents, rooms_by_name):
    """owner текст → агентын id (itge.e = 'itgee'); «claude» бол төслийн өрөөний агент."""
    o = re.sub(r"\[\[|\]\]", "", owner or "").strip()
    n = o.lower()
    if not n:
        return None
    if n in HUMAN:
        return "itgee"
    import discord_feed
    if n in ("claude", "agent", "ai"):
        room = rooms_by_name.get(project_name)
        cands = [a for a in agents if room and a["room"] == room and not a.get("human")]
        cands.sort(key=lambda a: a.get("state") != "working")
        return cands[0]["id"] if cands else None
    return discord_feed.match_agent(o, agents)


def build(vault, state, start, end):
    """start/end = 'YYYY-MM-DD' (оролцуулна). → {items, shelf, milestones, daily, vault_name}."""
    vault = Path(vault)
    agents = state["agents"]
    rooms = state["rooms"]
    rooms_by_name = {r["project"]: r["id"] for r in rooms if r["kind"] == "project"}
    stage_of = {r["project"]: r["stage"] for r in rooms if r["kind"] == "project"}
    # тавиурт зөвхөн идэвхтэй/төлөвлөж буй төслийн task (архив, on-hold, someday, дууссан, өрөөгүй төсөл биш)
    shelf_ok = {r["project"] for r in rooms if r["kind"] == "project" and r.get("status") not in ("on-hold", "someday", "completed", "done", "cancelled")}
    working = {a["id"] for a in agents if a.get("state") == "working" and not a.get("human")}
    items, shelf, ms, daily = [], {}, [], []
    for n in vault_index.index(vault):
        t, fm, path = n["type"], n["fm"], n["path"]
        if path.startswith("_"):
            continue
        if t == "daily":
            d, _ = parse_dt(fm.get("date") or n["name"])
            if d and start <= d <= end:
                daily.append(d)
            continue
        if t == "project":
            parts = path.split("/")
            if len(parts) < 3 or parts[-2] != n["name"] or parts[0].startswith("99"):
                continue
            try:
                text = (vault / path).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in milestones(text):
                d, _ = parse_dt(m["date"])
                if d and start <= d <= end:
                    ms.append({"date": d, "label": m["label"], "done": m["done"], "project": n["name"],
                               "stage": stage_of.get(n["name"]), "room": rooms_by_name.get(n["name"])})
            continue
        proj = Path(link_target(fm.get("project"))).name if fm.get("project") else ""
        st = (fm.get("status") or "").lower()
        if t == "task":
            d, tm = parse_dt(fm.get("due"))
            if not d:
                d, tm = parse_dt(fm.get("scheduled"))
            ag = owner_agent(fm.get("owner"), proj, agents, rooms_by_name)
            state_ = "done" if st in DONE else ("working" if ag in working and st == "next-action" else "scheduled")
            item = {"kind": "task", "path": path, "title": n["title"], "date": d, "time": tm, "project": proj,
                    "stage": stage_of.get(proj), "room": rooms_by_name.get(proj), "status": st or "inbox",
                    "priority": fm.get("priority", ""), "owner": re.sub(r"\[\[|\]\]", "", fm.get("owner", ""))[:60],
                    "agent": ag, "state": state_, "due_raw": fm.get("due", "")}
            if d:
                if start <= d <= end:
                    items.append(item)
            elif st == "next-action" and (not proj or proj in shelf_ok):
                shelf.setdefault(proj or "Төсөлгүй", []).append(item)
        elif t in ("event", "meeting"):
            d, tm = parse_dt(fm.get("scheduled") or fm.get("date") or fm.get("met"))
            if d and start <= d <= end:
                items.append({"kind": "event", "path": path, "title": n["title"], "date": d,
                              "time": tm or ((re.match(r"^\d\d:\d\d", str(fm.get("time") or fm.get("start") or "")) or [None])[0]),
                              "project": proj, "stage": stage_of.get(proj), "room": rooms_by_name.get(proj),
                              "status": st or "scheduled", "state": "done" if st in DONE else "scheduled", "agent": None})
    items.sort(key=lambda x: (x["date"], x["time"] or "", x["title"]))
    order = {a: i for i, a in enumerate(ACTIVITIES)}
    shelf_l = [{"project": k, "stage": stage_of.get(k), "tasks": sorted(v, key=lambda x: x["title"])}
               for k, v in shelf.items()]
    shelf_l.sort(key=lambda g: (order.get(g["stage"], 99), g["project"]))
    return {"items": items, "shelf": shelf_l, "milestones": ms, "daily": sorted(set(daily)), "vault_name": vault.name,
            "range": [start, end]}


# ---------- товлох: зөвхөн `due:` мөрийг солино ----------
class ScheduleError(ValueError):
    pass


def set_due(vault, task_path, due, confirm):
    """task_path (vault-аас харьцангуй) файлын frontmatter-ийн `due:` мөрийг л солино. → өмнөх утга."""
    if confirm is not True:
        raise ScheduleError("баталгаажуулалт (confirm) алга")
    due = (due or "").strip()
    if due:
        d, _ = parse_dt(due)
        if not d or d != due:
            raise ScheduleError("огноо YYYY-MM-DD байх ёстой")
    rel = str(task_path or "").replace("\\", "/").lstrip("/")
    if ".." in rel.split("/") or not TASK_DIR_RE.match(rel):
        raise ScheduleError("зөвхөн 01-GTD/Tasks (эсвэл хуучин task хавтас) доторх task")
    vault = Path(vault).resolve()
    f = (vault / rel).resolve()
    if vault not in f.parents or not f.is_file():
        raise ScheduleError("файл олдсонгүй")
    raw = f.read_bytes()
    text = raw.decode("utf-8")
    m = re.match(r"^---(\r?\n)(.*?)(\r?\n)---", text, re.S)
    if not m:
        raise ScheduleError("frontmatter алга")
    nl = m.group(1)
    block = m.group(2)
    fmline = dict(re.findall(r"(?m)^([A-Za-z_][\w-]*):[ \t]*(.*?)\s*$", block))
    if fmline.get("type", "").strip("\"'") != "task":
        raise ScheduleError("task биш")
    if fmline.get("private", "").lower() == "true" or "finances/private" in rel.lower():
        raise ScheduleError("хувийн note")
    dm = re.search(r"(?m)^due:[^\r\n]*", block)
    prev = dm.group(0)[4:].strip().strip("\"'") if dm else ""
    new_line = f"due: {due}" if due else "due:"
    if dm:
        nb = block[:dm.start()] + new_line + block[dm.end():]
    else:
        nb = block + nl + new_line
    out = text[:m.start(2)] + nb + text[m.end(2):]
    f.write_bytes(out.encode("utf-8"))
    vault_index.invalidate()
    return {"ok": True, "path": rel, "due": due, "previous": prev}
