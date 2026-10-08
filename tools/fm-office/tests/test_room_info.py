import sys, tempfile, time, unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import room_info, sender  # noqa: E402


def w(p, t):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding="utf-8")


TASK = '---\ntype: task\nstatus: {st}\npriority: 🔴\ndue: {due}\nowner: "bd"\nproject: "[[02-Projects/1-Active/Project A/Project A]]"\nupdated: {upd}\n---\n# {title}\n'


class TaskBatonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        v = self.v = Path(self.tmp.name)
        w(v / "01-GTD/Tasks/a.md", TASK.format(st="next-action", due="2026-10-10", upd="2026-10-01", title="Шинэ бүтцийн task"))
        w(v / "01-GTD/Tasks/b.md", TASK.format(st="waiting", due="", upd="2026-10-01", title="Хүлээж буй"))
        w(v / "01-GTD/Tasks/c.md", TASK.format(st="completed", due="", upd="2026-10-08", title="Дууссан"))
        w(v / "01-GTD/Tasks/d.md", TASK.format(st="next-action", due="", upd="", title="Өөр төсөл").replace("Project A/Project A", "Project B/Project B"))
        w(v / "02-GTD/tasks/legacy.md", TASK.format(st="someday", due="", upd="", title="Хуучин замын task"))
        w(v / "_system/fm/state/proj-a.md",
          "# proj-a\n\n## ОДОО · 2026-10-09 10:00 · Mac-A (Mac)\n**Дараагийн алхам (Mac-A, 10-09):** deploy хийх\n"
          "**itge.e-ийн сүүлийн хүсэлт:** нууц хүсэлт\n\n**Хаана зогссон (сүүлийн хариу):**\nHeader засагдсан.\n\n## ТҮҮХ\n- x\n")
        w(v / "02-Projects/1-Active/Project A/Project A.md",
          '---\nstatus: active\nstage: "[[x/activities/Дизайн]]"\ndue: 2026-12-01\nfigma: https://figma.com/file/x\n'
          'finance:\n  - amount: 999999\nmilestones:\n  - label: MVP\n    date: 2026-11-01\n    done: false\n  - label: Kickoff\n    date: 2026-09-01\n    done: true\n---\n')
        (v / "02-Projects/1-Active/Project A/_BRAIN.md").write_text("x", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_tasks_new_and_legacy_paths(self):
        t = room_info.tasks_for(self.v, "Project A", now=datetime(2026, 10, 9))
        self.assertEqual([x["title"] for x in t["groups"]["next-action"]], ["Шинэ бүтцийн task"])
        self.assertEqual(len(t["groups"]["waiting"]), 1)
        self.assertEqual(t["groups"]["someday"][0]["title"], "Хуучин замын task")
        self.assertEqual(t["open"], 3)
        self.assertEqual(t["done_week"], 1)

    def test_baton(self):
        b = room_info.baton(self.v, "proj-a")
        self.assertEqual(b["ts"], "2026-10-09 10:00")
        self.assertEqual(b["by"], "Mac-A")
        self.assertEqual(b["next"], "deploy хийх")
        self.assertEqual(b["stopped"], "Header засагдсан.")
        self.assertNotIn("нууц", str(b))
        self.assertIsNone(room_info.baton(self.v, "missing"))

    def test_project_info_whitelist(self):
        room = {"id": "p:Project A", "project": "Project A", "kind": "project", "stage": "Дизайн", "status": "active"}
        info = room_info.project_info(self.v, room, [], [], {"proj-a"})
        self.assertEqual(info["due"], "2026-12-01")
        self.assertEqual([m["label"] for m in info["milestones"]], ["MVP", "Kickoff"])
        self.assertTrue(info["milestones"][1]["done"])
        labels = [l["label"] for l in info["links"]]
        self.assertIn("🎨 Figma", labels)
        self.assertIn("🧠 _BRAIN", labels)
        self.assertNotIn("999999", str(info))

    def test_project_note_flat_and_legacy(self):
        w(self.v / "02-Projects/Flat One/Flat One.md", "---\nstatus: planning\n---\n")
        self.assertEqual(room_info.project_note(self.v, "Flat One"), self.v / "02-Projects/Flat One/Flat One.md")
        self.assertEqual(room_info.project_note(self.v, "Project A"),
                         self.v / "02-Projects/1-Active/Project A/Project A.md")


class SendValidationTest(unittest.TestCase):
    ALLOWED = {"project-a", "gtd"}
    SESS = [{"id": "s1", "name": "📁 Project A", "device_name": "Mac"}]

    def setUp(self):
        sender._sent.clear()

    def test_rejects(self):
        V = sender.validate
        with self.assertRaises(sender.SendError):
            V({"channel": "project-a", "text": "hi"}, self.ALLOWED)  # confirm алга
        with self.assertRaises(sender.SendError):
            V({"channel": "project-a", "text": "  ", "confirm": True}, self.ALLOWED)
        with self.assertRaises(sender.SendError):
            V({"channel": "other-project", "text": "hi", "confirm": True}, self.ALLOWED)
        with self.assertRaises(sender.SendError):
            V({"channel": "business", "text": "hi", "confirm": True}, self.ALLOWED | {"business"})
        with self.assertRaises(sender.SendError):
            V({"channel": "gtd", "text": "x" * 2000, "confirm": True}, self.ALLOWED)
        with self.assertRaises(sender.SendError):
            V({"kind": "wake", "target": "nope", "text": "hi", "confirm": True}, self.ALLOWED, self.SESS)

    def test_ok_and_wake_and_mocked_send(self):
        self.assertEqual(sender.validate({"channel": "#project-a", "text": " hi ", "confirm": True}, self.ALLOWED), ("project-a", "hi"))
        ch, txt = sender.validate({"kind": "wake", "target": "s1", "text": "эхэл", "confirm": True}, self.ALLOWED, self.SESS)
        self.assertEqual((ch, txt), ("gtd", "→ 📁 Project A @mac: эхэл"))
        calls = []
        r = sender.handle("v", {"channel": "gtd", "text": "hi", "confirm": True}, self.ALLOWED, [],
                          send=lambda v, c, t: calls.append((c, t)) or "123")
        self.assertEqual(r, {"ok": True, "channel": "gtd", "id": "123"})
        self.assertEqual(calls, [("gtd", "hi")])
        with self.assertRaises(sender.SendError):  # rate limit: 10 с-д 1
            sender.handle("v", {"channel": "gtd", "text": "hi2", "confirm": True}, self.ALLOWED, [], send=lambda *a: "1")
        self.assertTrue(sender.FOOTER.endswith("· FM Office"))


if __name__ == "__main__":
    unittest.main()
