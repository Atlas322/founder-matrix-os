import sys, tempfile, unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import hall_data  # noqa: E402


def vault():
    d = Path(tempfile.mkdtemp())
    (d / "04-Resources/references").mkdir(parents=True)
    (d / "04-Resources/references/Видео.md").write_text("үз https://youtu.be/dQw4w9WgXcQ ба https://www.youtube.com/watch?v=dQw4w9WgXcQ", encoding="utf-8")
    (d / "04-Resources/references/Нууц.md").write_text("---\nprivate: true\n---\n", encoding="utf-8")
    (d / "_system").mkdir(); (d / "00-Soul").mkdir()
    return d


class HallTest(unittest.TestCase):
    def test_root_hides_private_folders(self):
        names = [f["name"] for f in hall_data.list_dir(vault(), "")["folders"]]
        self.assertEqual(names, ["04-Resources"])

    def test_notes_videos_dedup_and_private_hidden(self):
        r = hall_data.list_dir(vault(), "04-Resources/references")
        self.assertEqual([n["name"] for n in r["notes"]], ["Видео"])
        self.assertEqual(r["notes"][0]["videos"], ["dQw4w9WgXcQ"])

    def test_rejects_escape_and_hidden(self):
        v = vault()
        for bad in ("../", "_system", "00-Soul"):
            with self.assertRaises(hall_data.HallError):
                hall_data.list_dir(v, bad)

    def test_write_atom_never_overwrites(self):
        v = vault()
        req = {"confirm": True, "title": "Toon/shading: тэмдэглэл", "video": "dQw4w9WgXcQ",
               "highlights": [{"t": 75, "text": "matcap = хуурамч гэрэл"}], "home": "04-Resources/references"}
        a = hall_data.write_atom(v, req, today=date(2026, 10, 18))
        b = hall_data.write_atom(v, req, today=date(2026, 10, 18))
        self.assertEqual(a["path"], "04-Resources/Atomic/knowledge/2026-10-18 - Toon shading тэмдэглэл.md")
        self.assertTrue(b["path"].endswith("(2).md"))
        text = (v / a["path"]).read_text(encoding="utf-8")
        self.assertIn("[1:15](https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=75s) — matcap = хуурамч гэрэл", text)
        self.assertIn('up: "[[04-Resources/references]]"', text)

    def test_write_atom_requires_confirm_and_content(self):
        v = vault()
        with self.assertRaises(hall_data.HallError):
            hall_data.write_atom(v, {"title": "x", "body": "y"})
        with self.assertRaises(hall_data.HallError):
            hall_data.write_atom(v, {"confirm": True, "title": "x"})
        with self.assertRaises(hall_data.HallError):
            hall_data.write_atom(v, {"confirm": True, "title": "x", "body": "y", "video": "bad id!"})

    def test_write_atom_reader_quotes(self):
        v = vault()
        a = hall_data.write_atom(v, {"confirm": True, "title": "Унших", "url": "https://ex.com/a",
                                     "highlights": [{"t": None, "text": "чухал өгүүлбэр"}]}, today=date(2026, 10, 18))
        text = (v / a["path"]).read_text(encoding="utf-8")
        self.assertIn("- > чухал өгүүлбэр", text); self.assertIn('url: "https://ex.com/a"', text)

    def test_notes_carry_kind(self):
        r = hall_data.list_dir(vault(), "04-Resources/references")
        self.assertEqual(r["notes"][0]["kind"], "video")

    def test_topics_group_and_untagged(self):
        v = vault()
        ref = v / "04-Resources/references"
        (ref / "А.md").write_text('---\ntopics:\n  - "[[04-Resources/Topics/Дизайн]]"\nurl: "https://github.com/a/b"\n---\n', encoding="utf-8")
        (ref / "Б.md").write_text('---\ntopics:\n  - "[[04-Resources/Topics/Дизайн]]"\n  - "[[04-Resources/Topics/AI]]"\nurl: "https://youtu.be/dQw4w9WgXcQ"\n---\n', encoding="utf-8")
        t = hall_data.topics(v)
        names = [g["name"] for g in t["topics"]]
        self.assertEqual(names[0], "Дизайн"); self.assertEqual(names[-1], hall_data.UNTAGGED)
        self.assertEqual(t["topics"][0]["kinds"], {"repo": 1, "video": 1})
        refs = hall_data.topic_refs(v, "Дизайн")["notes"]
        self.assertEqual([n["kind"] for n in refs], ["video", "repo"])   # төрлийн дарааллаар


if __name__ == "__main__":
    unittest.main()
