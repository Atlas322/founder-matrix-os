import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import home_data  # noqa: E402


class HomeDataTest(unittest.TestCase):
    def test_parse_gallery_skips_header_and_non_links(self):
        text = "| Сайт | Холбоос | Технологи | Юу |\n|---|---|---|---|\n| Bruno | https://bruno-simon.com | Three.js | физик |\n| X | шууд биш | a | b |\n"
        rows = home_data.parse_gallery(text)
        self.assertEqual(rows, [{"name": "Bruno", "url": "https://bruno-simon.com", "tech": "Three.js", "learn": "физик"}])

    def test_library_counts_and_hides_private(self):
        with tempfile.TemporaryDirectory() as d:
            v = Path(d)
            (v / "04-Resources/Research/Hub A").mkdir(parents=True)
            dec = v / "04-Resources/Atomic/decisions"; dec.mkdir(parents=True)
            (dec / "2026-10-18 - нээлттэй.md").write_text("---\ntype: atom\n---\n", encoding="utf-8")
            (dec / "2026-10-18 - нууц.md").write_text("---\nprivate: true\n---\n", encoding="utf-8")
            (dec / "Decisions.md").write_text("индекс", encoding="utf-8")
            lib = home_data.library(v)
            self.assertEqual(lib["research"], 1)
            self.assertEqual(lib["atoms"], 1)
            self.assertEqual(lib["decisions"], 1)
            self.assertEqual(lib["recent"], ["2026-10-18 - нээлттэй"])


if __name__ == "__main__":
    unittest.main()
