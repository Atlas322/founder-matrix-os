import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import garden_data  # noqa: E402


class GardenTest(unittest.TestCase):
    def test_build(self):
        v = Path(tempfile.mkdtemp())
        for n, st in (("B", "planning"), ("A", "active"), ("C", "archive")):
            (v / "02-Projects" / n).mkdir(parents=True)
            (v / "02-Projects" / n / f"{n}.md").write_text(f"---\nstatus: {st}\n---\n", encoding="utf-8")
        (v / "03-Areas/Goals").mkdir(parents=True)
        (v / "01-GTD/Inbox").mkdir(parents=True); (v / "01-GTD/Inbox/санаа.md").write_text("x", encoding="utf-8")
        (v / "99-Archive/old").mkdir(parents=True)
        d = garden_data.build(v)
        self.assertEqual([p["name"] for p in d["projects"]], ["A", "B"])
        self.assertEqual(d["areas"], ["Goals"]); self.assertEqual(d["inbox"]["recent"], ["санаа"]); self.assertEqual(d["archive"], 1)


if __name__ == "__main__":
    unittest.main()
