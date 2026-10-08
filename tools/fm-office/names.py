"""FM Office — сешний одоогийн нэрийг дүрийн бүтцээс гаргана (хуучин registry нэр биш).

Эх сурвалж (бүгд runtime-д уншина, repo-д хүн/харилцагчийн нэр бичихгүй):
  plugins/fm/sidebar.json                         → role → одоогийн гарчиг («🏛️ Architect», «📥 GTD» …)
  <vault>/_system/fm/agents/*.md, 03-Areas/AI Team/ai-workers/*.md  → `role:` + `aliases:` (хуучин нэрс)
  <vault>/_system/fm/fm-office.json  "names"      → нэмэлт хуучин→шинэ хүснэгт, "role_map" → note role → sidebar role
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIDEBAR_CANDIDATES = [HERE.parents[1] / "plugins" / "fm" / "sidebar.json", HERE.parents[1] / "sidebar.json"]
ROLE_NOTE_DIRS = ["_system/fm/agents", "03-Areas/AI Team/ai-workers", "04-Areas/AI Team/ai-workers"]  # шинэ байршил эхэнд, хуучин нь fallback
DEV_SUFFIX = re.compile(r"\s*[\(\[]?\s*(?:·\s*)?\b(PC|Mac)\b\s*[\)\]]?\s*$", re.I)
EMOJI_LEAD = re.compile(r"^[^\w\[\(]+", re.U)


def norm(s):
    return re.sub(r"[^\w]+", "", str(s or "").lower())


def clean(s):
    """«🖥️ Tool Developer (PC)» → «Tool Developer»; «Mac-Sys» → «Sys»."""
    s = str(s or "").strip()
    s = DEV_SUFFIX.sub("", s)
    s = re.sub(r"^(PC|Mac)[-\s·]+", "", s, flags=re.I)
    return EMOJI_LEAD.sub("", s).strip()


def sidebar_titles():
    for p in SIDEBAR_CANDIDATES:
        try:
            sb = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out = {}
        for s in sb.get("sessions", []):
            r, t = s.get("role", ""), s.get("title", "")
            if "<" in r or s.get("group") == "Finance" or r in out:
                continue
            out[r] = t
        for s in sb.get("sessions", []):  # «🔍 Research · <сэдэв>» загвар
            if s.get("role") == "research":
                out["research"] = s.get("title", "🔍 Research · <сэдэв>")
        return out
    return {}


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.S)
    if not m:
        return {}, []
    fm, aliases, cur = {}, [], None
    for line in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if k:
            cur = k.group(1)
            v = k.group(2).strip()
            fm[cur] = v.strip('"').strip("'")
            if cur == "aliases" and v.startswith("["):
                aliases += [a.strip().strip('"').strip("'") for a in v.strip("[]").split(",") if a.strip()]
        elif cur == "aliases" and line.strip().startswith("- "):
            aliases.append(line.strip()[2:].strip().strip('"').strip("'"))
    return fm, aliases


class Names:
    def __init__(self, vault, cfg):
        self.titles = sidebar_titles()
        role_map = {"portfolio": "project", "content": "creative"}
        role_map.update(cfg.get("role_map") or {})
        self.alias = {}  # norm(old name) → current title
        for d in ROLE_NOTE_DIRS:
            base = Path(vault) / d
            if not base.is_dir():
                continue
            for f in base.glob("*.md"):
                try:
                    fm, al = frontmatter(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    continue
                role = role_map.get(fm.get("role", ""), fm.get("role", ""))
                title = self.titles.get(role)
                if not title or "private" in (fm.get("tags", "") + str(fm.get("private", ""))).lower() or role == "finance":
                    continue
                for a in al + [f.stem]:
                    self.alias.setdefault(norm(clean(a)), title)
        for old, new in (cfg.get("names") or {}).items():
            self.alias[norm(clean(old))] = new
        for t in self.titles.values():
            self.alias.setdefault(norm(clean(t)), t)

    def resolve(self, label):
        """Хуучин/шинэ нэр → одоогийн гарчиг эсвэл None."""
        n = norm(clean(label))
        if not n:
            return None
        if n in self.alias:
            return self.alias[n]
        for k, v in sorted(self.alias.items(), key=lambda kv: -len(kv[0])):  # «sysadmin» ⊃ «sys» гэх мэт
            if len(k) >= 3 and (k in n or (len(n) >= 4 and n in k)):
                return v
        return None

    def display(self, v, room_name=None):
        """Registry-ийн нэг сешн → одоогийн харуулах нэр (төхөөрөмжгүй)."""
        role, proj = v.get("role") or "", str(v.get("project") or "")
        if (role == "project" or (not role and v.get("group") == "projects")) and proj not in ("", "project"):
            return "📁 " + (room_name or clean(v.get("title") or v.get("name") or proj))
        if role == "research":
            topic = clean((v.get("title") or v.get("name") or "").split("·")[-1]) or proj
            tmpl = self.titles.get("research", "🔍 Research · <сэдэв>")
            return re.sub(r"<[^>]+>", topic, tmpl)
        if role in self.titles:
            return self.titles[role]
        for k in ("title", "name", "old_title"):
            r = self.resolve(v.get(k))
            if r:
                return r
        return clean(v.get("title") or v.get("name") or proj) or "?"
