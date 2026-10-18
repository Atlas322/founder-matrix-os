"""Second Brain мини хот (гэр) — Номын сан ба Gallery-ийн өгөгдөл (зөвхөн уншина).

Номын сан = 04-Resources: судалгааны hub-ууд, атомын тоо, сүүлд нэмэгдсэн атомууд.
Gallery    = «Gallery - 3D вэб сайтууд» note-ийн хүснэгт (мөр бүр нэг хүрээ).
`private: true` атомыг тоолохгүй, харуулахгүй.
"""
from pathlib import Path

GALLERY_NOTE = "04-Resources/Research/FM Office 3D вэб ба motion/Output/Gallery - 3D вэб сайтууд.md"


def _private(p):
    try:
        head = p.read_text(encoding="utf-8", errors="ignore")[:600]
    except OSError:
        return True
    return "private: true" in head


def library(vault):
    res = Path(vault) / "04-Resources"
    hubs = sorted(d.name for d in (res / "Research").iterdir() if d.is_dir()) if (res / "Research").is_dir() else []
    atoms = [p for p in (res / "Atomic").rglob("*.md") if not _private(p)] if (res / "Atomic").is_dir() else []
    atoms = [p for p in atoms if p.stem[:4].isdigit()]          # «YYYY-MM-DD - …» атомууд (индекс note биш)
    recent = sorted(atoms, key=lambda p: p.stat().st_mtime, reverse=True)[:5]
    gloss = res / "glossary"
    return {
        "research": len(hubs), "hubs": hubs[-6:],
        "atoms": len(atoms),
        "decisions": sum(1 for p in atoms if "decisions" in p.parts),
        "glossary": sum(1 for _ in gloss.glob("*.md")) if gloss.is_dir() else 0,
        "recent": [p.stem for p in recent],
    }


def parse_gallery(text):
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[1].startswith("http"):
            continue
        rows.append({"name": cells[0], "url": cells[1], "tech": cells[2], "learn": cells[3]})
    return rows


def gallery(vault):
    p = Path(vault) / GALLERY_NOTE
    return parse_gallery(p.read_text(encoding="utf-8")) if p.is_file() else []


def build(vault):
    return {"library": library(vault), "gallery": gallery(vault)}
