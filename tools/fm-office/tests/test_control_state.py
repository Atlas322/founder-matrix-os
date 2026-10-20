"""Удирдлагын өрөө: транскриптээс төлөв, tool дараалал, subagent (itge.e 2026-10-20)."""
import json, sys, time, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import control_state as cs  # noqa: E402


def L(*items):
    return [json.dumps(i) for i in items]


def use(i, name, inp, typ="assistant"):
    return {"type": typ, "timestamp": "2026-01-01T10:00:00Z", "message": {"content": [{"type": "tool_use", "id": i, "name": name, "input": inp}], "usage": {"input_tokens": 10, "output_tokens": 5}}}


def res(i, err=False):
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": i, "is_error": err}]}}


class Control(unittest.TestCase):
    def test_needs_you(self):
        tr = cs.parse_transcript(L(use("a", "Read", {"file_path": "x.md"}), res("a"),
                                   use("b", "AskUserQuestion", {"questions": [{"question": "Аль өнгө?"}]})))
        self.assertEqual(cs.state_of({}, tr, time.time()), "needs_you")
        self.assertEqual(tr["pending"][0]["arg"], "Аль өнгө?")
        self.assertEqual(tr["tokens"], 30)

    def test_shell_and_error(self):
        tr = cs.parse_transcript(L(use("a", "Edit", {"file_path": "y"}), res("a", True), use("b", "Bash", {"command": "pytest"})))
        self.assertTrue(tr["tools"][0]["error"])
        self.assertEqual(cs.state_of({"lastActivityAt": time.time() * 1000}, tr), "shell")

    def test_subagent_and_idle(self):
        tr = cs.parse_transcript(L(use("s", "Agent", {"subagent_type": "Explore", "description": "find repos"}), res("s")))
        self.assertEqual(tr["subagents"][0]["state"], "done")
        self.assertEqual(cs.state_of({"lastActivityAt": 0}, tr, time.time()), "idle")

    def test_awaiting_flag(self):
        self.assertEqual(cs.state_of({"interruptedAwaitingPerson": {"x": 1}}, cs.parse_transcript([])), "needs_you")


if __name__ == "__main__":
    unittest.main()
