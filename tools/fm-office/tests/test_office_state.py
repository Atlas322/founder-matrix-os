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
        w(v / "03-Projects/1-Active/BYD Website/BYD Website.md",
          '---\ntype: project\nstatus: active\nstage: "[[04-Areas/Business/activities/Хөгжүүлэлт]]"\n---\n# BYD\n')
        w(v / "03-Projects/2-Planning/Inai App/Inai App.md",
          '---\nstatus: planning\nstage: "[[04-Areas/Business/activities/Brief]]"\n---\n')
        w(v / "03-Projects/1-Active/Secret/Secret.md", "---\nstatus: active\nprivate: true\n---\n")
        w(v / "03-Projects/3-On-hold/Lab/Lab.md", "---\nstatus: on-hold\n---\n")
        (v / "99-Archive/Projects/Old One").mkdir(parents=True)
        w(v / "04-Areas/Business/finances/private/secret.md", "SHOULD NEVER APPEAR 999999")
        reg = {"sessions": {
            "aaaaaaaa-1": {"name": "Mac-BYD", "group": "projects", "project": "byd", "device": "Mac", "role": "project"},
            "bbbbbbbb-2": {"name": "BYD (PC)", "group": "projects", "project": "byd", "device": "PC", "role": "project"},
            "cccccccc-3": {"name": "💰 Санхүү (PC)", "group": "areas", "project": "finance", "device": "PC", "private": True},
            "dddddddd-4": {"name": "Finance · Business", "group": "finance", "project": "finance", "device": "PC"},
            "eeeeeeee-5": {"name": "Mac-Home", "group": "areas", "project": "area", "device": "Mac", "private": True},
            "ffffffff-6": {"name": "Mac-Gold", "group": "resources", "project": "gold", "device": "Mac"},
        }, "roles": {}}
        w(v / "_system/fm/registry.json", json.dumps(reg, ensure_ascii=False))
        w(v / "_system/fm/channels.json", json.dumps({"byd": "byd-website"}))
        w(v / "_system/fm/state/byd.md", "# byd\n\n## ОДОО · 2026-10-09 10:00 · Mac-BYD (Mac)\nтекст\n")
        w(v / "_system/logs/2026-10-09.md",
          "- **09:55** · Mac-BYD → Mac-Gold: судалгаа хэрэгтэй\n- **09:58** · finance → area: нууц\n")
        self.state = build_state(v, now=datetime(2026, 10, 9, 10, 5))

    def tearDown(self):
        self.tmp.cleanup()

    def test_projects_and_stages(self):
        rooms = {r["project"]: r for r in self.state["rooms"] if r["kind"] == "project"}
        self.assertEqual(rooms["BYD Website"]["stage"], "Хөгжүүлэлт")
        self.assertEqual(rooms["Inai App"]["status"], "planning")
        self.assertEqual(rooms["Inai App"]["stage"], "Brief")
        self.assertIsNone(rooms["Lab"]["stage"])
        self.assertNotIn("Secret", rooms)
        self.assertTrue(any(r["kind"] == "archive" and r["project"] == "Old One" for r in self.state["rooms"]))

    def test_workshop_load(self):
        ws = {r["project"]: r["load"] for r in self.state["rooms"] if r["kind"] == "workshop"}
        self.assertEqual(ws["Хөгжүүлэлт"], 1)
        self.assertEqual(ws["Brief"], 1)
        self.assertEqual(ws["Контент"], 0)

    def test_agents_private_filtered_and_working(self):
        ag = {a["name"]: a for a in self.state["agents"]}
        self.assertEqual(set(ag), {"Mac-BYD", "BYD (PC)", "Mac-Gold"})
        self.assertEqual(ag["Mac-BYD"]["state"], "working")
        self.assertEqual(ag["Mac-BYD"]["device"], "🍎")
        self.assertEqual(ag["Mac-BYD"]["room"], "p:BYD Website")
        self.assertEqual(ag["Mac-BYD"]["channel"], "byd-website")
        self.assertEqual(ag["BYD (PC)"]["state"], "idle")
        self.assertIsNone(ag["BYD (PC)"]["last_seen"])
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
