# founder-matrix-os

Founder.Matrix vault-ийн **хөдөлгүүр**: системийн тохиргоо, ажиллах зарчим, tools, Mac ↔ PC relay.
Vault-ийн агуулга (тэмдэглэл) энд **орохгүй**.

| Хавтас | Юу |
|---|---|
| `relay/` | Mac ↔ PC Claude-уудын чат. `pc-to-mac.md`, `mac-to-pc.md`. Бичихээс өмнө `git pull`, бичсэний дараа commit + push. Append-only. |
| `vault/` | `_CLAUDE.md`, `AGENTS.md`, `CONTEXT.md` — vault ажиллах дүрэм |
| `claude/` | `.claude/` — agents, settings.json (hooks), launch.json |
| `tools/` | `_system/tools/` — Figma/Framer bridge, sidepanel, notion, save-to-inbox… |

Эх сурвалж: `<OLD-VAULT>` (PC). 2026-10-02 Obsidian Sync дууссан тул relay энд шилжив.
Дараагийн алхам: Mac clone → relay ажиллуулах → vault синкийн шийдлийг BD + 2 Claude хамт гаргах.

## Founder Matrix Second Brain: `fm` plugin (2026-10-05, TEST v0)

Энэ repo нь мөн **Claude Code marketplace `founder-matrix`** болно: `.claude-plugin/marketplace.json` → `plugins/fm/` (Founder Matrix OS). Хэрэглэгч бүр `/plugin marketplace add rollingbd/founder-matrix-os` → `/plugin install fm@founder-matrix` → `/fm:setup` гэж өөрийн хувийн vault-аа үүсгэнэ. Дэлгэрэнгүй: [`plugins/fm/README.md`](plugins/fm/README.md). Тест: `python3 tests/test_hooks.py`, `claude plugin validate --strict plugins/fm`.

> ⚠️ Баг (Төвшин, Соёл) болон Season 2-ын сурагчдад эрх өгөхөөс өмнө: энэ repo-ийн git түүхэнд `state/`, `relay/registry.json` зэрэг хувийн мэдээлэл бий — түүхийг цэвэрлэх (filter-repo + force-push) алхмыг itge.e батална.
