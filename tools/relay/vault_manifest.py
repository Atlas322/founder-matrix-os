#!/usr/bin/env python3
"""Vault manifest + diff between PC and Mac (BD: two devices, each a full local backup).

  vault_manifest.py make <vault_dir> <device>   → state/manifest-<device>.tsv  (path, size, sha1)
  vault_manifest.py diff                       → only-PC / only-Mac / content differs  (prints, writes state/vault-diff.md)

Skips .obsidian/workspace*.json, .trash, node_modules, desktop.ini, .tmp.drive*.
"""
import hashlib, os, sys, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ST = REPO / "state"
SKIP_DIRS = {"node_modules", ".trash", "__pycache__", ".git"}
SKIP_FILES = {"desktop.ini", ".DS_Store", "workspace.json", "workspace-mobile.json"}


def sha1(p):
    h = hashlib.sha1()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def make(vault, device):
    vault = Path(vault); rows = []
    for r, ds, fs in os.walk(vault):
        ds[:] = [d for d in ds if d not in SKIP_DIRS and not d.startswith(".tmp.drive")]
        for f in fs:
            if f in SKIP_FILES or f.startswith(".tmp.drive"): continue
            p = Path(r) / f
            try: rows.append((p.relative_to(vault).as_posix(), p.stat().st_size, sha1(p)))
            except OSError: pass
    rows.sort()
    out = ST / f"manifest-{device}.tsv"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(f"# {device} {vault} {datetime.datetime.now():%Y-%m-%d %H:%M} files={len(rows)}\n")
        for r in rows: fh.write("\t".join(map(str, r)) + "\n")
    print(out, len(rows))


def load(device):
    d = {}
    for line in open(ST / f"manifest-{device}.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        p, s, h = line.rstrip("\n").split("\t"); d[p] = (int(s), h)
    return d


def diff():
    a, b = load("PC"), load("Mac")
    only_a = sorted(set(a) - set(b)); only_b = sorted(set(b) - set(a))
    chg = sorted(p for p in set(a) & set(b) if a[p][1] != b[p][1])
    dup = sorted(p for p in set(a) | set(b) if " (1)" in p)
    lines = [f"# Vault diff · {datetime.datetime.now():%Y-%m-%d %H:%M}",
             f"PC {len(a)} · Mac {len(b)} · ижил {len(set(a) & set(b)) - len(chg)}", "",
             f"## Зөвхөн PC ({len(only_a)})", *[f"- {p}" for p in only_a],
             f"## Зөвхөн Mac ({len(only_b)})", *[f"- {p}" for p in only_b],
             f"## Агуулга зөрүүтэй ({len(chg)})", *[f"- {p}" for p in chg],
             f"## '(1)' давхар ({len(dup)})", *[f"- {p}" for p in dup]]
    (ST / "vault-diff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:2]), f"| only PC {len(only_a)} · only Mac {len(only_b)} · differ {len(chg)} · (1) {len(dup)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1] == "make": make(sys.argv[2], sys.argv[3])
    else: diff()
