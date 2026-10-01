#!/usr/bin/env python3
"""Founder Matrix OS — PARA relay (session ↔ group ↔ org).

Channels (files under <repo>/relay/):
  org.md                 — every session listens
  groups/<group>.md      — tasks | projects | areas | resources | archive
  s/<name>.md            — one session's inbox

Commands:
  relay.py inbox                     hook (SessionStart / UserPromptSubmit): reads hook JSON on stdin,
                                     git pull (throttled), prints new entries as additionalContext
  relay.py register NAME GROUP       bind the current session (CLAUDE_SESSION_ID or --sid) to NAME + GROUP
  relay.py send TO "title" [body]    TO = all | @<group> | <session-name>; appends, commits, pushes
  relay.py who                       show registry
"""
import json, os, sys, subprocess, time, datetime, socket
from pathlib import Path

REPO = Path(os.environ.get("FMOS_REPO", Path(__file__).resolve().parents[2]))
RELAY = REPO / "relay"
REG = RELAY / "registry.json"
STATE = Path.home() / ".fmos_relay_state.json"   # per-machine read cursors (not in git)
GROUPS = ["tasks", "projects", "areas", "resources", "archive"]
DEVICE = os.environ.get("FMOS_DEVICE") or ("Mac" if sys.platform == "darwin" else "PC")
PULL_EVERY = 45  # seconds


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True, encoding="utf-8")


def load(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return d


def save(p, v):
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")


def pull(state):
    if time.time() - state.get("_pulled", 0) > PULL_EVERY:
        git("pull", "-q", "--rebase", "--autostash")
        state["_pulled"] = time.time()


def channels_for(sid, reg):
    me = reg.get("sessions", {}).get(sid)
    ch = [RELAY / "org.md"]
    if me:
        ch.append(RELAY / "groups" / f"{me['group']}.md")
        ch.append(RELAY / "s" / f"{me['name']}.md")
    return me, ch


def entries(path, offset):
    if not path.exists():
        return [], 0
    data = path.read_bytes()
    new = data[offset:].decode("utf-8", "ignore")
    blocks = [b.strip() for b in ("\n" + new).split("\n## ")[1:]]
    return ["## " + b for b in blocks if b], len(data)


def cmd_inbox():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        hook = {}
    sid = hook.get("session_id", "")
    event = hook.get("hook_event_name", "")
    state = load(STATE, {})
    pull(state)
    reg = load(REG, {"sessions": {}})
    me, chans = channels_for(sid, reg)
    cur = state.setdefault(sid, {})
    out = []
    for p in chans:
        key = str(p.relative_to(RELAY))
        first = key not in cur
        items, size = entries(p, cur.get(key, 0))
        if first and event != "SessionStart":
            items = []  # don't flood mid-session on first sight
        elif first:
            items = items[-5:]  # new session: last 5 per channel
        cur[key] = size
        if items:
            out.append(f"### #{key}\n" + "\n\n".join(items))
    save(STATE, state)
    who = f"{me['name']} · @{me['group']} · {DEVICE}" if me else f"бүртгэлгүй ({DEVICE}, sid {sid[:8]})"
    if not out and event != "SessionStart":
        return
    ctx = f"[FMOS relay] Энэ сешн: {who}.\n"
    if not me and event == "SessionStart":
        ctx += ("Бүртгүүлэх: `python " + str(Path(__file__)) + f" register <нэр> <{'|'.join(GROUPS)}> --sid {sid}` "
                "(BD-ийн sidebar групптэй ижил). Илгээх: `relay.py send <all|@group|нэр> \"гарчиг\" \"агуулга\"`.\n")
    ctx += "\n\n".join(out) if out else "Шинэ relay бичлэг алга."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event or "UserPromptSubmit", "additionalContext": ctx}}, ensure_ascii=False))


def cmd_register(name, group, sid):
    group = group.lower().lstrip("@")
    assert group in GROUPS, f"group ∈ {GROUPS}"
    git("pull", "-q", "--rebase", "--autostash")
    reg = load(REG, {"sessions": {}})
    reg["sessions"][sid] = {"name": name, "group": group, "device": DEVICE,
                            "host": socket.gethostname(), "since": datetime.date.today().isoformat()}
    save(REG, reg)
    (RELAY / "s").mkdir(exist_ok=True)
    git("add", str(REG))
    git("commit", "-qm", f"relay: register {name} @{group} ({DEVICE})")
    git("push", "-q")
    print(f"registered {name} @{group} {DEVICE}")


def cmd_send(to, title, body, sid):
    git("pull", "-q", "--rebase", "--autostash")
    reg = load(REG, {"sessions": {}})
    me = reg["sessions"].get(sid, {"name": f"{DEVICE}-{sid[:6] or 'bd'}", "group": "?"})
    if to in ("all", "@all", "org"):
        path = RELAY / "org.md"
    elif to.startswith("@"):
        g = to[1:].lower(); assert g in GROUPS, f"group ∈ {GROUPS}"
        path = RELAY / "groups" / f"{g}.md"
    else:
        path = RELAY / "s" / f"{to}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {ts} · {me['name']} ({DEVICE}) → {to} · {title}\n{body}\n")
    git("add", str(path))
    git("commit", "-qm", f"relay {me['name']} → {to}: {title}")
    r = git("push", "-q")
    print("sent" if r.returncode == 0 else "committed (push failed: " + r.stderr.strip() + ")")



# ── Discord transport (default): channels = Discord, no git per message ──
import urllib.request
API = "https://discord.com/api/v10"
DTOKEN_F = Path.home() / ".fmos_discord_token"
DCFG = RELAY / "discord.json"

def dapi(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bot " + DTOKEN_F.read_text().strip(), "Content-Type": "application/json",
                 "User-Agent": "FMOS-relay (https://github.com/rollingbd/founder-matrix-os, 1)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read() or b"null")

def dchannels(state):
    ch = state.get("_dch")
    if not ch or time.time() - state.get("_dch_t", 0) > 3600:
        gid = load(DCFG, {})["guild"]["id"]
        ch = {c["name"]: c["id"] for c in dapi("GET", f"/guilds/{gid}/channels") if c.get("type") == 0}
        state["_dch"], state["_dch_t"] = ch, time.time()
    return ch

def d_inbox(hook):
    sid = hook.get("session_id", ""); event = hook.get("hook_event_name", "")
    state = load(STATE, {}); reg = load(REG, {"sessions": {}})
    me = reg["sessions"].get(sid)
    names = ["org"] + ([me["group"]] if me else [])
    ch = dchannels(state); cur = state.setdefault(sid, {}); out = []
    my_tag = f"[{me['name']}]" if me else None
    for n in names:
        cid = ch.get(n)
        if not cid: continue
        last = cur.get(n)
        q = f"?limit=20" + (f"&after={last}" if last else "")
        msgs = sorted(dapi("GET", f"/channels/{cid}/messages{q}"), key=lambda m: int(m["id"]))
        if not last and event != "SessionStart": msgs = []
        elif not last: msgs = msgs[-5:]
        if msgs: cur[n] = msgs[-1]["id"]
        elif not last:
            lm = dapi("GET", f"/channels/{cid}/messages?limit=1"); cur[n] = lm[0]["id"] if lm else "0"
        lines = [f"- {m['timestamp'][11:16]} **{m['author'].get('global_name') or m['author']['username']}**: {m['content']}"
                 for m in msgs if not (my_tag and m["content"].startswith(my_tag))]
        if lines: out.append(f"### #{n}\n" + "\n".join(lines))
    save(STATE, state)
    if not out and event != "SessionStart": return
    who = f"{me['name']} · @{me['group']} · {DEVICE}" if me else f"бүртгэлгүй ({DEVICE}, sid {sid[:8]})"
    ctx = (f"[FMOS Discord] Энэ сешн: {who}. Хариу/мэдэгдэл: `python {Path(__file__)} send <org|group> \"текст\" --sid {sid}`.\n"
           + ("\n\n".join(out) if out else "Шинэ мессеж алга."))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event or "UserPromptSubmit", "additionalContext": ctx}}, ensure_ascii=False))

def d_send(to, text, sid):
    reg = load(REG, {"sessions": {}}); me = reg["sessions"].get(sid, {"name": f"{DEVICE}-{sid[:6]}"})
    state = load(STATE, {}); ch = dchannels(state); save(STATE, state)
    name = "org" if to in ("all", "@all", "org") else to.lstrip("@").lower()
    cid = ch[name]; msg = f"[{me['name']}] {text}"
    for i in range(0, len(msg), 1900):
        dapi("POST", f"/channels/{cid}/messages", {"content": msg[i:i+1900]})
    print("sent →", name)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if "--sid" in a:
        i = a.index("--sid"); sid = a[i + 1]; del a[i:i + 2]
    if not a or a[0] == "inbox":
        try: hook = json.load(sys.stdin)
        except Exception: hook = {}
        try: return d_inbox(hook)
        except Exception as e:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": hook.get("hook_event_name","UserPromptSubmit"), "additionalContext": f"[FMOS Discord] уншиж чадсангүй: {e}"}}, ensure_ascii=False)); return
    if a[0] == "register":
        return cmd_register(a[1], a[2], sid)
    if a[0] == "send":
        return d_send(a[1], " ".join(a[2:]), sid)
    if a[0] == "gsend":  # old git transport
        return cmd_send(a[1], a[2], a[3] if len(a) > 3 else "", sid)
    if a[0] == "who":
        for k, v in load(REG, {"sessions": {}})["sessions"].items():
            print(f"{v['name']:<24} @{v['group']:<10} {v['device']:<4} {k}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
