import json, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
H = json.loads((HERE / "assets" / "hotspots.json").read_text(encoding="utf-8"))


def pt_ok(p):
    return isinstance(p, list) and len(p) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 100 for v in p)


class HotspotTest(unittest.TestCase):
    def test_rooms_have_image_and_desks(self):
        for key, room in H["rooms"].items():
            self.assertTrue((HERE / "assets" / "img" / room["img"]).is_file(), key)
            self.assertGreaterEqual(len(room["desks"]), 4, key)
            self.assertTrue(all(pt_ok(p) for p in room["desks"]), key)

    def test_stage_and_kind_maps_point_to_rooms(self):
        for st in ("Brief", "Бэлтгэл", "Дизайн", "Хөгжүүлэлт", "Контент"):
            self.assertIn(H["stage_image"][st], H["rooms"])
        for k, v in H["kind_image"].items():
            self.assertIn(v, H["rooms"], k)

    def test_office_zones_and_desks(self):
        for k, p in H["office"]["zones"].items():
            self.assertTrue(pt_ok(p), k)
        self.assertTrue(all(pt_ok(p) for p in H["office"]["desks"]))


if __name__ == "__main__":
    unittest.main()
