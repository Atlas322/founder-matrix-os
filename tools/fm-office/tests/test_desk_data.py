"""Төслийн ширээ, хурлын ширээ (itge.e 2026-10-20)."""
import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import desk_data as dd  # noqa: E402

T = """---
type: task
status: {st}
owner: "📚 Wiki"
project: "[[02-Projects/P/P]]"
raci:
  responsible: "📚 Wiki"
  accountable: itge.e
  consulted: ["🎨 Creative"]
{dep}workflow: journal
---
# x
## Шаардлага
Судалгаа хийх.
- [x] 1. Task
- [ ] 2. Эх сурвалж
- [ ] ❓ Аль эх сурвалжийг авах вэ?
"""


class Desk(unittest.TestCase):
    def test_desks_order_and_questions(self):
        with tempfile.TemporaryDirectory() as d:
            v = Path(d); (v / "01-GTD/Tasks").mkdir(parents=True)
            (v / "01-GTD/Tasks/A.md").write_text(T.format(st="in-progress", dep=""), encoding="utf-8")
            (v / "01-GTD/Tasks/B.md").write_text(T.format(st="inbox", dep='depends_on: ["[[01-GTD/Tasks/A]]"]\n'), encoding="utf-8")
            (v / "01-GTD/Tasks/C.md").write_text(T.format(st="completed", dep=""), encoding="utf-8")
            ds = dd.desks(v, [{"state": "needs_you", "ask": "Өнгө?", "title": "🎨 P › x", "cwd": "", "since_s": 60}])
            self.assertEqual(len(ds), 1); dk = ds[0]
            self.assertEqual([t["title"] for t in dk["tasks"]], ["A", "B"])
            self.assertEqual([t["level"] for t in dk["tasks"]], [0, 1])
            self.assertEqual(dk["tasks"][0]["raci"]["consulted"], "🎨 Creative")
            self.assertEqual(dk["tasks"][0]["steps"], [1, 2])
            self.assertEqual(dk["questions"][0]["text"], "Өнгө?")
            self.assertEqual(len(dk["questions"]), 3)

    def test_meeting_append(self):
        with tempfile.TemporaryDirectory() as d:
            v = Path(d)
            dd.add_issue(v, {"text": "Статус самбар хаана?"}); dd.add_issue(v, {"text": "Hook туршъя уу?"})
            m = dd.meeting(v)
            self.assertEqual([i["text"].split(" · ")[0] for i in m["items"]], ["Статус самбар хаана?", "Hook туршъя уу?"])
            with self.assertRaises(dd.DeskError):
                dd.add_issue(v, {"text": " "})


if __name__ == "__main__":
    unittest.main()
