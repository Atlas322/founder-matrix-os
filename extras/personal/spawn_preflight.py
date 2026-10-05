#!/usr/bin/env python3
"""spawn-preflight (itge.e personal skill, NOT shipped in the fm plugin) - run BEFORE creating,
closing or re-mapping any session.

Reads the disk, not memory:
  1. project status (frontmatter is truth, not the board) + open tasks + scope contract
  2. sessions registered in <vault>/_system/fm/registry.json (role · device · title)
  3. role coverage: which roles have no bound session on this device
  4. git working tree / worktrees - only if the vault is a git repo

Usage: spawn_preflight.py <vault> [--plugin <path to plugins/fm>]
(default plugin path: <repo>/plugins/fm, i.e. two folders up from this file)
Read-only. Python 3.9+, stdlib only, macOS / Windows / Linux.
"""
import datetime
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # never write __pycache__ into the plugin folder
HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[1] / "plugins" / "fm"
if "--plugin" in sys.argv:
    _i = sys.argv.index("--plugin")
    PLUGIN = Path(sys.argv[_i + 1]).expanduser()
    del sys.argv[_i:_i + 2]
sys.path.insert(0, str(PLUGIN / "skills" / "project" / "scripts"))
sys.path.insert(0, str(PLUGIN / "skills" / "role" / "scripts"))

try:
    import fm_project  # noqa: E402
    import fm_role  # noqa: E402
except ImportError as e:  # pragma: no cover
    sys.stderr.write("preflight: sibling scripts missing (%s)\n" % e)
    sys.exit(1)

_out = fm_project._out


def git(vault: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(vault)] + list(args), capture_output=True, text=True,
                           encoding="utf-8", timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main(argv):
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252/cp437
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        _out(__doc__ or "")
        sys.exit(0 if len(argv) > 1 else 1)
    vault = Path(os.path.expanduser(argv[1]))
    if not vault.is_dir():
        fm_project._die("Vault олдсонгүй: %s" % vault)

    _out("════════ PRE-FLIGHT · %s ════════" % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    _out("")
    _out("── 1. ТӨСЛИЙН ТӨЛӨВ ── (frontmatter = үнэн, самбар биш)")
    fm_project.cmd_list(vault, [])
    _out("")

    _out("── 2. БҮРТГЭЛТЭЙ СЕШНҮҮД ── (_system/fm/registry.json)")
    reg = fm_role.load_registry(vault)
    sessions = reg.get("sessions", {})
    if not sessions:
        _out("   (хоосон — /fm:role <slug>-ээр сешнээ дүрд холбо)")
    for sid, v in sorted(sessions.items(), key=lambda kv: (str(kv[1].get("role", "")), str(kv[1].get("device", "")))):
        if not isinstance(v, dict):
            continue
        _out("   %s | %-14s | %-6s | %s%s" % (sid[:8], v.get("role") or "— дүргүй", v.get("device", "?"),
                                            v.get("title", ""), "  🔒" if v.get("private") else ""))
    _out("")

    _out("── 3. ДҮРИЙН ХАМРАЛТ ── (энэ төхөөрөмж: %s)" % fm_role.detect_device())
    device = fm_role.detect_device()
    roles = fm_role.load_roles(vault)
    for r in roles:
        bound = [s for s, v in sessions.items() if isinstance(v, dict) and v.get("role") == r["slug"]]
        here = [s for s in bound if sessions[s].get("device") == device]
        dup = " ⚠️ давхар" if len(here) > 1 else ""
        _out("   %-16s | энд %d · нийт %d%s" % (r["slug"], len(here), len(bound), dup))
    if not roles:
        _out("   (дүрийн тэмдэглэл алга — /fm:setup)")
    _out("")

    if (vault / ".git").exists():
        _out("── 4. GIT ──")
        _out(git(vault, "log", "--oneline", "-6") or "   (commit алга)")
        dirty = git(vault, "status", "--porcelain")
        _out("   цэвэр" if not dirty else "   %d файл commit хийгдээгүй" % len(dirty.splitlines()))
        wt = git(vault, "worktree", "list").splitlines()[1:]
        _out("   worktree: цэвэр" if not wt else "   ⚠️ worktree (Obsidian харахгүй):\n     " + "\n     ".join(wt))
        _out("")

    _out("════════ ДАРААХ АЛХАМ ════════")
    _out("1. Амьд сешнүүдийг ав (Claude Desktop: mcp__ccd_session_mgmt__list_sessions).")
    _out("2. [*] төсөл сешнгүй → ҮҮСГЭХ нэр дэвшигч · сешн [ ] төсөл дээр → ХААХ нэр дэвшигч.")
    _out("3. гэрээ 0/4 🔴 төсөлд ажил даалгахаас өмнө хүрээний асуулт тавь.")
    _out("4. Зөрүүг A/B/C сонголтоор үзүүл. Зөвшөөрөлгүйгээр бүү үүсгэ / бүү хаа.")


if __name__ == "__main__":
    main(sys.argv)
