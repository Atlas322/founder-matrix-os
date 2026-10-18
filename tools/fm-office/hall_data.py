"""Gallery hall — vault-ийн хавтсуудыг үзэх (уншина) ба YouTube-ийн highlight-аас атом бичих (шинэ файл л үүсгэнэ).

list_dir(vault, rel)  → {path, folders:[{name,path,count}], notes:[{name,path,videos}]}
write_atom(vault, req) → 04-Resources/Atomic/knowledge/<YYYY-MM-DD - гарчиг>.md (байгаа файлыг дарахгүй)
Хувийн хэсэг (finances, private: true, _trash, _system, .obsidian, 00-Soul) огт харагдахгүй.
"""
import re
import ref_data
from datetime import date, datetime
from pathlib import Path

HIDDEN = {".obsidian", "_trash", "_system", ".trash", "00-Soul", "finances", "private", ".git"}
YT = re.compile(r"https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([\w-]{11})")
ATOM_DIR = "04-Resources/Atomic/knowledge"


class HallError(ValueError):
    pass


def _safe(vault, rel):
    root = Path(vault).resolve()
    p = (root / (rel or "")).resolve()
    if p != root and root not in p.parents:
        raise HallError("vault-аас гадуур")
    if any(part in HIDDEN or part.startswith(".") for part in p.relative_to(root).parts):
        raise HallError("хаалттай хавтас")
    return root, p


def _private(p):
    try:
        return "private: true" in p.read_text(encoding="utf-8", errors="ignore")[:600]
    except OSError:
        return True


def videos(text):
    seen = []
    for v in YT.findall(text):
        if v not in seen:
            seen.append(v)
    return seen


def list_dir(vault, rel=""):
    root, p = _safe(vault, rel)
    if not p.is_dir():
        raise HallError("хавтас алга")
    folders, notes = [], []
    for c in sorted(p.iterdir(), key=lambda x: x.name):
        if c.name in HIDDEN or c.name.startswith("."):
            continue
        r = c.relative_to(root).as_posix()
        if c.is_dir():
            folders.append({"name": c.name, "path": r, "count": sum(1 for _ in c.rglob("*.md"))})
        elif c.suffix == ".md" and not _private(c):
            text = c.read_text(encoding="utf-8", errors="ignore")
            notes.append({"name": c.stem, "path": r, "videos": videos(text), **ref_data.describe(text)})
    return {"path": p.relative_to(root).as_posix() if p != root else "", "folders": folders, "notes": notes}


def _ts(sec):
    sec = int(max(0, float(sec)))
    return f"{sec // 3600}:{sec // 60 % 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60}:{sec % 60:02d}"


def _clean_title(t):
    t = re.sub(r'[\\/:*?"<>|\n\r]+', " ", str(t or "")).strip()
    return re.sub(r"\s+", " ", t)[:60].strip()


def write_atom(vault, req, today=None):
    if req.get("confirm") is not True:
        raise HallError("confirm хэрэгтэй")
    title = _clean_title(req.get("title"))
    if not title:
        raise HallError("гарчиг хоосон")
    vid = str(req.get("video") or "")
    if vid and not re.fullmatch(r"[\w-]{11}", vid):
        raise HallError("YouTube id буруу")
    hl = [h for h in (req.get("highlights") or [])[:50] if str(h.get("text", "")).strip()]
    body = str(req.get("body") or "").strip()[:6000]
    if not hl and not body:
        raise HallError("агуулга хоосон")
    home = str(req.get("home") or "").strip()
    if home:
        _safe(vault, home)
    d = (today or date.today()).isoformat()
    root = Path(vault).resolve()
    folder = root / ATOM_DIR
    folder.mkdir(parents=True, exist_ok=True)
    name, n = f"{d} - {title}", 2
    while (folder / f"{name}.md").exists():                    # байгааг дарахгүй
        name, n = f"{d} - {title} ({n})", n + 1
    url = f"https://www.youtube.com/watch?v={vid}" if vid else ""
    src = str(req.get("url") or "")                             # унших/зураг горимын эх (видео биш)
    if not url and re.fullmatch(r"https?://[^\s\"]{4,500}", src):
        url = src
    lines = ["---", f"date: {d}", f"created: {d}", "type: atomic", "kind: highlight", "status: draft",
             "confidence: stated", "source: gallery-hall", "ai-first: true", "tags: [atomic, highlight, youtube]"]
    if url:
        lines.append(f'url: "{url}"')
    if home:
        lines.append(f'up: "[[{home}]]"')
    lines += ["---", f"# {title}", "", "## For future agent",
              f"itge.e Gallery hall-д ({datetime.now():%H:%M}) бичлэг үзэж байхдаа тэмдэглэсэн. `status: draft` — Wiki fact-check хийж, холбоосыг нь баталгаажуулна.", ""]
    if body:
        lines += [body, ""]
    if hl:
        lines += ["## Highlight", ""]
        for h in hl:
            txt = str(h["text"]).strip()[:500]
            if h.get("t") is None:                                 # унших горим: цитат
                lines.append(f"- > {txt}")
                continue
            t = _ts(h["t"])
            link = f"[{t}]({url}&t={int(float(h['t']))}s)" if vid else t
            lines.append(f"- {link} — {txt}")
        lines.append("")
    lines += ["## 🔗 Холбоос — яагаад"]
    lines.append(f"- `гэр` [[{home}]] — үзэж байсан хавтас" if home else "- `гэр` [[04-Resources/Atomic/knowledge]] — Gallery hall-аас")
    if url:
        lines.append(f"- `эх` {url}")
    path = folder / f"{name}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"ok": True, "path": path.relative_to(root).as_posix()}


# ---------- Сэдвээр: reference бүр `topics: [[04-Resources/Topics/<сэдэв>]]` ----------
REF_DIR = "04-Resources/references"
KIND_ORDER = ["video", "web", "repo", "read", "image", "post", "note"]
UNTAGGED = "Ангилаагүй"


def note_topics(text):
    fm = text.split("\n---", 1)[0] if text.startswith("---") else ""
    m = re.search(r"^topics:\s*\n((?:[ \t]+-.*\n?)+)", fm, re.M) or re.search(r"^topics:\s*\[(.*)\]", fm, re.M)
    return re.findall(r"\[\[04-Resources/Topics/([^\]|#]+)", m.group(1)) if m else []


def _refs(vault):
    root = Path(vault).resolve()
    d = root / REF_DIR
    for c in sorted(d.glob("*.md")) if d.is_dir() else []:
        text = c.read_text(encoding="utf-8", errors="ignore")
        if "private: true" in text[:600] or c.stem == "References":
            continue
        info = {"name": c.stem, "path": c.relative_to(root).as_posix(), "videos": videos(text), **ref_data.describe(text)}
        yield info, (note_topics(text) or [UNTAGGED])


def topic_parents(vault):
    """Дэд сэдэв → эх сэдэв: Topics/<нэр>.md-ийн `up: [[04-Resources/Topics/<эх>]]`."""
    out = {}
    d = Path(vault) / "04-Resources/Topics"
    for f in d.glob("*.md") if d.is_dir() else []:
        m = re.search(r'^up:\s*"?\[\[04-Resources/Topics/([^\]|#]+)', f.read_text(encoding="utf-8", errors="ignore")[:800], re.M)
        if m and m.group(1) != "Topics":
            out[f.stem] = m.group(1)
    return out


def _sub_label(t, parent):
    return t[len(parent) + 3:] if t.startswith(parent + " - ") else (t.split(" - ", 1)[1] if " - " in t else t)


def topics(vault):
    par, groups, total = topic_parents(vault), {}, 0
    for info, ts in _refs(vault):
        total += 1
        seen = set()
        for t in ts:
            room = par.get(t, t)
            g = groups.setdefault(room, {"name": room, "count": 0, "kinds": {}, "subs": {}, "sample": ""})
            if t != room:
                lbl = _sub_label(t, room)
                g["subs"][lbl] = g["subs"].get(lbl, 0) + 1
            if room in seen:
                continue
            seen.add(room)
            g["count"] += 1
            g["kinds"][info["kind"]] = g["kinds"].get(info["kind"], 0) + 1
            if not g["sample"] and info["kind"] in ("video", "image", "web", "repo"):
                g["sample"] = info["path"]
    out = sorted(groups.values(), key=lambda g: (g["name"] == UNTAGGED, -g["count"]))
    return {"topics": out, "total": total}


def topic_refs(vault, name):
    """Өрөөний ref-үүд: дэд сэдвээр (хана), дотор нь төрлөөр эрэмбэлнэ."""
    par, notes = topic_parents(vault), []
    for info, ts in _refs(vault):
        hits = [t for t in ts if par.get(t, t) == name]
        if hits:
            sub = next((_sub_label(t, name) for t in hits if t != name), "")
            notes.append({**info, "sub": sub})
    notes.sort(key=lambda n: (n["sub"] == "", n["sub"], KIND_ORDER.index(n["kind"]) if n["kind"] in KIND_ORDER else 99, n["name"]))
    return {"path": "", "topic": name, "folders": [], "notes": notes}
