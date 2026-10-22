"""Хөвсгөлийн Номын сан = 04-Resources-ийн note-ууд ном болж тавиурт байрлана (зөвхөн уншина).

books(vault)      → {"shelves": [{"key", "name", "books": [{"id", "title", "date", "size"}]}]}
read(vault, rel)  → {"title", "section", "date", "tags", "body"} — `private: true` note-ийг өгөхгүй,
                    зөвхөн 04-Resources доторх .md (зам гаднаас орохгүй).
"""
import re
from pathlib import Path

ROOT = "04-Resources"
NL_DIR = "02-Projects/INAI Newsletter/Output/Journal"
IMG = (".png", ".jpg", ".jpeg", ".webp")
SHELVES = [  # (key, нэр, хавтас, glob)
    ("books", "Унших ном", "library", "*.md"),
    ("decisions", "Шийдвэр", "Atomic/decisions", "*.md"),
    ("knowledge", "Мэдлэгийн атом", "Atomic/knowledge", "*.md"),
    ("references", "Лавлагаа", "references", "*.md"),
    ("research", "Судалгаа", "Research", "*/*.md"),
    ("glossary", "Глоссари", "glossary", "*.md"),
]
MAX_PER_SHELF = 2000   # хязгааргүй шахуу (atlas 2048 нүд)


class LibraryError(ValueError):
    pass


def _head(p, n=700):
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:n]
    except OSError:
        return ""


def _private(text):
    return re.search(r"^private:\s*true", text, re.M) is not None


def _date(p):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", p.stem)
    if m:
        return m.group(1)
    import datetime
    return datetime.date.fromtimestamp(p.stat().st_mtime).isoformat()


def books(vault):
    v = Path(vault) / ROOT
    out = []
    for key, name, folder, pat in SHELVES:
        d = v / folder
        items = []
        for p in sorted(d.glob(pat)) if d.is_dir() else []:
            if p.name.startswith(("_", ".")) or _private(_head(p)):
                continue
            items.append({"id": p.relative_to(v).as_posix(), "title": re.sub(r"^\d{4}-\d{2}-\d{2}\s*-\s*", "", p.stem),
                          "date": _date(p), "size": p.stat().st_size, "tags": _tags(_head(p))})
            if key == "books":
                fm = _fm(_head(p, 1500)); items[-1].update(title=fm.get("title") or items[-1]["title"], author=fm.get("author", ""), status=fm.get("status", ""))
                if p.stem in ("Reading",): items.pop()
        items.sort(key=lambda b: b["date"], reverse=True)
        out.append({"key": key, "name": name, "count": len(items), "books": items[:MAX_PER_SHELF]})
    nl = newsletters(vault)
    out.insert(0, {"key": "newsletter", "name": "INAI Newsletter", "count": len(nl), "books": nl})
    return {"shelves": out}


def _tags(head):
    m = re.search(r"^tags:\s*\[(.*?)\]", head, re.M)
    if m:
        return [t.strip().strip("\"'") for t in m.group(1).split(",") if t.strip()][:8]
    m = re.search(r"^tags:\s*\n((?:\s*-\s*.+\n)+)", head, re.M)
    return [t.strip()[1:].strip().strip("\"'") for t in m.group(1).splitlines()][:8] if m else []


_BL = {"key": None, "idx": {}}


def backlinks(vault, rel):
    """[[холбоос]]-ын урвуу индекс: тухайн note руу заасан note-ууд (04-Resources дотор, private-гүй). mtime-аар cache."""
    base = Path(vault) / ROOT
    files = [p for p in base.rglob("*.md") if not p.name.startswith(("_", "."))]
    key = (len(files), max((p.stat().st_mtime for p in files), default=0))
    if _BL["key"] != key:
        idx = {}
        for p in files:
            try:
                t = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if _private(t[:700]):
                continue
            src = {"id": p.relative_to(base).as_posix(), "title": re.sub(r"^\d{4}-\d{2}-\d{2}\s*-\s*", "", p.stem)}
            for m in set(re.findall(r"\[\[([^\]|#]+)", t)):
                idx.setdefault(m.split("/")[-1].strip(), {})[src["id"]] = src
        _BL.update(key=key, idx=idx)
    stem = Path(rel).stem if not rel.startswith("nl:") else ""
    return [x for x in _BL["idx"].get(stem, {}).values() if x["id"] != rel][:60]


def _fm(text):
    fm = {}
    if text.startswith("---"):
        for line in text[3:text.find("\n---", 3)].splitlines():
            m = re.match(r"^([\w-]+):\s*(.*)$", line)
            if m:
                fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def _issue_dir(vault, no):
    d = Path(vault) / NL_DIR
    if not re.fullmatch(r"\d{3}", no or "") or not d.is_dir():
        raise LibraryError("дугаар олдсонгүй")
    for x in d.iterdir():
        if x.is_dir() and x.name.startswith(no + " "):
            return x
    raise LibraryError("дугаар олдсонгүй")


def _issue_files(d, no):
    htmls = sorted(d.glob("*.html"), key=lambda p: (p.name != f"{no}.html", "v0" in p.name, -p.stat().st_mtime))
    if not htmls:
        htmls = sorted(d.glob("*site*/index.html"))
    imgs = sorted([p for p in d.iterdir() if p.suffix.lower() in IMG], key=lambda p: (not re.match(rf"{no}-00", p.name), p.name))
    return (htmls[0] if htmls else None), (imgs[0] if imgs else None)


def newsletters(vault):
    d = Path(vault) / NL_DIR
    out = []
    for x in sorted(d.iterdir(), reverse=True) if d.is_dir() else []:
        m = re.match(r"(\d{3}) - (.+)", x.name)
        if not x.is_dir() or not m:
            continue
        no, title = m.groups(); html, img = _issue_files(x, no)
        meta = {}
        j = x / f"{no}.json"
        if j.is_file():
            try:
                import json; meta = json.loads(j.read_text(encoding="utf-8"))
            except ValueError:
                pass
        import datetime
        out.append({"id": f"nl:{no}", "title": f"№{int(no)} · {title}", "date": meta.get("date") or datetime.date.fromtimestamp(x.stat().st_mtime).isoformat(),
                    "size": 20000, "cover": bool(img), "html": bool(html)})
    return out


def issue_asset(vault, no, rel):
    """/nl/<no>/<rel> — дугаарын хавтас доторх файл (html-ийн зураг, css)."""
    d = _issue_dir(vault, no).resolve(); p = (d / rel).resolve()
    if d not in p.parents or not p.is_file():
        raise LibraryError("файл алга")
    import mimetypes
    return p.read_bytes(), (mimetypes.guess_type(p.name)[0] or "application/octet-stream") + ("; charset=utf-8" if p.suffix in (".html", ".css", ".js") else "")


def issue_file(vault, no, kind):
    """kind = html | cover → (bytes, content-type)."""
    d = _issue_dir(vault, no); html, img = _issue_files(d, no)
    p = html if kind == "html" else img
    if not p:
        raise LibraryError("файл алга")
    ct = "text/html; charset=utf-8" if p.suffix == ".html" else {".png": "image/png", ".webp": "image/webp"}.get(p.suffix.lower(), "image/jpeg")
    return p.read_bytes(), ct


def _safe(vault, rel):
    base = (Path(vault) / ROOT).resolve()
    p = (base / rel).resolve()
    if base not in p.parents or p.suffix != ".md" or not p.is_file():
        raise LibraryError("ном олдсонгүй")
    return p


def read(vault, rel):
    if rel.startswith("nl:"):
        no = rel[3:]; d = _issue_dir(vault, no); html, img = _issue_files(d, no)
        title = re.sub(r"^\d{3} - ", "", d.name)
        return {"title": f"№{int(no)} · {title}", "section": "INAI Newsletter", "date": "", "tags": "", "type": "newsletter",
                "html": f"/nl/{no}/" + html.relative_to(d).as_posix() if html else "", "cover": f"/api/nl?no={no}&f=cover" if img else "", "body": ""}
    p = _safe(vault, rel)
    text = p.read_text(encoding="utf-8", errors="ignore")
    if _private(text[:700]):
        raise LibraryError("хувийн note")
    fm, body = {}, text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end > 0:
            for line in text[3:end].splitlines():
                m = re.match(r"^([\w-]+):\s*(.*)$", line)
                if m:
                    fm[m.group(1)] = m.group(2).strip().strip('"')
            body = text[end + 4:].lstrip("\n")
    rel_parts = Path(rel).parts
    sec = next((name for key, name, folder, _ in SHELVES if Path(rel).as_posix().startswith(folder)), rel_parts[0])
    if Path(rel).as_posix().startswith("library"):
        fm["title"] = fm.get("title") or p.stem
    return {"title": fm.get("title") or re.sub(r"^\d{4}-\d{2}-\d{2}\s*-\s*", "", p.stem), "author": fm.get("author", ""), "section": sec, "date": _date(p),
            "tags": fm.get("tags", ""), "type": fm.get("type", ""), "body": body[:60000]}
