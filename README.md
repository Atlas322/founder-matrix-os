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
