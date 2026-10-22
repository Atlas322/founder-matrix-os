"""Төслийн HUD = сүүлийн Inbox→task-ууд + төслүүдийн Output зураг/бичлэг, төсөлтэй нь холбосон (зөвхөн уншина).

feed(vault)        → {"projects": [{"name", "tasks": [...], "media": [...]}]}
media_file(vault, rel) → (bytes, content-type) — зөвхөн 02-Projects / 04-Resources/Research доторх зураг, бичлэг.
"""
import re
from urllib.parse import quote
from pathlib import Path

IMG = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
VID = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime"}
ROOTS = ("02-Projects", "04-Resources/Research")
PER_DIR = 14


class FeedError(ValueError):
    pass


def _fm(text):
    fm = {}
    if text.startswith("---"):
        for line in text[3:text.find("\n---", 3)].splitlines():
            m = re.match(r"^([\w-]+):\s*(.*)$", line)
            if m:
                fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def _proj(link):
    m = re.search(r"\[\[([^\]|#]+)", link or "")
    return m.group(1).split("/")[-1].strip() if m else ""


def _media_dirs(v):
    for root in ROOTS:
        base = v / root
        if not base.is_dir():
            continue
        for top in base.iterdir():
            if not top.is_dir():
                continue
            for d in [top / "Output", *(top / "Output").glob("*/"), top / "media" / "scenes" / "cut"]:
                if d.is_dir() and "туршилт" not in d.name:
                    yield top, d


def feed(vault, n_tasks=40):
    v = Path(vault)
    tasks, mention = [], {}
    tdir = v / "01-GTD" / "Tasks"
    files = sorted(tdir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True) if tdir.is_dir() else []
    for p in files[:200]:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        fm = _fm(t[:1500])
        if fm.get("private") == "true" or fm.get("type") != "task":
            continue
        pr = _proj(fm.get("project"))
        if pr:
            for m in re.findall(r"\[\[(?:04-Resources/Research/)?([^\]|#/]+)", t):
                mention.setdefault(m.strip(), pr)
            mention.setdefault("stem:" + p.stem.split(" - ")[0].strip().lower(), pr)
        if len(tasks) < n_tasks:
            tasks.append({"id": p.relative_to(v).as_posix(), "title": p.stem, "date": fm.get("date", ""), "status": fm.get("status", ""),
                          "owner": fm.get("owner", ""), "project": pr, "mtime": p.stat().st_mtime})
    media = []
    for top, d in _media_dirs(v):
        fs = sorted([p for p in d.iterdir() if p.suffix.lower() in IMG or p.suffix.lower() in VID], key=lambda p: p.stat().st_mtime, reverse=True)[:PER_DIR]
        pr = top.name if top.parent.name == "02-Projects" else (mention.get(top.name) or mention.get("stem:" + top.name.split(" - ")[0].strip().lower()) or top.name)
        for p in fs:
            media.append({"src": "/api/feed/file?p=" + quote(p.relative_to(v).as_posix()), "name": p.stem, "kind": "video" if p.suffix.lower() in VID else "image",
                          "project": pr, "from": top.name, "mtime": p.stat().st_mtime})
    media.sort(key=lambda m: m["mtime"], reverse=True)
    by = {}
    for t in tasks:
        by.setdefault(t["project"] or "Төсөлгүй", {"tasks": [], "media": []})["tasks"].append(t)
    for m in media[:160]:
        by.setdefault(m["project"], {"tasks": [], "media": []})["media"].append(m)
    last = lambda g: max([x["mtime"] for x in g["tasks"] + g["media"]] or [0])
    return {"projects": [{"name": k, **g} for k, g in sorted(by.items(), key=lambda kv: -last(kv[1]))]}


def media_file(vault, rel):
    v = Path(vault).resolve()
    p = (v / rel).resolve()
    ext = p.suffix.lower()
    if not any((v / r).resolve() in p.parents for r in ROOTS) or ext not in {**IMG, **VID} or not p.is_file():
        raise FeedError("файл алга")
    return p, {**IMG, **VID}[ext]
