"""FM Office — Discord руу мессеж илгээх (зөвхөн сервер талд, relay-ийн token-оор).

Дүрэм: зөвхөн тухайн өрөөний төслийн суваг эсвэл #gtd; хоосон биш, ≤1500 тэмдэгт; UI-ийн confirm заавал;
rate-limit (10 с-д 1, цагт 20); finance/private суваг хориотой; token хэзээ ч client руу явахгүй.
"""
import json, platform, re, threading, time, urllib.request
from pathlib import Path

import discord_feed

MAX_LEN = 1500
_lock = threading.Lock()
_sent = []  # timestamps
ICON = "🍎" if platform.system() == "Darwin" else "🖥️"
DEVICE = "Mac" if platform.system() == "Darwin" else "PC"
FOOTER = f"\n-# {ICON} {DEVICE} · FM Office"


class SendError(ValueError):
    pass


def validate(req, allowed_channels, sessions=None):
    """req = {channel, text, confirm, kind?, target?} → (channel, final_text). Алдаатай бол SendError."""
    if not isinstance(req, dict):
        raise SendError("буруу хүсэлт")
    if req.get("confirm") is not True:
        raise SendError("баталгаажуулалт (confirm) алга")
    text = str(req.get("text") or "").strip()
    if not text:
        raise SendError("хоосон текст")
    if len(text) > MAX_LEN:
        raise SendError(f"текст {MAX_LEN}-аас урт")
    kind = req.get("kind") or "message"
    ch = str(req.get("channel") or "").removeprefix("#")
    if kind == "wake":
        ch = "gtd"
        tgt = next((s for s in (sessions or []) if s["id"] == req.get("target")), None)
        if not tgt:
            raise SendError("сэрээх сешн олдсонгүй")
        dev = (tgt.get("device_name") or "PC").lower()
        text = f"→ {tgt['name']} @{dev}: {text}"
    elif kind != "message":
        raise SendError("буруу төрөл")
    if discord_feed.PRIVATE_CH.search(ch):
        raise SendError("хувийн/санхүүгийн суваг хориотой")
    if ch not in allowed_channels:
        raise SendError("энэ өрөөнөөс зөвхөн төслийн суваг эсвэл #gtd руу илгээнэ")
    return ch, text


def rate_check(now=None):
    now = now or time.time()
    with _lock:
        _sent[:] = [t for t in _sent if now - t < 3600]
        if _sent and now - _sent[-1] < 10:
            raise SendError("хэт олон удаа — 10 секунд хүлээ")
        if len(_sent) >= 20:
            raise SendError("цагийн хязгаар (20) хүрлээ")
        _sent.append(now)


def discord_send(vault, channel, text):
    """Relay-тэй ижил Discord API: guild-ийн сувгийг нэрээр нь олж POST. Token зөвхөн энд уншигдана."""
    token = discord_feed.TOKEN_F.read_text(encoding="utf-8").strip()
    gid = json.loads((Path(vault) / "_system/fm/discord.json").read_text(encoding="utf-8"))["guild"]["id"]
    chans = {c["name"].removeprefix(discord_feed.BUSY): c["id"] for c in discord_feed._api(f"/guilds/{gid}/channels", token)
             if c.get("type") == 0}
    if channel not in chans:
        raise SendError(f"#{channel} суваг Discord-д алга")
    body = json.dumps({"content": text + FOOTER, "allowed_mentions": {"parse": []}}).encode()
    req = urllib.request.Request(f"{discord_feed.API}/channels/{chans[channel]}/messages", data=body, method="POST",
                                 headers={"Authorization": "Bot " + token, "Content-Type": "application/json",
                                          "User-Agent": "FM-Office (local, 1)"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read() or b"{}").get("id")


def handle(vault, req, allowed_channels, sessions, send=discord_send):
    ch, text = validate(req, allowed_channels, sessions)
    rate_check()
    mid = send(vault, ch, text)
    return {"ok": True, "channel": ch, "id": str(mid or "")}
