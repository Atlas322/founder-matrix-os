#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude-ийн амьд төлөвийг Figma bridge-ийн панел руу түлхэнэ (hook-ууд дуудна).

    figstate.py prompt      # BD хүсэлт илгээв   → «бодож байна»
    figstate.py tool        # PreToolUse(Bash)   → зөвхөн fig.py-ийн командад
    figstate.py stop        # Claude дууслаа     → «хүлээж байна»
    figstate.py say "текст" # гараар
    figstate.py plan '{"title":"...","steps":[{"id":"a","label":"...","eta":60}]}'
    figstate.py step a run|done|err ["шинэ шошго"]

Hook-ийн JSON stdin-ээр ирнэ. Bridge унтарсан бол чимээгүй гарна (timeout 2с).
Панел руу `log()`-оор бичдэг тул серверийг өөрчлөх шаардлагагүй.
"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:3055/exec"
FILE = "Second Brain"


def push(text, kind="state"):
    code = "log(%s, %s);" % (json.dumps(text, ensure_ascii=False), json.dumps(kind))
    body = json.dumps({"code": code, "timeout": 2000, "file": FILE}).encode()
    try:
        req = urllib.request.Request(body=body, url=URL, headers={"content-type": "application/json"})
        urllib.request.urlopen(req, timeout=2).read()
    except Exception:
        pass  # plugin хаалттай эсвэл сервер унтарсан — чимээгүй өнгөрнө


def stdin_json():
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "say"
    if mode == "plan":
        push("@plan " + sys.argv[2], "state")
        return
    if mode == "step":
        u = {"id": sys.argv[2], "state": sys.argv[3] if len(sys.argv) > 3 else "run"}
        if len(sys.argv) > 4:
            u["label"] = sys.argv[4]
        push("@step " + json.dumps(u, ensure_ascii=False), "state")
        return
    if mode == "say":
        push(sys.argv[2] if len(sys.argv) > 2 else "…", sys.argv[3] if len(sys.argv) > 3 else "state")
        return
    if mode == "prompt":
        push("🧠 BD-ийн хүсэлтийг уншиж, бодож байна…", "state")
        return
    if mode == "stop":
        push("⏸ бэлэн — хүлээж байна", "ok")
        return
    if mode == "tool":
        d = stdin_json()
        cmd = str((d.get("tool_input") or {}).get("command") or "")
        if "fig.py" not in cmd:
            return
        if " run" in cmd:
            push("✏️ Figma дээр зурж байна…", "run")
        elif "export" in cmd:
            push("📸 Зургийг экспортлож байна…", "state")
        # reply / comments — панел дээр аль хэдийн харагдана


if __name__ == "__main__":
    main()
