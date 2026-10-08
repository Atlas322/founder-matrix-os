import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vault_index, calendar_data  # noqa: E402
from office_state import read_projects  # noqa: E402


def w(p, t, nl="\n"):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(t.replace("\n", nl).encode("utf-8"))


class DiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        v = self.v = Path(self.tmp.name)
        vault_index.invalidate()
        w(v / "02-Projects/Project New/Project New.md", '---\ntype: project\nstatus: active\nstage: "[[x/activities/Дизайн]]"\n---\n')
        w(v / "02-Projects/Project New/_BRAIN.md", "---\ntype: project\n---\n")  # нэр таарахгүй → өрөө биш
        w(v / "03-Projects/1-Active/Project Old/Project Old.md", "---\nstatus: active\n---\n")  # type-гүй → замын hint
        w(v / "02-Projects/3-On-hold/Project Hold/Project Hold.md", "---\ntype: project\n---\n")  # статусыг хавтаснаас
        w(v / "99-Archive/Projects/Project Done/Project Done.md", "---\ntype: project\nstatus: completed\n---\n")
        w(v / "02-Projects/Secret/Secret.md", "---\ntype: project\nprivate: true\n---\n")
        w(v / "_system/templates/Project.md", "---\ntype: project\n---\n")
        w(v / "03-Areas/Business/finances/private/x.md", "---\ntype: task\ndue: 2026-10-10\n---\n# нууц\n")
        w(v / "01-GTD/Tasks/new.md", '---\ntype: task\nstatus: next-action\nproject: "[[02-Projects/Project New/Project New]]"\ndue: 2026-10-14\n---\n# Шинэ task\n')
        w(v / "00-GTD/Tasks/old.md", '---\ntype: task\nstatus: next-action\nproject: "[[03-Projects/1-Active/Project Old/Project Old]]"\n---\n# Хуучин task\n')
        w(v / "02-GTD/tasks/legacy.md", "---\nstatus: waiting\n---\n# Legacy task\n")  # type-гүй, хуучин хавтас
        w(v / "01-GTD/Events/e.md", "---\ntype: meeting\nscheduled: 2026-10-15 19:00\n---\n# Уулзалт\n")
        w(v / "01-GTD/Daily/2026-10-14.md", "---\ntype: daily\n---\n")

    def tearDown(self):
        vault_index.invalidate()
        self.tmp.cleanup()

    def test_types_and_privacy(self):
        idx = vault_index.index(self.v)
        types = {(n["type"], n["name"]) for n in idx}
        self.assertIn(("task", "legacy"), types)
        self.assertIn(("meeting", "e"), types)
        self.assertIn(("daily", "2026-10-14"), types)
        self.assertFalse(any(n["name"] in ("x", "Secret") for n in idx))

    def test_projects_new_and_old_paths(self):
        rooms = {r["project"]: r for r in read_projects(self.v)}
        self.assertEqual(rooms["Project New"]["stage"], "Дизайн")
        self.assertEqual(rooms["Project Old"]["status"], "active")
        self.assertEqual(rooms["Project Hold"]["status"], "on-hold")
        self.assertEqual(rooms["Project Done"]["kind"], "archive")
        self.assertNotIn("_BRAIN", rooms)
        self.assertNotIn("Secret", rooms)
        self.assertNotIn("Project", rooms)

    def test_calendar_build(self):
        st = {"agents": [], "rooms": read_projects(self.v)}
        d = calendar_data.build(self.v, st, "2026-10-12", "2026-10-18")
        titles = {i["title"]: i for i in d["items"]}
        self.assertEqual(titles["Шинэ task"]["date"], "2026-10-14")
        self.assertEqual(titles["Шинэ task"]["stage"], "Дизайн")
        self.assertEqual(titles["Уулзалт"]["time"], "19:00")
        self.assertNotIn("нууц", titles)
        self.assertEqual([t["title"] for g in d["shelf"] for t in g["tasks"]], ["Хуучин task"])
        self.assertEqual(d["daily"], ["2026-10-14"])


class ScheduleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.v = Path(self.tmp.name)
        vault_index.invalidate()

    def tearDown(self):
        self.tmp.cleanup()

    def test_writes_only_due_crlf(self):
        src = '---\ndate: 2026-10-01\nupdated: 2026-10-02\ntype: task\nstatus: next-action\ndue: \nowner: "bd"\n---\n# T\nбие текст\n'
        f = self.v / "01-GTD/Tasks/t.md"
        w(f, src, nl="\r\n")
        r = calendar_data.set_due(self.v, "01-GTD/Tasks/t.md", "2026-10-14", True)
        self.assertEqual(r["previous"], "")
        exp = src.replace("due: \n", "due: 2026-10-14\n").replace("\n", "\r\n").encode("utf-8")
        self.assertEqual(f.read_bytes(), exp)  # бусад бүх byte (updated:, CRLF) хэвээр
        r = calendar_data.set_due(self.v, "01-GTD/Tasks/t.md", "", True)  # undo
        self.assertEqual(r["previous"], "2026-10-14")
        self.assertIn(b"due:\r\nowner", f.read_bytes())

    def test_inserts_missing_due_and_legacy_path(self):
        f = self.v / "02-GTD/tasks/a.md"
        w(f, "---\ntype: task\nstatus: next-action\n---\n# A\n")
        calendar_data.set_due(self.v, "02-GTD/tasks/a.md", "2026-11-01", True)
        self.assertEqual(f.read_text(encoding="utf-8"), "---\ntype: task\nstatus: next-action\ndue: 2026-11-01\n---\n# A\n")

    def test_rejects(self):
        w(self.v / "01-GTD/Tasks/p.md", "---\ntype: task\nprivate: true\n---\n")
        w(self.v / "01-GTD/Tasks/n.md", "---\ntype: note\n---\n")
        w(self.v / "02-Projects/X/X.md", "---\ntype: task\n---\n")
        w(self.v / "01-GTD/Tasks/ok.md", "---\ntype: task\n---\n")
        E = calendar_data.ScheduleError
        cases = [("01-GTD/Tasks/ok.md", "2026-10-14", None),       # confirm алга
                 ("01-GTD/Tasks/ok.md", "14/10", True),             # огноо буруу
                 ("01-GTD/Tasks/ok.md", "2026-02-30", True),
                 ("01-GTD/Tasks/p.md", "2026-10-14", True),         # private
                 ("01-GTD/Tasks/n.md", "2026-10-14", True),         # task биш
                 ("02-Projects/X/X.md", "2026-10-14", True),        # хавтсаас гадуур
                 ("01-GTD/Tasks/../../02-Projects/X/X.md", "2026-10-14", True),
                 ("01-GTD/Tasks/none.md", "2026-10-14", True)]
        for path, due, conf in cases:
            with self.assertRaises(E, msg=path + due):
                calendar_data.set_due(self.v, path, due, conf)
        self.assertNotIn("due", (self.v / "01-GTD/Tasks/ok.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
