import sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import library_data  # noqa: E402


def vault():
    v = Path(tempfile.mkdtemp())
    d = v / "04-Resources/Atomic/decisions"; d.mkdir(parents=True)
    (d / "2026-10-16 - Нэг шийдвэр.md").write_text("---\ntype: session-decision\ntags: [a]\n---\n# Гарчиг\nбие\n", encoding="utf-8")
    (d / "2026-10-17 - Нууц.md").write_text("---\nprivate: true\n---\nнууц\n", encoding="utf-8")
    (v / "04-Resources/references").mkdir(parents=True)
    (v / "04-Resources/references/Ном.md").write_text("лавлагаа", encoding="utf-8")
    (v / "01-GTD").mkdir(); (v / "01-GTD/x.md").write_text("гадна", encoding="utf-8")
    n = v / "02-Projects/INAI Newsletter/Output/Journal/001 - Анхны дугаар"; n.mkdir(parents=True)
    (n / "001.html").write_text("<p>hi</p>", encoding="utf-8"); (n / "001-00 Постер.png").write_bytes(b"png")
    return v


class LibraryTest(unittest.TestCase):
    def test_books_hides_private(self):
        sh = {s["key"]: s for s in library_data.books(vault())["shelves"]}
        self.assertEqual([b["title"] for b in sh["decisions"]["books"]], ["Нэг шийдвэр"])
        self.assertEqual(sh["references"]["count"], 1)

    def test_read_and_safety(self):
        v = vault()
        r = library_data.read(v, "Atomic/decisions/2026-10-16 - Нэг шийдвэр.md")
        self.assertEqual(r["section"], "Шийдвэр"); self.assertTrue(r["body"].startswith("# Гарчиг"))
        for bad in ("Atomic/decisions/2026-10-17 - Нууц.md", "../01-GTD/x.md", "references/../../01-GTD/x.md"):
            with self.assertRaises(library_data.LibraryError):
                library_data.read(v, bad)


class BacklinkTest(unittest.TestCase):
    def test_backlinks_and_tags(self):
        v = vault()
        (v / "04-Resources/references/Холбоо.md").write_text("---\ntags: [x, y]\n---\n[[2026-10-16 - Нэг шийдвэр]] харна", encoding="utf-8")
        (v / "04-Resources/references/Нууц2.md").write_text("---\nprivate: true\n---\n[[2026-10-16 - Нэг шийдвэр]]", encoding="utf-8")
        bl = library_data.backlinks(v, "Atomic/decisions/2026-10-16 - Нэг шийдвэр.md")
        self.assertEqual([b["title"] for b in bl], ["Холбоо"])
        refs = {b["title"]: b for s in library_data.books(v)["shelves"] if s["key"] == "references" for b in s["books"]}
        self.assertEqual(refs["Холбоо"]["tags"], ["x", "y"])


class NewsletterTest(unittest.TestCase):
    def test_issue_and_safety(self):
        v = vault()
        sh = library_data.books(v)["shelves"][0]
        self.assertEqual((sh["key"], sh["books"][0]["id"]), ("newsletter", "nl:001"))
        r = library_data.read(v, "nl:001"); self.assertEqual(r["html"], "/nl/001/001.html")
        self.assertEqual(library_data.issue_file(v, "001", "cover")[1], "image/png")
        for bad in ("../../../../01-GTD/x.md", "../001 - Анхны дугаар/../../x"):
            with self.assertRaises(library_data.LibraryError):
                library_data.issue_asset(v, "001", bad)
        with self.assertRaises(library_data.LibraryError):
            library_data.issue_file(v, "../x", "html")


if __name__ == "__main__":
    unittest.main()
