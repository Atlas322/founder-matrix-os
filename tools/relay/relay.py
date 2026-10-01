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
GROUPS = ["tasks", "projects", "areas", "resources", "research", "development", "archive"]
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
        hook = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
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


def _full_sid(sid):
    if len(sid) >= 36: return sid
    hits = sorted((Path.home() / ".claude" / "projects").glob(f"*/{sid}*.jsonl"), key=lambda p: p.stat().st_mtime)
    return hits[-1].stem if hits else sid

def cmd_register(name, group, sid, project=None):
    sid = _full_sid(sid)
    group = group.lower().lstrip("@")
    assert group in GROUPS, f"group ∈ {GROUPS}"
    git("pull", "-q", "--rebase", "--autostash")
    reg = load(REG, {"sessions": {}})
    keep = {k: v for k, v in reg["sessions"].get(sid, {}).items() if k in ("project", "title", "private")}
    reg["sessions"][sid] = {**keep, "name": name, "group": group, "device": DEVICE,
                            "host": socket.gethostname(), "since": datetime.date.today().isoformat()}
    if project: reg["sessions"][sid]["project"] = project
    if "--private" in sys.argv: reg["sessions"][sid]["private"] = True
    if "--title" in sys.argv: reg["sessions"][sid]["title"] = sys.argv[sys.argv.index("--title") + 1]
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
import urllib.request, urllib.error
API = "https://discord.com/api/v10"
DTOKEN_F = Path.home() / ".fmos_discord_token"
DCFG = RELAY / "discord.json"

def dapi(method, path, body=None):
    req = urllib.request.Request(API + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bot " + DTOKEN_F.read_text().strip(), "Content-Type": "application/json",
                 "User-Agent": "FMOS-relay (https://github.com/rollingbd/founder-matrix-os, 1)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            if e.code in (429, 502, 503) and attempt < 4:
                try: wait = float(json.loads(e.read() or b"{}").get("retry_after", 2))
                except Exception: wait = 2
                time.sleep(min(wait + 0.5, 30)); continue
            raise

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
    names = ["org"] + ([chmap().get(sid, chname(me))] if me else [])
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
    if me and me.get("project") and event == "SessionStart":
        sf = REPO / "state" / f"{me['project']}.md"
        if sf.exists():
            t = sf.read_text(encoding="utf-8"); now = t.split("## ТҮҮХ")[0].strip()
            hist = [l for l in t.split("## ТҮҮХ")[-1].strip().splitlines() if l.startswith("- ")][-5:]
            NL = chr(10)
            out.insert(0, f"### 🏃 baton · {me['project']}{NL}{now}{NL}{NL}Сүүлийн түүх:{NL}" + NL.join(hist))
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


def d_watch(sid, every=20):
    """Continuous: print one line per new Discord message for this session (own messages skipped)."""
    reg = load(REG, {"sessions": {}}); me = reg["sessions"].get(sid)
    names = ["org"] + ([chmap().get(sid, chname(me))] if me else [])
    tag = f"[{me['name']}]" if me else None
    st = load(STATE, {}); ch = dchannels(st); save(STATE, st)
    last = {}
    for n in names:
        lm = dapi("GET", f"/channels/{ch[n]}/messages?limit=1") if n in ch else []
        last[n] = lm[0]["id"] if lm else "0"
    while True:
        time.sleep(every)
        for n in names:
            if n not in ch: continue
            try: msgs = sorted(dapi("GET", f"/channels/{ch[n]}/messages?after={last[n]}&limit=20"), key=lambda m: int(m["id"]))
            except Exception as e: print(f"[watch error] {e}", flush=True); continue
            for m in msgs:
                last[n] = m["id"]
                if tag and m["content"].startswith(tag): continue
                who = m["author"].get("global_name") or m["author"]["username"]
                print(f"#{n} · {who}: " + m["content"].replace("\n", " ⏎ ")[:600], flush=True)


def _last_turn(tp):
    user = asst = ""
    try:
        for line in open(tp, encoding="utf-8", errors="ignore"):
            try: j = json.loads(line)
            except Exception: continue
            m = j.get("message") or {}
            c = m.get("content")
            txt = c if isinstance(c, str) else "\n".join(x.get("text", "") for x in (c or []) if isinstance(x, dict) and x.get("type") == "text")
            if not txt.strip(): continue
            if j.get("type") == "user" and not txt.startswith("<"): user, asst = txt, ""
            elif j.get("type") == "assistant": asst = txt
    except Exception: pass
    return user.strip(), asst.strip()

def d_baton(hook, push_every=300):
    """Stop hook: write state/<project>.md (ОДОО overwritten, ТҮҮХ appended); commit+push throttled."""
    sid = hook.get("session_id", ""); me = load(REG, {"sessions": {}})["sessions"].get(sid)
    if not me or not me.get("project"): return
    user, asst = _last_turn(hook.get("transcript_path", ""))
    if not asst: return
    f = REPO / "state" / f"{me['project']}.md"; f.parent.mkdir(exist_ok=True)
    old = f.read_text(encoding="utf-8") if f.exists() else ""
    hist = old.split("## ТҮҮХ", 1)[1].strip() if "## ТҮҮХ" in old else ""
    nxt = [l for l in old.split("## ТҮҮХ")[0].splitlines() if l.startswith("**Дараагийн алхам")]
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    first = asst.split("\n")[0][:140]
    now = (f"# {me['project']}\n\n## ОДОО · {ts} · {me['name']} ({DEVICE})\n"
           + (nxt[0] + "\n" if nxt else "") + f"**BD-ийн сүүлийн хүсэлт:** {user[:500]}\n\n**Хаана зогссон (сүүлийн хариу):**\n{asst[:2500]}\n")
    line = f"- {ts} · {DEVICE} · {me['name']} · {first}"
    f.write_text(now + "\n## ТҮҮХ\n" + (hist + "\n" if hist else "") + line + "\n", encoding="utf-8")
    st = load(STATE, {}); k = "_baton_push_" + me["project"]
    if time.time() - st.get(k, 0) > push_every:
        git("add", str(f)); git("commit", "-qm", f"baton {me['project']} · {me['name']} ({DEVICE})")
        git("pull", "-q", "--rebase", "--autostash"); git("push", "-q")
        st[k] = time.time(); save(STATE, st)


def d_next(text, sid):
    """Pin 'Дараагийн алхам' in state/<project>.md (kept across auto baton writes)."""
    me = load(REG, {"sessions": {}})["sessions"].get(sid)
    if not me or not me.get("project"): print("project алга"); return
    f = REPO / "state" / f"{me['project']}.md"; old = f.read_text(encoding="utf-8") if f.exists() else f"# {me['project']}\n\n## ТҮҮХ\n"
    head, _, tail = old.partition("## ТҮҮХ")
    lines = [l for l in head.splitlines() if not l.startswith("**Дараагийн алхам")]
    i = next((k + 1 for k, l in enumerate(lines) if l.startswith("## ОДОО")), len(lines))
    ts = datetime.datetime.now().strftime("%m-%d %H:%M")
    lines.insert(i, f"**Дараагийн алхам ({me['name']}, {ts}):** {text}")
    f.write_text("\n".join(lines).rstrip() + "\n\n## ТҮҮХ" + tail, encoding="utf-8")
    git("add", str(f)); git("commit", "-qm", f"baton next {me['project']}"); git("pull", "-q", "--rebase", "--autostash"); git("push", "-q")
    print("pinned")


import re as _re
def chname(v):
    """Discord channel name from the Claude app session title (same title on PC & Mac → same channel).
    Leading status emoji (🔥 📐 ⏸ ✅ …) is kept so Discord mirrors the sidebar."""
    t = (v.get("title") or v.get("project") or v["name"]).strip()
    m = _re.match(r"^([^\w\s\[\(]+)\s*", t)
    emo = m.group(1) if m else ""
    rest = t[m.end():] if m else t
    body = _re.sub(r"-+", "-", _re.sub(r"[^\w\-]+", "-", rest.lower(), flags=_re.U)).strip("-")
    return ((emo + "-") if emo else "") + body[:85]

def chmap():
    """session_id → numbered Discord channel. Same project slug on PC & Mac → ONE channel (named by the first titled session)."""
    regs = [(sid, v) for sid, v in load(REG, {"sessions": {}})["sessions"].items() if not v.get("private")]
    key = lambda v: v.get("project") or chname(v)
    first = {}
    for sid, v in regs:
        k = key(v)
        if k not in first or (v.get("title") and not first[k].get("title")): first[k] = v
    names = {}; counter = {}
    for k, v in first.items():
        base = chname(v)
        emo, _, core = base.partition("-") if not _re.match(r"^\w", base) else ("", "", base)
        if not _re.match(r"^\d", core):
            counter[v["group"]] = counter.get(v["group"], 0) + 1
            core = f"{counter[v['group']]:02d}-{core}"
        names[k] = (emo + "-" if emo else "") + core
    return {sid: names[key(v)] for sid, v in regs}

CATS = {"tasks": "01 Tasks", "projects": "02 Projects", "areas": "03 Areas", "resources": "04 Resources", "research": "05 Research", "development": "06 Development", "system": "07 System", "archive": "08 Archive"}
SYSTEM_CH = ["org", "status", "status-data", "general", "relay"]

def d_sync():
    """Discord = sidebar: category per PARA group, one channel per project slug. Never deletes — old channels → Archive."""
    gid = load(DCFG, {})["guild"]["id"]
    reg = [v for v in load(REG, {"sessions": {}})["sessions"].values() if not v.get("private")]
    allc = dapi("GET", f"/guilds/{gid}/channels")
    byname = {_re.sub(r"^\d+\s*", "", c["name"]).lower().replace("r&d", "research"): c for c in allc if c["type"] == 4}
    cats = {}
    for i, (k, name) in enumerate(CATS.items()):
        c = byname.get(k)
        if c:
            cats[k] = c["id"]
            if c["name"] != name or c.get("position") != i:
                dapi("PATCH", f"/channels/{c['id']}", {"name": name, "position": i}); print("category", name)
        else:
            cats[k] = dapi("POST", f"/guilds/{gid}/channels", {"name": name, "type": 4, "position": i})["id"]; print("category +", name)
    text = {c["name"]: c for c in allc if c["type"] == 0}
    CHF = RELAY / "channels.json"; prev = load(CHF, {})  # project → last channel name (for in-place rename)
    want = {}
    for sid, name in chmap().items():
        v = load(REG, {"sessions": {}})["sessions"][sid]
        want.setdefault(name, (v["group"], v.get("project")))
    for slug, (grp, proj) in want.items():
        parent = cats[grp if grp in CATS else "archive"]
        if slug not in text and proj and prev.get(proj) in text and prev.get(proj) not in want:
            o = prev[proj]; dapi("PATCH", f"/channels/{text[o]['id']}", {"name": slug, "parent_id": parent}); print("rename", o, "→", slug)
            text[slug] = text.pop(o); continue
        old = _re.sub(r"^\d+-", "", slug)
        if slug not in text and old not in text:  # same title, different number/group → move existing channel
            cand = [n for n in text if _re.sub(r"^\d+-", "", n) == old and n not in want]
            if cand: old = cand[0]
        if slug not in text and old in text and old not in want:
            dapi("PATCH", f"/channels/{text[old]['id']}", {"name": slug, "parent_id": parent}); print("rename", old, "→", slug)
            text[slug] = text.pop(old); continue
        if slug not in text and proj and proj in text and proj not in want:
            dapi("PATCH", f"/channels/{text[proj]['id']}", {"name": slug, "parent_id": parent}); print("rename", proj, "→", slug)
            text[slug] = text.pop(proj); continue
        if slug in text:
            if text[slug].get("parent_id") != parent:
                dapi("PATCH", f"/channels/{text[slug]['id']}", {"parent_id": parent}); print("move", slug, "→", grp)
        else:
            dapi("POST", f"/guilds/{gid}/channels", {"name": slug, "type": 0, "parent_id": parent}); print("channel +", slug, "@", grp)
            time.sleep(0.6)
    for n, c in text.items():
        if n in want: continue
        tgt = cats["system"] if n in SYSTEM_CH else cats["archive"]
        if c.get("parent_id") != tgt:
            dapi("PATCH", f"/channels/{c['id']}", {"parent_id": tgt}); print("move", n, "→", "System" if n in SYSTEM_CH else "Archive")
    save(CHF, {proj: slug for slug, (grp, proj) in want.items() if proj})
    git("add", str(CHF)); git("commit", "-qm", "relay: channels.json"); git("push", "-q")
    allc = dapi("GET", f"/guilds/{gid}/channels")
    gidx = {}
    for c in sorted([c for c in allc if c["type"] == 0], key=lambda c: (c.get("parent_id") or "", c["name"])):
        i = gidx.get(c.get("parent_id"), 0); gidx[c.get("parent_id")] = i + 1
        if c.get("position") != i: dapi("PATCH", f"/channels/{c['id']}", {"position": i}); time.sleep(0.3)
    st = load(STATE, {}); st.pop("_dch", None); save(STATE, st)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if "--sid" in a:
        i = a.index("--sid"); sid = a[i + 1]; del a[i:i + 2]
    if not a or a[0] == "inbox":
        try: hook = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
        except Exception: hook = {}
        try: return d_inbox(hook)
        except Exception as e:
            print(json.dumps({"hookSpecificOutput": {"hookEventName": hook.get("hook_event_name","UserPromptSubmit"), "additionalContext": f"[FMOS Discord] уншиж чадсангүй: {e}"}}, ensure_ascii=False)); return
    if a[0] == "register":
        pj = a[a.index("--project")+1] if "--project" in a else None
        return cmd_register(a[1], a[2], sid, pj)
    if a[0] == "send":
        return d_send(a[1], " ".join(a[2:]), sid)
    if a[0] == "gsend":  # old git transport
        return cmd_send(a[1], a[2], a[3] if len(a) > 3 else "", sid)
    if a[0] == "sync-discord":
        return d_sync()
    if a[0] == "next":
        return d_next(" ".join(a[1:]), sid)
    if a[0] == "baton":
        try: hook = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
        except Exception: return
        return d_baton(hook)
    if a[0] == "watch":
        return d_watch(sid)
    if a[0] == "who":
        for k, v in load(REG, {"sessions": {}})["sessions"].items():
            print(f"{v['name']:<24} @{v['group']:<10} {v['device']:<4} {k}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
