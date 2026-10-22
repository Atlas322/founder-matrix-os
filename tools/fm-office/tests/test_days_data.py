import sys, tempfile, unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import days_data  # noqa: E402


def vault():
    v = Path(tempfile.mkdtemp())
    (v / "_system/logs").mkdir(parents=True)
    (v / "_system/logs/2026-10-16.md").write_text(
        "- **00:07** · architect → update · fm 0.9.90\n- **02:05** · PC-Harvester → [[x]]\n- **12:53** · 🎨 Creative → постер\n"
        "- **12:25** · Mac Wiki → судалгаа\n- **13:00** · 📁 Project A → дугаар\nбусад мөр\n", encoding="utf-8")
    (v / "04-Resources/Atomic/decisions").mkdir(parents=True)
    (v / "04-Resources/Atomic/decisions/2026-10-16 - нэг.md").write_text("---\ntype: atom\n---\n", encoding="utf-8")
    (v / "04-Resources/Atomic/decisions/2026-10-16 - нууц.md").write_text("---\nprivate: true\n---\n", encoding="utf-8")
    (v / "01-GTD/Tasks").mkdir(parents=True)
    (v / "01-GTD/Tasks/Ажил.md").write_text("---\nstatus: completed\ncompleted: 2026-10-17 10:00\n---\n", encoding="utf-8")
    (v / "01-GTD/Daily").mkdir(parents=True)
    (v / "01-GTD/Daily/2026-10-17.md").write_text("---\ntype: daily\n---\n# Бямба\n- өглөө гүйсэн\n", encoding="utf-8")
    return v


class DaysTest(unittest.TestCase):
    def test_days_counts(self):
        d = days_data.days(vault(), today=date(2026, 10, 18))["days"]
        self.assertEqual([x["date"] for x in d], ["2026-10-16", "2026-10-17", "2026-10-18"])
        c = d[0]["counts"]
        self.assertEqual((c["architect"], c["creative"], c["wiki"], c["project"], c["atom"]), (1, 1, 1, 1, 1))   # harvester тоологдохгүй, нууц атом ч
        self.assertEqual(d[1]["counts"]["task"], 1); self.assertTrue(d[1]["daily"])
        self.assertEqual(d[2]["total"], 0)

    def test_day_detail_and_validation(self):
        v = vault()
        x = days_data.day(v, "2026-10-17")
        self.assertEqual(x["tasks"], ["Ажил"]); self.assertEqual(x["daily"]["title"], "Бямба")
        with self.assertRaises(ValueError):
            days_data.day(v, "../etc")

    def test_life_links_past_to_present(self):
        v = vault()
        (v / "04-Resources/Atomic/decisions/2026-10-17 - хоёр.md").write_text("---\ntype: atom\n---\n[[2026-10-16 - нэг]] дээр тулгуурлав\n", encoding="utf-8")
        L = days_data.life(v, today=date(2026, 10, 18))
        self.assertIn(["A:2026-10-16 - нэг", "A:2026-10-17 - хоёр", 1], L["edges"])
        self.assertFalse(any("нууц" in i["id"] for i in L["items"]))


if __name__ == "__main__":
    unittest.main()
