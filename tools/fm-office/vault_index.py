"""Vault-ийг алхаж note бүрийн frontmatter-ийг уншаад `type:`-аар ангилна (хавтас hardcode хийхгүй).

Төрөл: project / task / event / meeting / daily. Frontmatter-т type алга бол замын hint-ээр:
  …Projects/<Name>/<Name>.md → project · …/Tasks|tasks/*.md → task · …/Events|meetings/*.md → event ·
  …/Daily|daily/YYYY-MM-DD.md → daily.
Нууцлал: `finances/private`, `_trash`, `.obsidian`, `.git` хавтсыг огт нээхгүй; `private: true` note-ийг алгасна.
Хурд: зөвхөн эхний 4 KB уншина, үр дүнг 60 с cache-лэнэ (vault ~4500 note).
"""
import os, re, threading, time
from pathlib import Path

SKIP_DIRS = {".obsidian", ".git", "_trash", "node_modules", ".trash", "private"}
SKIP_PATH = re.compile(r"(^|/)finances/private(/|$)", re.I)
TYPES = {"project", "task", "event", "meeting", "daily"}
CACHE_S = 60
_cache = {}
_lock = threading.Lock()


def read_fm(path, limit=4096):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(limit)
    except OSError:
        return None, ""
    m = re.match(r"^---\r?\n(.*?)\r?\n---", head, re.S)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
            if k:
                out[k.group(1)] = k.group(2).strip().strip('"').strip("'")
    return out, head


def hint_type(rel):
    parts = rel.split("/")
    name = parts[-1][:-3]
    low = [p.lower() for p in parts[:-1]]
    if len(parts) >= 3 and parts[-2] == name and any(p.endswith("projects") for p in low):
        return "project"
    if low and low[-1] == "tasks":
        return "task"
    if low and low[-1] in ("events", "meetings"):
        return "event"
    if low and low[-1] == "daily" and re.match(r"^\d{4}-\d\d-\d\d$", name):
        return "daily"
    return None


def scan(vault):
    """[{type, path(rel posix), name, fm}] — private-гүй."""
    vault = Path(vault)
    out = []
    for root, dirs, files in os.walk(vault):
        rel_root = Path(root).relative_to(vault).as_posix()
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")
                   and not SKIP_PATH.search(f"{rel_root}/{d}".lstrip("./"))]
        for fn in files:
            if not fn.endswith(".md"):
                continue
            rel = (f"{rel_root}/{fn}" if rel_root != "." else fn)
            hint = hint_type(rel)
            fm, head = read_fm(Path(root) / fn)
            if fm is None:
                continue
            t = (fm.get("type") or "").lower()
            if t not in TYPES:
                if fm.get("type"):  # өөр төрөл зарласан бол hint-ээр дарахгүй
                    continue
                t = hint
            if not t or str(fm.get("private", "")).lower() == "true":
                continue
            h1 = re.search(r"^#\s+(.+)$", head, re.M)
            out.append({"type": t, "path": rel, "name": fn[:-3], "fm": fm, "title": (h1.group(1).strip() if h1 else fn[:-3])[:160]})
    return out


def index(vault, fresh=False):
    key = str(Path(vault).resolve())
    with _lock:
        c = _cache.get(key)
        if not fresh and c and time.time() - c[0] < CACHE_S:
            return c[1]
    data = scan(vault)
    with _lock:
        _cache[key] = (time.time(), data)
    return data


def by_type(vault, *types, fresh=False):
    return [n for n in index(vault, fresh) if n["type"] in types]


def invalidate():
    with _lock:
        _cache.clear()


def project_rooms(vault, fresh=False):
    """Төслийн өрөө болох note: <…Projects>/<Name>/<Name>.md (статус хавтас байсан ч болно), _system биш.
    → [(note, archived: bool, folder_status)] ; folder_status = хуучин 1-Active/2-Planning/3-On-hold hint."""
    out = []
    for n in by_type(vault, "project", fresh=fresh):
        parts = n["path"].split("/")
        if parts[0].startswith("_") or len(parts) < 3 or parts[-2] != n["name"]:
            continue
        anc = [q.lower() for q in parts[:-2]]
        if not any(q.endswith("projects") for q in anc):
            continue
        folder = {"1-active": "active", "2-planning": "planning", "3-on-hold": "on-hold"}.get(anc[-1], "")
        out.append((n, parts[0].lower().startswith("99"), folder))
    return out


def find_project(vault, name):
    for n, _, _ in project_rooms(vault):
        if n["name"] == name:
            return Path(vault) / n["path"]
    return None
