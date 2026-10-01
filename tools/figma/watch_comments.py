#!/usr/bin/env python3
"""watch_comments.py - Figma Claude Bridge plugin-ий 💬 шинэ (хариулаагүй) комментыг 5с тутам шалгаж,
шинэ бүрийг нэг мөрөөр stdout-д хэвлэнэ (Claude Monitor-т зориулсан). Нэг комментыг нэг л удаа.
  python3 watch_comments.py [--interval 5]"""
import json, sys, time, urllib.request
URL = "http://127.0.0.1:3055/comments"
iv = float(sys.argv[sys.argv.index("--interval") + 1]) if "--interval" in sys.argv else 5
seen, down = set(), False
while True:
    try:
        with urllib.request.urlopen(URL, timeout=8) as r:
            items = json.load(r)
        if down:
            print("ℹ bridge сервер дахин холбогдлоо", flush=True); down = False
        for c in items if isinstance(items, list) else []:
            last = (c.get("replies") or [c])[-1]
            key = c.get("id", "") + ":" + str(last.get("at", c.get("at")))
            if key in seen or last.get("from") == "claude":
                continue
            seen.add(key)
            n = c.get("node") or {}
            text = (last.get("text") or c.get("text") or "").replace("\n", " ")
            print(f"💬 [{c.get('file')}] {n.get('name','?')} ({n.get('id','?')}) · thread {c.get('id')}: {text}", flush=True)
    except Exception as e:
        if not down:
            print(f"⚠ bridge сервертэй холбогдож чадсангүй ({type(e).__name__}) — node bridge/server.mjs ажиллаж байгаа эсэхийг шалга", flush=True)
            down = True
    time.sleep(iv)
