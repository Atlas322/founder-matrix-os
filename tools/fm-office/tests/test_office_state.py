import json, sys, tempfile, unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from office_state import build_state  # noqa: E402


def w(p, text):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class OfficeStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        v = self.v = Path(self.tmp.name)
        w(v / "03-Projects/1-Active/Project A/Project A.md",
          '---\ntype: project\nstatus: active\nstage: "[[04-Areas/Business/activities/Хөгжүүлэлт]]"\n---\n# A\n')
        w(v / "03-Projects/2-Planning/Project B/Project B.md",
          '---\nstatus: planning\nstage: "[[04-Areas/Business/activities/Brief]]"\n---\n')
        w(v / "03-Projects/1-Active/Secret/Secret.md", "---\nstatus: active\nprivate: true\n---\n")
        w(v / "03-Projects/3-On-hold/Lab/Lab.md", "---\nstatus: on-hold\n---\n")
        (v / "99-Archive/Projects/Old One").mkdir(parents=True)
        w(v / "04-Areas/Business/finances/private/secret.md", "SHOULD NEVER APPEAR 999999")
        reg = {"sessions": {
            "aaaaaaaa-1": {"name": "Mac-A", "group": "projects", "project": "proj-a", "device": "Mac", "role": "project"},
            "bbbbbbbb-2": {"name": "A (PC)", "group": "projects", "project": "proj-a", "device": "PC", "role": "project"},
            "cccccccc-3": {"name": "💰 Санхүү (PC)", "group": "areas", "project": "finance", "device": "PC", "private": True},
            "dddddddd-4": {"name": "Finance · Business", "group": "finance", "project": "finance", "device": "PC"},
            "eeeeeeee-5": {"name": "Mac-Home", "group": "areas", "project": "area", "device": "Mac", "private": True},
            "ffffffff-6": {"name": "Mac-Gold", "group": "resources", "project": "gold", "device": "Mac"},
        }, "roles": {}}
        w(v / "_system/fm/registry.json", json.dumps(reg, ensure_ascii=False))
        w(v / "_system/fm/fm-office.json", json.dumps({"aliases": {"proj-a": "Project A"}, "research": ["gold"]}))
        w(v / "_system/fm/channels.json", json.dumps({"proj-a": "project-a"}))
        w(v / "_system/fm/state/proj-a.md", "# proj-a\n\n## ОДОО · 2026-10-09 10:00 · Mac-A (Mac)\nтекст\n")
        w(v / "_system/logs/2026-10-09.md",
          "- **09:55** · Mac-A → Mac-Gold: судалгаа хэрэгтэй\n- **09:58** · finance → area: нууц\n")
        self.state = build_state(v, now=datetime(2026, 10, 9, 10, 5), discord=False)

    def tearDown(self):
        self.tmp.cleanup()

    def test_projects_and_stages(self):
        rooms = {r["project"]: r for r in self.state["rooms"] if r["kind"] == "project"}
        self.assertEqual(rooms["Project A"]["stage"], "Хөгжүүлэлт")
        self.assertEqual(rooms["Project B"]["status"], "planning")
        self.assertEqual(rooms["Project B"]["stage"], "Brief")
        self.assertIsNone(rooms["Lab"]["stage"])
        self.assertTrue(rooms["Lab"]["parked"])
        self.assertFalse(rooms["Project A"]["parked"])
        order = [r["project"] for r in self.state["rooms"] if r["kind"] == "project"]
        self.assertEqual(order, ["Project B", "Project A", "Lab"])  # stage дарааллаар, parked төгсгөлд
        self.assertNotIn("Secret", rooms)
        self.assertTrue(any(r["kind"] == "archive" and r["project"] == "Old One" for r in self.state["rooms"]))

    def test_workshop_load(self):
        ws = {r["project"]: r["load"] for r in self.state["rooms"] if r["kind"] == "workshop"}
        self.assertEqual(ws["Хөгжүүлэлт"], 1)
        self.assertEqual(ws["Brief"], 1)
        self.assertEqual(ws["Контент"], 0)

    def test_agents_private_filtered_and_working(self):
        ag = {a["name"]: a for a in self.state["agents"] if not a.get("human")}
        self.assertEqual(set(ag), {"Mac-A", "A (PC)", "Mac-Gold"})
        self.assertEqual(ag["Mac-A"]["state"], "working")
        self.assertEqual(ag["Mac-A"]["device"], "🍎")
        self.assertEqual(ag["Mac-A"]["room"], "p:Project A")
        self.assertEqual(ag["Mac-A"]["channel"], "project-a")
        self.assertEqual(ag["A (PC)"]["state"], "idle")
        self.assertIsNone(ag["A (PC)"]["last_seen"])
        self.assertEqual(ag["Mac-Gold"]["room"], "research")

    def test_conversations_and_no_private_leak(self):
        conv = self.state["conversations"]
        self.assertEqual(len(conv), 1)
        self.assertEqual(conv[0]["from"], "aaaaaaaa")
        self.assertEqual(conv[0]["to"], "ffffffff")
        dump = json.dumps(self.state, ensure_ascii=False)
        self.assertNotIn("999999", dump)
        self.assertNotIn("Санхүү (PC)", dump)
        self.assertNotIn("нууц", dump)


if __name__ == "__main__":
    unittest.main()
