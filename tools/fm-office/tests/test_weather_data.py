import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import weather_data  # noqa: E402


class WeatherTest(unittest.TestCase):
    def test_kind_of(self):
        k = weather_data.kind_of
        self.assertEqual(k(0), "clear"); self.assertEqual(k(1, 50), "cloudy"); self.assertEqual(k(3), "overcast")
        self.assertEqual(k(2, 90), "overcast"); self.assertEqual(k(45), "fog"); self.assertEqual(k(61), "rain")
        self.assertEqual(k(81), "rain"); self.assertEqual(k(73), "snow"); self.assertEqual(k(85), "snow"); self.assertEqual(k(95), "storm")

    def test_aq_label(self):
        f = weather_data.aq_label
        self.assertEqual(f(48), "сайн"); self.assertEqual(f(51), "дунд"); self.assertEqual(f(160), "эрүүл бус")
        self.assertEqual(f(420), "аюултай"); self.assertEqual(f(None), "сайн")


if __name__ == "__main__":
    unittest.main()
