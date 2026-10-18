import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import osm_data  # noqa: E402


class OsmTest(unittest.TestCase):
    def test_height(self):
        self.assertEqual(osm_data.height({"height": "30 m"}), 30.0)
        self.assertAlmostEqual(osm_data.height({"building:levels": "9"}), 28.9)
        self.assertEqual(osm_data.height({"building": "house"}), 6.0)
        self.assertEqual(osm_data.height({"height": "abc", "building": "garage"}), 3.0)

    def test_to_local(self):
        lat, lon = 47.89, 106.93
        g = [{"lat": lat, "lon": lon}, {"lat": lat + .001, "lon": lon}, {"lat": lat + .001, "lon": lon + .001}]
        raw = {"elements": [
            {"type": "way", "tags": {"building": "yes", "building:levels": "3"}, "geometry": g},
            {"type": "way", "tags": {"highway": "residential"}, "geometry": g[:2]},
            {"type": "way", "tags": {"leisure": "park"}, "geometry": g},
            {"type": "way", "tags": {"waterway": "river"}, "geometry": g[:2]},
            {"type": "node", "tags": {"natural": "tree"}, "lat": lat, "lon": lon + .001},
        ]}
        d = osm_data.to_local(raw, lat, lon)
        b = d["buildings"][0]
        self.assertAlmostEqual(b[0], 10.3); self.assertEqual(b[1:3], [0.0, 0.0])
        self.assertAlmostEqual(b[4], -110.5, places=0)              # хойд зүг = -z
        self.assertEqual(d["roads"][0][0], 6); self.assertIn("park", d["areas"]); self.assertEqual(d["rivers"][0][0], 30)
        self.assertAlmostEqual(d["trees"][0], 74.7, places=0)


if __name__ == "__main__":
    unittest.main()
