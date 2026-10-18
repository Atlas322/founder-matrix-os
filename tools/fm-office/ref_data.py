"""Reference note-ийг төрлөөр нь (видео, вэб, унших, зураг, пост, repo) ангилж, үзэгчид хэрэгтэй өгөгдлийг бэлтгэнэ.

classify(fm, url)  → kind. Домэйн эхэлж (pinterest нь `reftype: Website` байсан ч зураг), дараа нь `reftype`.
fetch_ref(vault, rel) → тухайн note-ийн url-ыг л татна (дурын url биш — SSRF-ээс сэргийлнэ), 10 мин cache.
"""
import json, re, time, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

KINDS = ("video", "web", "read", "image", "post", "repo", "note")
DOMAIN = {"youtube.com": "video", "youtu.be": "video", "pinterest.com": "image", "pin.it": "image", "instagram.com": "image",
          "threads.com": "post", "threads.net": "post", "facebook.com": "post", "x.com": "post", "twitter.com": "post",
          "github.com": "repo"}
REFTYPE = {"video": "video", "watch event": "video", "moodboard": "image", "infographic": "image", "ads": "image",
           "post": "post", "article": "read", "research": "read", "book": "read", "ai skill": "repo", "my tools": "repo",
           "tool": "repo"}
UA = "Mozilla/5.0 (FM Office reader)"
_cache = {}


def frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    fm = {}
    for line in text[3:end if end > 0 else 0].splitlines():
        m = re.match(r"^([\w-]+):\s*(.+?)\s*$", line)
        if m:
            fm[m.group(1).lower()] = m.group(2).strip().strip('"').strip("'")
    return fm


def domain(url):
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def classify(fm, url):
    d = domain(url) if url else ""
    for k, v in DOMAIN.items():
        if d == k or d.endswith("." + k):
            return v
    rt = (fm.get("reftype") or "").strip().lower()
    if rt in REFTYPE:
        return REFTYPE[rt]
    return "web" if url else "note"


def first_url(fm, text):
    u = fm.get("url") or ""
    if u.startswith("http"):
        return u
    m = re.search(r"https?://[^\s)\]>\"']+", text[text.find("\n---", 3) + 4:] if text.startswith("---") else text)
    return m.group(0) if m else ""


def describe(text):
    fm = frontmatter(text)
    url = first_url(fm, text)
    img = next((fm[k] for k in ("cover", "thumbnail", "image")
                if fm.get(k, "").startswith("http") or re.search(r"\.(png|jpe?g|webp)$", fm.get(k, ""), re.I)), "")
    return {"kind": classify(fm, url), "url": url, "image": img, "reftype": fm.get("reftype", ""), "domain": domain(url) if url else ""}


# ---------- HTML → унших горим ----------
class _Reader(HTMLParser):
    BLOCK = {"p", "h1", "h2", "h3", "li", "blockquote", "pre"}
    SKIP = {"script", "style", "nav", "footer", "header", "aside", "form", "noscript", "svg"}

    def __init__(self):
        super().__init__()
        self.meta, self.blocks, self.cur, self.tag, self.skip, self.title = {}, [], [], None, 0, ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            k = (a.get("property") or a.get("name") or "").lower()
            if k in ("og:title", "og:description", "og:image", "description", "twitter:image") and a.get("content"):
                self.meta.setdefault(k, a["content"])
        if tag == "title":
            self._in_title = True
        if tag in self.SKIP:
            self.skip += 1
        if tag in self.BLOCK and not self.skip:
            self._flush(); self.tag = tag

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag in self.BLOCK:
            self._flush()

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self.tag and not self.skip:
            self.cur.append(data)

    def _flush(self):
        t = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        if self.tag and len(t) > (2 if self.tag.startswith("h") else 30):
            self.blocks.append({"tag": self.tag, "text": t[:2000]})
        self.cur, self.tag = [], None


def parse_html(html):
    r = _Reader()
    try:
        r.feed(html)
    except Exception:
        pass
    r._flush()
    return {"title": r.meta.get("og:title") or r.title.strip(), "desc": r.meta.get("og:description") or r.meta.get("description", ""),
            "image": r.meta.get("og:image") or r.meta.get("twitter:image", ""), "blocks": r.blocks[:300]}


def frameable(headers):
    xfo = (headers.get("X-Frame-Options") or "").lower()
    csp = (headers.get("Content-Security-Policy") or "").lower()
    if xfo in ("deny", "sameorigin"):
        return False
    m = re.search(r"frame-ancestors([^;]*)", csp)
    return not (m and "*" not in m.group(1))


def _get(url, limit=2_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en,mn;q=0.8"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read(limit).decode(r.headers.get_content_charset() or "utf-8", "ignore"), r.headers


def _github(url):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) < 2:
        return {}
    o, n = parts[0], parts[1]
    out = {}
    try:
        meta = json.loads(_get(f"https://api.github.com/repos/{o}/{n}")[0])
        out["repo"] = {"name": meta.get("full_name"), "stars": meta.get("stargazers_count"), "lang": meta.get("language"),
                       "desc": meta.get("description"), "pushed": (meta.get("pushed_at") or "")[:10]}
    except Exception:
        pass
    try:
        md = _get(f"https://raw.githubusercontent.com/{o}/{n}/HEAD/README.md")[0]
        out["blocks"] = [{"tag": "h2" if b.startswith("#") else "p", "text": b.lstrip("# ").strip()[:2000]}
                         for b in re.split(r"\n\s*\n", md) if b.strip() and not b.strip().startswith(("<", "!["))][:200]
    except Exception:
        pass
    return out


def fetch_ref(vault, rel, hall_safe):
    root, p = hall_safe(vault, rel)
    if p.suffix != ".md" or not p.is_file():
        raise ValueError("note алга")
    text = p.read_text(encoding="utf-8", errors="ignore")
    if "private: true" in text[:600]:
        raise ValueError("хувийн note")
    d = describe(text)
    d.update({"path": p.relative_to(root).as_posix(), "name": p.stem})
    url = d["url"]
    if not url or d["kind"] == "video":
        return d
    hit = _cache.get(url)
    if hit and time.time() - hit[0] < 600:
        return {**d, **hit[1]}
    extra = {}
    try:
        if d["kind"] == "repo" and d["domain"] == "github.com":
            extra = _github(url)
        else:
            html, headers = _get(url)
            page = parse_html(html)
            blocks = page["blocks"] or ([{"tag": "p", "text": page["desc"]}] if page["desc"] else [])   # JS-ээр ачаалдаг сайт (Notion, Threads)
            extra = {"page": {k: page[k] for k in ("title", "desc", "image")}, "blocks": blocks, "frameable": frameable(headers)}
    except Exception as e:
        extra = {"error": type(e).__name__}
    _cache[url] = (time.time(), extra)
    return {**d, **extra}


# ---------- thumbnail: самбарт харуулах зураг (сервер татаж, диск дээр cache — WebGL-д CORS асуудалгүй) ----------
THUMB_DIR = Path.home() / ".fmos" / "fm-office-thumbs"
YT_ID = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})")


def thumb_source(d):
    """note-ийн тайлбараас зургийн url: frontmatter cover/thumbnail → YouTube → GitHub og → хуудасны og:image."""
    if d.get("image"):
        return d["image"]
    url = d.get("url") or ""
    m = YT_ID.search(url)
    if d.get("kind") == "video" and m:
        return f"https://img.youtube.com/vi/{m.group(1)}/hqdefault.jpg"
    if d.get("domain") == "github.com":
        parts = urlparse(url).path.strip("/").split("/")
        if len(parts) >= 2:
            return f"https://opengraph.githubassets.com/1/{parts[0]}/{parts[1]}"
    return (d.get("page") or {}).get("image") or ""


def thumb(vault, rel, hall_safe):
    """(bytes, content_type) эсвэл None. 1 удаа татаад ~/.fmos/fm-office-thumbs-д хадгална."""
    import hashlib
    root, p = hall_safe(vault, rel)
    if p.suffix != ".md" or not p.is_file():
        return None
    text = p.read_text(encoding="utf-8", errors="ignore")
    if "private: true" in text[:600]:
        return None
    THUMB_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(p.relative_to(root).as_posix().encode()).hexdigest()
    for ext, ct in ((".jpg", "image/jpeg"), (".png", "image/png"), (".webp", "image/webp"), (".none", "")):
        f = THUMB_DIR / (key + ext)
        if f.exists():
            return (f.read_bytes(), ct) if ct else None
    d = describe(text)
    img = d.get("image") or ""
    if img and not img.startswith("http"):                       # vault доторх cover (04-Resources/references/covers/…)
        lp = (root / img).resolve()
        ct = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(lp.suffix.lower())
        if ct and root in lp.parents and lp.is_file():
            return lp.read_bytes(), ct
        d["image"] = ""
    src = thumb_source(d)
    if not src and d["url"] and d["kind"] != "note":
        try:
            src = thumb_source({**d, "page": parse_html(_get(d["url"])[0])})
        except Exception:
            src = ""
    data, ct = b"", ""
    if src.startswith("http"):
        try:
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=10) as r:
                ct = (r.headers.get_content_type() or "").lower()
                data = r.read(4_000_000) if ct.startswith("image/") else b""
        except Exception:
            data = b""
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(ct)
    if not data or not ext:
        (THUMB_DIR / (key + ".none")).write_bytes(b"")          # дахин оролдохгүй
        return None
    (THUMB_DIR / (key + ext)).write_bytes(data)
    return data, ct
