import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ref_data  # noqa: E402


class RefDataTest(unittest.TestCase):
    def test_domain_beats_reftype(self):
        self.assertEqual(ref_data.classify({"reftype": "Website"}, "https://www.pinterest.com/pin/1/"), "image")
        self.assertEqual(ref_data.classify({}, "https://youtu.be/abc"), "video")
        self.assertEqual(ref_data.classify({"reftype": "Product"}, "https://github.com/a/b"), "repo")

    def test_reftype_case_insensitive_and_fallbacks(self):
        self.assertEqual(ref_data.classify({"reftype": "Article"}, "https://x.notion.site/a"), "read")
        self.assertEqual(ref_data.classify({"reftype": "website"}, "https://21st.dev"), "web")
        self.assertEqual(ref_data.classify({}, ""), "note")

    def test_describe_reads_frontmatter(self):
        t = '---\nreftype: Website\nurl: "https://www.pinterest.com/pin/9/"\nthumbnail: "https://i.pinimg.com/a.jpg"\n---\n# x\n'
        d = ref_data.describe(t)
        self.assertEqual((d["kind"], d["image"], d["domain"]), ("image", "https://i.pinimg.com/a.jpg", "pinterest.com"))

    def test_url_from_body_when_no_frontmatter_url(self):
        self.assertEqual(ref_data.describe("---\ntype: reference\n---\nҮз: https://ex.com/a).")["url"], "https://ex.com/a")

    def test_parse_html_reader(self):
        html = ('<html><head><title>T</title><meta property="og:image" content="https://i/x.png"></head><body>'
                '<nav><p>цэс цэс цэс цэс цэс цэс цэс цэс цэс</p></nav><article><h2>Гарчиг</h2>'
                '<p>Энэ бол хангалттай урт догол мөр бөгөөд уншигдах ёстой.</p><script>x()</script><p>богино</p></article></body></html>')
        r = ref_data.parse_html(html)
        self.assertEqual(r["title"], "T"); self.assertEqual(r["image"], "https://i/x.png")
        self.assertEqual([b["text"] for b in r["blocks"]], ["Гарчиг", "Энэ бол хангалттай урт догол мөр бөгөөд уншигдах ёстой."])

    def test_frameable(self):
        self.assertFalse(ref_data.frameable({"X-Frame-Options": "DENY"}))
        self.assertFalse(ref_data.frameable({"Content-Security-Policy": "frame-ancestors 'self'"}))
        self.assertTrue(ref_data.frameable({}))

    def test_thumb_source_order(self):
        ts = ref_data.thumb_source
        self.assertEqual(ts({"image": "https://i/c.jpg", "kind": "video", "url": "https://youtu.be/abcdefghijk"}), "https://i/c.jpg")
        self.assertEqual(ts({"kind": "video", "url": "https://www.youtube.com/watch?v=abcdefghijk"}), "https://img.youtube.com/vi/abcdefghijk/hqdefault.jpg")
        self.assertEqual(ts({"kind": "repo", "domain": "github.com", "url": "https://github.com/a/b"}), "https://opengraph.githubassets.com/1/a/b")
        self.assertEqual(ts({"kind": "web", "url": "https://x.dev", "page": {"image": "https://x.dev/og.png"}}), "https://x.dev/og.png")


if __name__ == "__main__":
    unittest.main()
