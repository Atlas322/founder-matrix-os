#!/usr/bin/env python3
"""A task finished without a claim has no `started:` - the pane then tracks no working time for it.
`done` must say so, record who finished it, and take the real start with --started."""
import datetime, re, subprocess, sys, tempfile
from pathlib import Path
P = Path(__file__).resolve().parents[1] / "plugins" / "fm"
TASK = P / "skills/task/scripts/fm_task.py"


def run(*a):
    return subprocess.run([sys.executable, *map(str, a)], capture_output=True, text=True, encoding="utf-8")


def field(vault, title, key):
    text = (vault / "01-GTD/Tasks" / (title + ".md")).read_text(encoding="utf-8")
    m = re.search(r"^%s:[ \t]*(.*)$" % key, text.split("\n---", 1)[0], re.M)
    return m.group(1).strip() if m else ""


def main():
    v = Path(tempfile.mkdtemp()) / "v"
    run(P / "scripts/fm_setup.py", v, "--member", "T")
    today = datetime.date.today().isoformat()
    by = ["--by", "Architect · PC", "--summary", "s"]
    for t in ("A", "B", "C", "D", "E"):
        run(TASK, "new", v, t, "--owner", "me", "--status", "next-action")

    a = run(TASK, "done", v, "A", *by)                       # never claimed, no --started
    b = run(TASK, "done", v, "B", *by, "--started", "00:00")  # never claimed, start given as HH:MM today
    run(TASK, "claim", v, "C", "--by", "Architect · PC")
    c_started = field(v, "C", "started")
    c = run(TASK, "done", v, "C", *by, "--started", "00:00")  # claimed: the recorded start wins
    d = run(TASK, "done", v, "D", *by, "--started", "25:99")  # not a time
    e = run(TASK, "done", v, "E", *by, "--started", "2999-01-01 10:00")  # after the finish
    a2 = run(TASK, "done", v, "A", *by, "--started", "00:00")  # backfill a finished task

    checks = [
        ("unclaimed done still completes", a.returncode == 0 and field(v, "A", "status") == "completed"),
        ("unclaimed done warns that no time was tracked", "started" in a.stdout and "⚠" in a.stdout),
        ("unclaimed done records the device that finished it", field(v, "A", "claimed") == "PC"),
        ("--started HH:MM is written as today's stamp", b.returncode == 0 and field(v, "B", "started") == today + " 00:00"),
        ("--started given: no warning", "⚠" not in b.stdout),
        ("a claimed task keeps its recorded start", c.returncode == 0 and c_started != "" and field(v, "C", "started") == c_started),
        ("a bad --started is refused, task untouched", d.returncode != 0 and field(v, "D", "status") == "next-action"),
        ("--started after the finish is refused, task untouched", e.returncode != 0 and field(v, "E", "status") == "next-action"),
        ("backfill: --started fills a finished task, completed kept",
         a2.returncode == 0 and field(v, "A", "started") == today + " 00:00" and field(v, "A", "completed") != ""),
    ]
    bad = [n for n, ok in checks if not ok]
    for n, ok in checks: print(("PASS  " if ok else "FAIL  ") + n)
    print(f"\n{len(checks) - len(bad)}/{len(checks)} passed"); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
