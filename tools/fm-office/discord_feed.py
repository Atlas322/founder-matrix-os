"""FM Office — relay Discord-оос сешн хоорондын яриаг уншина (зөвхөн сервер талд).

Token (~/.fmos_discord_token) болон Discord-ийн түүхий JSON хэзээ ч browser руу явахгүй:
энд зөвхөн {from, to, type, text(≤80), ts} үйл явдал болгож буцаана.

Суваг: _system/fm/channels.json (project slug → channel нэр) + discord.json (guild id).
Нууцлал: business / personal / 💰 / finance / санхүү сувгийг огт уншихгүй; private сешн агентын жагсаалтад
байхгүй тул тааралгүй үлдэж, ийм мессежийг алгасна.
"""
import json, re, threading, time, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://discord.com/api/v10"
TOKEN_F = Path.home() / ".fmos_discord_token"
CACHE_S = 60
LIMIT = 50
WINDOW_H = 24
TEXT_MAX = 80
HUMAN_ID = "itgee"
PRIVATE_CH = re.compile(r"business|personal|💰|finance|санхүү|private|хувийн", re.I)
BUSY = "🟢"

DEV = {"pc": "PC", "mac": "Mac", "🖥️": "PC", "🖥": "PC", "🍎": "Mac"}
# «-# 🖥️ PC · 🏛️ Architect»  /  «🍎 Mac · 📥 GTD» (мөрийн эхэнд эсвэл төгсгөлд)
FOOTER_RE = re.compile(r"^(?:-#\s*)?(?:🖥️|🖥|🍎)?\s*(PC|Mac)\s*·\s*(.+?)\s*$", re.I | re.M)
# «🖥️ [Creative Director · PC]» (хуучин prefix)
PREFIX_RE = re.compile(r"^\s*(?:🖥️|🖥|🍎)?\s*\[([^\]·]+?)\s*·\s*(PC|Mac)\]\s*", re.I)
# хаяглалт: «→ PC (Architect)», «→ Mac @mac», «for pc», «@architect»
ARROW_RE = re.compile(r"→\s*(PC|Mac)?\s*(?:\(([^)]+)\))?\s*(?:@(\w[\w-]*))?", re.I)
FOR_RE = re.compile(r"\bfor\s*(mac|pc)\b", re.I)
AT_RE = re.compile(r"@([\w][\w.-]*)", re.U)


def norm(s):
    return re.sub(r"[^\w]+", "", str(s or "").lower())


def strip_md(s):
    s = re.sub(r"<[@#!&]*\d+>", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"[*_`~>|]+", "", s)
    return re.sub(r"\s+", " ", s).strip()


def match_agent(label, agents, device=None, aliases=None):
    """Нэр/гарчиг/дүр/project-оор агент олно; device өгвөл тэрийг илүүд үзнэ."""
    n = norm(label)
    if not n:
        return None
    alias = norm((aliases or {}).get(label.strip().lower(), ""))
    cands = []
    for a in agents:
        if a.get("human"):
            continue
        keys = {norm(a["name"]), norm(a["title"]), norm(a.get("role")), norm(a["project"])}
        keys.discard("")
        if n in keys or (alias and alias in keys) or any(len(n) >= 4 and (n in k or k in n) for k in keys if len(k) >= 4):
            cands.append(a)
    if device:
        dc = [a for a in cands if a.get("device_name") == device]
        cands = dc or cands
    return cands[0]["id"] if cands else None


def parse_message(m, channel_name, owners, agents, aliases=None, human_names=("bd", "itge.e", "itgee")):
    """Нэг Discord мессеж → яриа эсвэл None. owners = энэ сувгийн эзэн агентууд."""
    if PRIVATE_CH.search(channel_name or ""):
        return None
    raw = m.get("content") or ""
    if not raw.strip():
        return None
    author = m.get("author") or {}
    text, src, dev = raw, None, None
    if not author.get("bot") or norm(author.get("username")) in {norm(h) for h in human_names}:
        src = HUMAN_ID
    else:
        bot_dev = "Mac" if "mac" in str(author.get("username", "")).lower() else "PC"
        fm = None
        for fm in FOOTER_RE.finditer(raw):
            pass  # сүүлийн footer мөр
        pm = PREFIX_RE.match(raw)
        if fm:
            dev = DEV.get(fm.group(1).lower(), bot_dev)
            src = match_agent(fm.group(2), agents, dev, aliases)
            text = raw[:fm.start()] + raw[fm.end():]
        elif pm:
            dev = DEV.get(pm.group(2).lower(), bot_dev)
            src = match_agent(pm.group(1), agents, dev, aliases)
            text = raw[pm.end():]
        else:
            dev = bot_dev
            same = [a for a in owners if a.get("device_name") == dev] or owners
            src = same[0]["id"] if same else None
        if not src:
            return None  # танигдаагүй/private сешн → алгас
    text = strip_md(text)
    # хаяглалт
    dst = None
    am = ARROW_RE.search(text)
    if am and (am.group(1) or am.group(2) or am.group(3)):
        d = DEV.get((am.group(1) or "").lower())
        name = am.group(2) or (am.group(3) if am.group(3) and am.group(3).lower() not in ("pc", "mac") else None)
        d = d or DEV.get((am.group(3) or "").lower())
        if name:
            dst = match_agent(name, agents, d, aliases)
        elif d:
            same = [a for a in owners if a.get("device_name") == d and a["id"] != src]
            dst = same[0]["id"] if same else None
    if not dst:
        fm2 = FOR_RE.search(text)
        if fm2:
            d = DEV[fm2.group(1).lower()]
            same = [a for a in owners if a.get("device_name") == d and a["id"] != src]
            dst = same[0]["id"] if same else None
    if not dst:
        for at in AT_RE.findall(text):
            if at.lower() in ("pc", "mac", "all", "everyone", "here"):
                continue
            dst = match_agent(at, agents, None, aliases)
            if dst and dst != src:
                break
            dst = None
    if not dst:
        if src == HUMAN_ID:  # itge.e бичсэн → сувгийн эзэн (ажиллаж буйг нь илүүд)
            o = sorted(owners, key=lambda a: a.get("state") != "working")
            dst = o[0]["id"] if o else None
        else:
            dst = HUMAN_ID if any(a["id"] == src for a in owners) else (owners[0]["id"] if owners else HUMAN_ID)
    if dst == src:
        dst = HUMAN_ID if src != HUMAN_ID else None
    t = text.lstrip()
    typ = "🙋" if t.startswith("🙋") else "✅" if t.startswith("✅") else "itge.e" if src == HUMAN_ID else "Discord"
    if len(text) > TEXT_MAX:
        text = text[:TEXT_MAX - 1].rstrip() + "…"
    try:
        ts = datetime.fromisoformat(m["timestamp"]).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except (KeyError, ValueError, TypeError):
        ts = ""
    return {"id": str(m.get("id", "")), "ts": ts, "from": src, "to": dst,
            "type": typ, "text": text, "channel": (channel_name or "").removeprefix(BUSY)}


# ---------- Discord-оос татах (cache 60 с) ----------
_cache = {"t": 0.0, "data": [], "chan": {}, "chan_t": 0.0}
_lock = threading.Lock()


def _api(path, token):
    req = urllib.request.Request(API + path, headers={"Authorization": "Bot " + token,
                                                      "User-Agent": "FM-Office (local, 1)"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read() or b"null")


def fetch(vault, agents, aliases=None, now=None, wait=False):
    """Сүүлийн 24 цагийн (≤50) яриа. Хуучирсан бол арын thread-ээр шинэчилж, одоогийн cache-ийг шууд буцаана
    (Discord-ийн олон суваг ~10 с тул /api/state-ийг хүлээлгэхгүй). Token эсвэл сүлжээ алга бол []."""
    if not TOKEN_F.is_file():
        return []
    if time.time() - _cache["t"] >= CACHE_S and _lock.acquire(blocking=False):
        _cache["t"] = time.time()
        th = threading.Thread(target=_refresh, args=(vault, agents, aliases, now), daemon=True)
        th.start()
        if wait:
            th.join()
    return _cache["data"]


def _refresh(vault, agents, aliases, now):
    try:
        token = TOKEN_F.read_text(encoding="utf-8").strip()
        fm = Path(vault) / "_system" / "fm"
        gid = json.loads((fm / "discord.json").read_text(encoding="utf-8"))["guild"]["id"]
        chmap = json.loads((fm / "channels.json").read_text(encoding="utf-8"))  # slug → channel name
        if time.time() - _cache["chan_t"] > 3600:
            _cache["chan"] = {c["name"].removeprefix(BUSY): c["id"] for c in _api(f"/guilds/{gid}/channels", token)
                              if c.get("type") == 0}
            _cache["chan_t"] = time.time()
        byname = _cache["chan"]
        watch = {}  # channel id → (name, owners)
        for slug, cname in chmap.items():
            if PRIVATE_CH.search(cname) or PRIVATE_CH.search(slug) or cname not in byname:
                continue
            owners = [a for a in agents if a["project"] == slug and not a.get("human")]
            watch[byname[cname]] = (cname, owners)
        if "gtd" in byname and byname["gtd"] not in watch:
            watch[byname["gtd"]] = ("gtd", [a for a in agents if a["project"] == "area"])
        try:
            for t in _api(f"/guilds/{gid}/threads/active", token).get("threads", []):
                if t.get("parent_id") in watch and not PRIVATE_CH.search(t.get("name", "")):
                    watch[t["id"]] = watch[t["parent_id"]]
        except Exception:
            pass
        since = (now or datetime.now(timezone.utc)) - timedelta(hours=WINDOW_H)
        out = []
        for cid, (cname, owners) in watch.items():
            try:
                msgs = _api(f"/channels/{cid}/messages?limit=20", token) or []
            except Exception:
                continue
            for m in msgs:
                try:
                    if datetime.fromisoformat(m["timestamp"]) < since:
                        continue
                except (KeyError, ValueError):
                    continue
                ev = parse_message(m, cname, owners, agents, aliases)
                if ev:
                    out.append(ev)
        out.sort(key=lambda e: e["ts"])
        _cache["data"] = out[-LIMIT:]
    except Exception:
        pass  # сүлжээ унасан → өмнөх cache хэвээр
    finally:
        _lock.release()
