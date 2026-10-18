import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import map_data  # noqa: E402


class MapDataTest(unittest.TestCase):
    def test_home_and_clients(self):
        v = Path(tempfile.mkdtemp())
        (v / "03-Areas/people").mkdir(parents=True)
        (v / "03-Areas/people/Me.md").write_text('---\nis-vault-owner: true\nhome: {"name": "Гэр", "lng": 1.5, "lat": 2.5}\n---\n', encoding="utf-8")
        c = v / "03-Areas/Business/X/companies"; c.mkdir(parents=True)
        (c / "A.md").write_text('---\nstatus: active\nlocations: [{"name": "A1", "lng": 3, "lat": 4}, {"name": "A2", "city": "Дархан"}]\n---\n', encoding="utf-8")
        (c / "B.md").write_text('---\nstatus: declined\nlocations: [{"name": "B1", "lng": 5, "lat": 6}]\n---\n', encoding="utf-8")
        d = map_data.build(v)
        self.assertEqual(d["office"], [1.5, 2.5])
        self.assertEqual([x["name"] for x in d["clients"]], ["A1"]); self.assertEqual(d["clients"][0]["lngLat"], [3, 4])
        self.assertEqual(d["unplaced"][0]["name"], "A2")


if __name__ == "__main__":
    unittest.main()
