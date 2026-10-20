"""Удирдлагын өрөө (agent office) — Claude Code-ийн сешнүүдийн төлөв ба agent tree (шат 1, зөвхөн унших).

Эх (бүгд локал, тохиргоо өөрчлөхгүй):
  Claude апп-ын сешн файл  <claude-code-sessions>/*/*/local_*.json  → title, model, isArchived, spawnedFrom (эцэг),
                                                                       lastActivityAt, cliSessionId
  Транскрипт              ~/.claude/projects/*/<cliSessionId>.jsonl  → сүүлийн tool-ууд, хариугүй tool_use,
                                                                       subagent (Agent/Task tool)
Төлөв (Habblaud-ийн санаа, «чамайг хүлээж байна» хамгийн чухал):
  needs_you  хариугүй AskUserQuestion / ExitPlanMode, эсвэл апп «interruptedAwaitingPerson»
  shell      хариугүй Bash (тест, build ажиллаж байна)
  working    сүүлийн 90 с-д бичигдсэн
  idle       бусад
🔒 Finance (гарчиг эсвэл өвөг нь 🔒/💼/finance) — агуулгыг уншихгүй, «хаалттай» л.
"""
import json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "plugins" / "fm" / "tools" / "relay"))
try:
    import fmconfig  # noqa: E402
except Exception:  # pragma: no cover
    fmconfig = None

ASK_TOOLS = {"AskUserQuestion", "ExitPlanMode"}
SHELL_TOOLS = {"Bash", "PowerShell"}
AGENT_TOOLS = {"Agent", "Task"}
BUSY_S = 90
TAIL_BYTES = 400_000
PRIVATE = re.compile(r"🔒|💼|finance|санхүү", re.I)
ROUTINE = re.compile(r"harvester|өглөөний тойм|долоо хоногийн тойм", re.I)   # fm_sidebar-ийн ROUTINE-тай ижил


def app_dir():
    try:
        return Path(fmconfig.claude_app_sessions_dir())
    except Exception:
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude-code-sessions"


def _tail_lines(p, n=TAIL_BYTES):
    try:
        with open(p, "rb") as f:
            f.seek(0, 2); size = f.tell(); f.seek(max(0, size - n))
            data = f.read().decode("utf-8", "ignore")
    except OSError:
        return []
    lines = data.splitlines()
    return lines[1:] if size > n else lines


def _short(v, n=90):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = re.sub(r"\s+", " ", s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _arg(name, inp):
    inp = inp or {}
    for k in ("description", "command", "file_path", "pattern", "query", "url", "prompt", "skill", "to"):
        if inp.get(k):
            return _short(inp[k])
    if name in ASK_TOOLS:
        q = (inp.get("questions") or [{}])[0]
        return _short(q.get("question") or inp.get("plan") or "")
    return _short(inp, 60)


def parse_transcript(lines, now=None):
    """jsonl мөрүүд → {tools: [...сүүлийн 12], pending: {id: tool}, subagents: [...], tokens, last_ts, last_text}."""
    now = now or time.time()
    tools, pending, subs, results = [], {}, [], set()
    tokens, last_ts, last_text = 0, 0.0, ""
    for ln in lines:
        try:
            j = json.loads(ln)
        except ValueError:
            continue
        ts = j.get("timestamp")
        if ts:
            try:
                last_ts = max(last_ts, time.mktime(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) - time.timezone)
            except ValueError:
                pass
        m = j.get("message") or {}
        u = m.get("usage") or {}
        tokens += int(u.get("input_tokens") or 0) + int(u.get("output_tokens") or 0)
        content = m.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use":
                name = c.get("name", "?"); inp = c.get("input") or {}
                rec = {"id": c.get("id"), "tool": name, "arg": _arg(name, inp), "error": False}
                tools.append(rec); pending[c.get("id")] = rec
                if name in AGENT_TOOLS:
                    subs.append({"id": c.get("id"), "name": inp.get("subagent_type") or "subagent",
                                 "task": _short(inp.get("description") or inp.get("prompt") or "", 80),
                                 "model": inp.get("model") or "", "state": "working"})
            elif c.get("type") == "tool_result":
                tid = c.get("tool_use_id"); results.add(tid); rec = pending.pop(tid, None)
                if rec and c.get("is_error"):
                    rec["error"] = True
                for s in subs:
                    if s["id"] == tid:
                        s["state"] = "failed" if c.get("is_error") else "done"
            elif c.get("type") == "text" and j.get("type") == "assistant":
                last_text = _short(c.get("text", ""), 160)
    return {"tools": tools[-12:], "pending": list(pending.values()), "subagents": subs[-12:],
            "tokens": tokens, "last_ts": last_ts, "last_text": last_text}


def state_of(app, tr, now=None):
    now = now or time.time()
    pend = [p["tool"] for p in tr["pending"]]
    if app.get("interruptedAwaitingPerson") or any(t in ASK_TOOLS for t in pend):
        return "needs_you"
    last = max(tr["last_ts"], (app.get("lastActivityAt") or 0) / 1000)
    if any(t in SHELL_TOOLS for t in pend) and now - last < 3600:
        return "shell"
    if now - last < BUSY_S:
        return "working"
    return "idle"


def _transcripts():
    root = Path.home() / ".claude" / "projects"
    return {p.stem: p for p in root.glob("*/*.jsonl")} if root.is_dir() else {}


def build(now=None, include_archived=False):
    now = now or time.time()
    trs = _transcripts()
    apps = {}
    for f in app_dir().glob("*/*/local_*.json"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if j.get("isArchived") and not include_archived:
            continue
        apps[j.get("sessionId")] = j

    def private(sid, seen=()):
        a = apps.get(sid)
        if not a or sid in seen:
            return False
        if PRIVATE.search(a.get("title") or ""):
            return True
        par = (a.get("spawnedFrom") or {}).get("sessionId")
        return private(par, seen + (sid,)) if par else False

    sessions = []
    for sid, a in apps.items():
        priv = private(sid)
        tp = trs.get(a.get("cliSessionId") or "")
        tr = parse_transcript(_tail_lines(tp)) if (tp and not priv) else {"tools": [], "pending": [], "subagents": [], "tokens": 0, "last_ts": 0, "last_text": ""}
        st = state_of(a, tr, now)
        last = max(tr["last_ts"], (a.get("lastActivityAt") or 0) / 1000)
        waiting = next((p for p in tr["pending"] if p["tool"] in ASK_TOOLS), None)
        sessions.append({
            "id": sid, "title": a.get("title") or "?", "model": a.get("model") or "", "cwd": "" if priv else (a.get("cwd") or ""),
            "parent": (a.get("spawnedFrom") or {}).get("sessionId"),
            "state": st, "private": priv, "since_s": int(now - last) if last else None,
            "turns": a.get("completedTurns") or 0, "routine": bool(ROUTINE.search(a.get("title") or "")),
            "tokens": 0 if priv else tr["tokens"],
            "tools": [] if priv else tr["tools"],
            "ask": None if priv else (waiting["arg"] if waiting else None),
            "subagents": [] if priv else tr["subagents"],
            "last_text": "" if priv else tr["last_text"] or _short(a.get("lastTurnReport") or "", 160),
        })
    ids = {s["id"] for s in sessions}
    for s in sessions:
        if s["parent"] not in ids:
            s["parent"] = None
    order = {"needs_you": 0, "shell": 1, "working": 2, "idle": 3}
    sessions.sort(key=lambda s: (order[s["state"]], s["since_s"] if s["since_s"] is not None else 1e12))
    counts = {k: sum(1 for s in sessions if s["state"] == k) for k in order}
    return {"generated": int(now), "counts": counts, "total": len(sessions),
            "tokens": sum(s["tokens"] for s in sessions), "sessions": sessions}


if __name__ == "__main__":
    d = build()
    print(json.dumps({k: d[k] for k in ("counts", "total", "tokens")}, ensure_ascii=False))
    for s in d["sessions"][:15]:
        print(s["state"], s["since_s"], s["title"], "←", s["parent"], s["ask"] or "", len(s["subagents"]))
