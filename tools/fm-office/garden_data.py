"""Zen цэцэрлэгийн барилгууд = vault-ийн PARA. build(vault) → {"projects", "areas", "inbox", "archive"}.

projects: 02-Projects/<нэр>/<нэр>.md-ийн `status` (Archive-ийг алгасна) — идэвхтэй нь эхэнд
areas   : 03-Areas/ доорх хавтсууд
inbox   : 01-GTD/Inbox/*.md — тоо + сүүлийн 8 гарчиг
archive : 99-Archive/ доорх хавтасны тоо
goals   : 03-Areas/Goals/**.md нэрс (хүслийн хад)
"""
import re
from pathlib import Path

ORDER = {"active": 0, "planning": 1, "ongoing": 1, "on-hold": 2}


def _status(md):
    try:
        head = md.read_text(encoding="utf-8", errors="ignore")[:3000]
    except OSError:
        return ""
    m = re.search(r"^status:\s*\"?([\w-]+)", head, re.M) if head.startswith("---") else None
    return m.group(1).lower() if m else ""


def build(vault):
    v = Path(vault)
    projects = []
    for d in sorted((v / "02-Projects").glob("*/")):
        if d.name.startswith((".", "_")):
            continue
        st = _status(d / f"{d.name}.md")
        if st in ("archive", "archived", "completed", "done"):
            continue
        projects.append({"name": d.name, "status": st or "—"})
    projects.sort(key=lambda p: (ORDER.get(p["status"], 3), p["name"]))
    areas = [d.name for d in sorted((v / "03-Areas").glob("*/")) if not d.name.startswith((".", "_"))]
    inbox = sorted((v / "01-GTD/Inbox").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    archive = [d for d in (v / "99-Archive").glob("*/") if not d.name.startswith(".")]
    goals = [p.stem for p in sorted((v / "03-Areas/Goals").rglob("*.md")) if not p.name.startswith(("_", "."))][:24]
    return {"goals": goals, "projects": projects, "areas": areas, "inbox": {"count": len(inbox), "recent": [p.stem for p in inbox[:8]]},
            "archive": len(archive)}
