"""Удирдлагын өрөө · оффис (шат 2): төслийн ширээ ба хурлын ширээ — vault-аас (itge.e 2026-10-20).

Төслийн ширээ (төсөл бүрд): нээлттэй task-ууд RACI-тай, ажлын дарааллаар (depends_on; хоосон = зэрэг),
  ажилбарын явц («## Ажилбар» чеклист), тайлбар (task-ийн «Шаардлага»/бие-ийн эхний мөр),
  ширээн дээр үлдсэн асуулт = энэ төслийн ✋ сешнүүдийн асуулт + task доторх «- [ ] ❓ …» мөр.
Хурлын ширээ: `01-GTD/Хурлын ширээ.md` — itge.e-ийн бичсэн шийдэх асуудал (`- [ ] …`), шийдсэн нь `- [x] … → [[атом]]`.
  Бичих нь зөвхөн мөр нэмэх (append) — байгааг хэзээ ч дарахгүй.
"""
import datetime, re
from pathlib import Path

OPEN = {"inbox", "next-action", "in-progress", "waiting"}
MEET_REL = "01-GTD/Хурлын ширээ.md"
MEET_HEAD = ("---\ntype: meeting-board\ntags: [meeting]\nai-first: true\n---\n\n# Хурлын ширээ\n\n"
             "## For future agent\n\nitge.e-ийн шийдэх асуудлууд (Удирдлагын өрөөнөөс бичигддэг). Агент холбогдох асуудалд санал, "
             "сонголтоо доор нь `  - ` мөрөөр нэмнэ; itge.e шийдмэгц `- [x] … → [[шийдвэрийн атом]]`.\n\n## Асуудлууд\n")


class DeskError(ValueError):
    pass


def _fm(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    out, key = {}, None
    if not m:
        return out
    for ln in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", ln)
        if k:
            key = k.group(1); v = re.sub(r"(^|\s)#.*$", "", k.group(2)).strip() if not k.group(2).strip().startswith(("'", '"')) else k.group(2).strip()
            out[key] = v.strip('"').strip("'")
        elif key and re.match(r"^\s+-\s", ln):
            out.setdefault(key + "[]", []).append(ln.split("-", 1)[1].strip().strip('"').strip("'"))
        elif key and re.match(r"^\s+\w+:", ln):
            kk, vv = ln.strip().split(":", 1)
            out.setdefault(key + "{}", {})[kk.strip()] = ", ".join(x.strip().strip('"').strip("'") for x in vv.strip().strip("[]").split(",") if x.strip())
    return out


def _proj_name(v):
    m = re.search(r"\[\[(?:[^|\]]*/)?([^|\]/]+)(?:\|[^\]]*)?\]\]", v or "")
    return m.group(1) if m else (v or "").strip()


def _summary(body):
    m = re.search(r"##\s*Шаардлага\s*\n+(.+)", body)
    line = (m.group(1) if m else next((l for l in body.splitlines() if l.strip() and not l.startswith(("#", "---", ">", "|"))), ""))
    return re.sub(r"\s+", " ", line).strip()[:220]


def tasks(vault):
    out = []
    for f in sorted((Path(vault) / "01-GTD" / "Tasks").glob("*.md")):
        try:
            t = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        except OSError:
            continue
        fm = _fm(t)
        if fm.get("type") != "task" or fm.get("status", "").lower() not in OPEN:
            continue
        if re.search(r"🔒|private", fm.get("tags", "") + " ".join(fm.get("tags[]", []))):
            continue
        body = t.split("\n---", 2)[-1]
        steps_done = len(re.findall(r"^- \[x\] \d+\.", t, re.M)); steps_all = steps_done + len(re.findall(r"^- \[ \] \d+\.", t, re.M))
        nxt = (re.search(r"^- \[ \] (\d+\..+)$", t, re.M) or [None, ""])[1]
        raci = fm.get("raci{}", {})
        out.append({
            "path": "01-GTD/Tasks/" + f.name, "title": f.stem, "status": fm.get("status"), "owner": fm.get("owner", ""),
            "project": _proj_name(fm.get("project", "")) or "Бусад", "priority": fm.get("priority", ""),
            "raci": {k: raci.get(k, "") for k in ("responsible", "accountable", "consulted", "informed") if raci.get(k)},
            "depends_on": fm.get("depends_on[]", []) or ([fm["depends_on"]] if fm.get("depends_on") else []),
            "workflow": fm.get("workflow", ""), "steps": [steps_done, steps_all], "next_step": nxt,
            "why": _summary(body),
            "questions": re.findall(r"^- \[ \] ❓\s*(.+)$", t, re.M),
        })
    return out


def _order(ts):
    """depends_on-оор шат (level) оноох: 0 = эхлэх боломжтой; ижил шат = зэрэг."""
    names = {t["title"]: t for t in ts}
    def lvl(t, seen=()):
        deps = [_proj_name(d) or d for d in t["depends_on"]]
        deps = [names[d] for d in deps if d in names and d not in seen]
        return 0 if not deps else 1 + max(lvl(d, seen + (t["title"],)) for d in deps)
    for t in ts:
        t["level"] = lvl(t)
    return sorted(ts, key=lambda t: (t["level"], t["status"] != "in-progress", t["title"]))


def desks(vault, sessions=()):
    by = {}
    for t in tasks(vault):
        by.setdefault(t["project"], []).append(t)
    out = []
    for name, ts in by.items():
        qs = [{"from": "task", "who": t["owner"], "text": q, "task": t["title"]} for t in ts for q in t["questions"]]
        for s in sessions:
            if s.get("state") == "needs_you" and s.get("ask") and name.lower() in (s.get("cwd", "") + " " + s.get("title", "")).lower():
                qs.insert(0, {"from": "session", "who": s["title"], "text": s["ask"], "since_s": s.get("since_s")})
        out.append({"project": name, "tasks": _order(ts), "questions": qs,
                    "running": sum(1 for t in ts if t["status"] == "in-progress")})
    out.sort(key=lambda d: (-len(d["questions"]), -d["running"], d["project"] == "Бусад", d["project"]))
    return out


def meeting(vault):
    f = Path(vault) / MEET_REL
    if not f.is_file():
        return {"path": MEET_REL, "items": []}
    items, cur = [], None
    for ln in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- \[( |x)\] (.+)$", ln)
        if m:
            cur = {"done": m.group(1) == "x", "text": m.group(2), "notes": []}; items.append(cur)
        elif cur and re.match(r"^\s+- ", ln):
            cur["notes"].append(ln.strip()[2:])
    return {"path": MEET_REL, "items": items}


def add_issue(vault, req):
    text = re.sub(r"\s+", " ", str((req or {}).get("text", ""))).strip()
    if not text or len(text) > 500:
        raise DeskError("асуудлын текст 1–500 тэмдэгт байх ёстой")
    f = Path(vault) / MEET_REL
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"- [ ] {text} · _{stamp}_\n"
    if not f.exists():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(MEET_HEAD + "\n" + line, encoding="utf-8")
    else:
        with open(f, "a", encoding="utf-8") as h:   # зөвхөн нэмнэ (shared-log-append-only)
            h.write(("" if f.read_text(encoding="utf-8").endswith("\n") else "\n") + line)
    return {"ok": True, "path": MEET_REL, "added": text}
