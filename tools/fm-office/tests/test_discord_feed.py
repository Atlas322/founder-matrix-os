import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timezone  # noqa: E402
from discord_feed import parse_message, local_time, HUMAN_ID  # noqa: E402

A = lambda i, name, title, role, project, dev, state="idle": {
    "id": i, "name": name, "title": title, "role": role, "project": project, "device_name": dev, "state": state}
AGENTS = [
    A("arch-pc", "Tool Developer (PC)", "🏛️ Architect", "developer", "developer", "PC", "working"),
    A("arch-mac", "Tool Developer", "🏛️ Architect", "developer", "developer", "Mac"),
    A("cd-pc", "Creative Director", "Creative · Director", "creative", "creative", "PC"),
    A("gtd-mac", "Mac-Sys", "📥 GTD", "area", "area", "Mac"),
    A("pa-pc", "Project A (PC)", "📁 Project A", "project", "proj-a", "PC"),
    A("pa-mac", "Mac-A", "📁 Project A", "project", "proj-a", "Mac"),
]
OWN_A = [a for a in AGENTS if a["project"] == "proj-a"]
OWN_ARCH = [a for a in AGENTS if a["project"] == "developer"]
BOT_PC = {"username": "FM-Relay-PC", "bot": True}
BOT_MAC = {"username": "FM-Relay-Mac", "bot": True}
HUMAN = {"username": "bd", "bot": False}


def msg(content, author, mid="1", ts="2026-10-09T08:00:00+00:00"):
    return {"id": mid, "content": content, "author": author, "timestamp": ts}


class ParseTest(unittest.TestCase):
    def test_footer_author_and_reply_to_human(self):
        ev = parse_message(msg("Deploy бэлэн боллоо\n-# 🖥️ PC · 🏛️ Architect", BOT_PC), "architect", OWN_ARCH, AGENTS)
        self.assertEqual(ev["from"], "arch-pc")
        self.assertEqual(ev["to"], HUMAN_ID)  # өөрийн сувагт → itge.e руу хариу
        self.assertEqual(ev["type"], "Discord")
        self.assertNotIn("-#", ev["text"])

    def test_old_prefix_and_explicit_arrow(self):
        ev = parse_message(msg("🖥️ [Creative Director · PC] ✅ дууслаа → PC (Architect)", BOT_PC), "creative-director", [AGENTS[2]], AGENTS)
        self.assertEqual(ev["from"], "cd-pc")
        self.assertEqual(ev["to"], "arch-pc")
        self.assertEqual(ev["type"], "✅")

    def test_mac_footer_and_for_pc(self):
        ev = parse_message(msg("🙋 авлаа, for pc шалгана уу\n🍎 Mac · 📁 Project A", BOT_MAC), "project-a", OWN_A, AGENTS)
        self.assertEqual(ev["from"], "pa-mac")
        self.assertEqual(ev["to"], "pa-pc")
        self.assertEqual(ev["type"], "🙋")

    def test_at_addressing(self):
        ev = parse_message(msg("@architect relay-г шалгаарай\n-# 🍎 Mac · 📥 GTD", BOT_MAC), "gtd", [AGENTS[3]], AGENTS)
        self.assertEqual(ev["from"], "gtd-mac")
        self.assertIn(ev["to"], ("arch-pc", "arch-mac"))

    def test_human_goes_to_working_owner(self):
        ev = parse_message(msg("Энэ хэр явж байна?", HUMAN), "architect", OWN_ARCH, AGENTS)
        self.assertEqual(ev["from"], HUMAN_ID)
        self.assertEqual(ev["to"], "arch-pc")
        self.assertEqual(ev["type"], "itge.e")

    def test_privacy_and_truncation(self):
        self.assertIsNone(parse_message(msg("✅ бүртгэлээ", BOT_PC), "business", [], AGENTS))
        self.assertIsNone(parse_message(msg("x", HUMAN), "💰-personal", [], AGENTS))
        # танигдаагүй (private) сешний footer → алгасна
        self.assertIsNone(parse_message(msg("нууц\n-# 🖥️ PC · Finance · Санхүү", BOT_PC), "project-a", OWN_A, AGENTS))
        ev = parse_message(msg("я" * 300, HUMAN), "project-a", OWN_A, AGENTS)
        self.assertLessEqual(len(ev["text"]), 80)
        self.assertEqual(set(ev), {"id", "ts", "hhmm", "iso", "from", "to", "type", "text", "channel"})


    def test_utc_to_local_time(self):
        ev = parse_message(msg("сайн уу", HUMAN, ts="2026-10-08T16:28:00.123000+00:00"), "project-a", OWN_A, AGENTS)
        exp = datetime(2026, 10, 8, 16, 28, tzinfo=timezone.utc).astimezone()  # машины tz (UB дээр 10-09 00:28)
        self.assertEqual(ev["hhmm"], exp.strftime("%H:%M"))
        self.assertEqual(ev["ts"], exp.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(datetime.fromisoformat(ev["iso"]).utcoffset(), exp.utcoffset())
        self.assertEqual(local_time("2026-10-08T16:28:00Z").astimezone(timezone.utc).hour, 16)

    def test_old_name_footer_resolves_via_keys(self):
        ag = [dict(AGENTS[0], name="🏛️ Architect", title="🏛️ Architect", keys={"tooldeveloper", "tooldeveloperpc"})]
        ev = parse_message(msg("ok\n-# 🖥️ PC · Tool Developer (PC)", BOT_PC), "architect", ag, ag)
        self.assertEqual(ev["from"], "arch-pc")


if __name__ == "__main__":
    unittest.main()
