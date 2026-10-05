# `fm`: Founder Matrix OS (marketplace `founder-matrix`)

**Founder Matrix Second Brain**-ийн Claude Code plugin. Гишүүн бүрийн **хувийн Obsidian vault**-ийг GTD + PARA + атом тэмдэглэлээр ажиллуулж, бизнес ба хувийн амьдралыг нэг дор цэгцэлнэ. Бүх сешн нь **Agent**, зөвхөн **дүрээрээ** ялгарна (GTD, Project, Area, Resource, Санхүү 🔒, Content Writer, Creative Director, Tool Developer, төсөл тус бүрийн дүр). Дүрийн тэмдэглэлүүд plugin-д биш, таны vault-ийн `04-Areas/AI Team/ai-workers/`-д амьдарна.

> **Суулгах алхам, өдөр тутмын хэрэглээ, нууцлал, асуудал шийдэх:** repo-гийн үндсэн [README.md](../../README.md). Энэ файл зөвхөн plugin-ийн дотоод бүтцийг тайлбарлана.

## Суулгах (товч)

```
gh auth login && gh auth setup-git
/plugin marketplace add rollingbd/founder-matrix-os
/plugin install fm@founder-matrix
/reload-plugins
```

Тохиргоо: `vault_path` (заавал), `member`, `device`. Төхөөрөмжийн `~/.fmos/config.json` (`vault`, `device`, `member`) болон `FM_VAULT` орчны хувьсагчийг ч уншина. Дараа нь vault хавтаснаасаа Claude Code нээгээд `/fm:setup`.

## Юу орсон бэ

| Хэсэг | Агуулга |
|---|---|
| Skill (`/fm:…`) | `setup`, `role`, `vault`, `save`, `inbox`, `track`, `update`, `clip`, `daily`, `task`, `project`, `spawn`, `finance`, `bases`, `canvas`, `vault-cli` |
| Agent | `resource`, `content-writer`, `creative-director`, `tool-developer` (vault дахь дүрийн тэмдэглэл рүү заадаг нимгэн заагч) |
| Hook | SessionStart: `_system/BOOT.md` + дүрийн дүрмийг ачаална (≤10 KB). PostToolUse: тэмдэглэл бичих бүрт lint (frontmatter, огноо, файлын нэр); token болон хувийн санхүүг буруу газар бичихийг **блоклоно** |
| Vault загвар | `vault-template/`: PARA хавтсууд, `_system/BOOT.md`, `_system/fm/`, дүрийн тэмдэглэлүүд, загварууд, Bases, хувийн санхүүгийн модуль |

## `/fm:setup`: амьдралын onboarding

1. **Араг яс** (`scripts/fm_setup.py`): эхлээд dry-run, зөвшөөрсний дараа `vault-template`-ийг хуулна. Байгаа файлыг **хэзээ ч дарж бичихгүй**, `.obsidian/`-д хүрэхгүй, vault-аас гадуур юу ч бичихгүй.
2. **Ярилцлага** (нэг асуулт нэг удаа, мэдэхгүй бол `TBD`):
   - **SOUL** (`01-Soul/SOUL.md`): хэн бэ, үнэт зүйл, энэ жилийн гол бүтээл, anti-goal, харилцааны хэв маяг;
   - **Зорилго** (`07-Goals/`);
   - **Area-ууд**: бизнес (`04-Areas/Business/`: компани, хэрэгсэл, санхүү) ба хувийн (`04-Areas/Life/`: эрүүл мэнд, гэр бүл…);
   - **Төслүүд** (`03-Projects/`): бизнес ба хувийн 1–3 идэвхтэй төсөл;
   - **Хүмүүс** (`04-Areas/people/`), **лавлагаа** (`05-Resources/`);
   - **Хувийн санхүү** 🔒 (`04-Areas/Business/finances/private/`): зөвхөн бүтэц; агуулгыг `/fm:finance` Санхүү сешнд хөтөлнө;
   - **Дүрүүд** (`04-Areas/AI Team/ai-workers/`) → `_system/fm/registry.json`.
3. Энэ сешнийг дүрд холбох: `/fm:role gtd`.

## Хөдөлгүүрийн өгөгдөл: `_system/fm/`

| Файл | Юу |
|---|---|
| `registry.json` | сешн ↔ дүр, төсөл, төхөөрөмж, `private` |
| `channels.json`, `discord.json` | Discord relay (заавал биш, [docs/discord-relay.md](../../docs/discord-relay.md)) |
| `state/<төсөл>.md` | baton: ОДОО (хаана зогссон, дараагийн алхам) ба ТҮҮХ |

`_system/relay/` нь хуучин (архив) суваг, шинэ өгөгдөл бичихгүй. `_system/STATUS.md` дүр бүрийн төлөвийг `/fm:update`-ээр хүлээн авна.

## Нууцлал (товч)

- «Хувийн» = **vault-аас хэзээ ч гарахгүй**: registry-д `"private": true` эсвэл `finance` / `tax` / `gold` төсөл; git, Discord, STATUS, лог, daily, атом руу орохгүй. Зөвхөн `role: finance` сешн уншиж, бичнэ.
- Token (`*_token`) нь `sensitive` тохиргоо тул OS keychain-д хадгалагдана. Lint hook тэмдэглэлд token шиг мөр бичигдэхийг блоклоно.

## Windows

Hook-ууд `python3`-ийг shell-гүй (exec form) дууддаг. `python3` олдохгүй бол hook алдаа гаргаад үргэлжилнэ (сешн блоклогдохгүй, гэхдээ context, lint ажиллахгүй). Шийдэл: `uv python install 3.12 --default`, Microsoft Store Python, эсвэл `python.exe`-г `python3.exe` болгон хуулах. Дэлгэрэнгүй: [README](../../README.md#windows-дээр-python3), `hooks/README.md`. Бүх script цэвэр Python 3.9+ (pathlib, стандарт сан, UTF-8), bash/jq шаардахгүй.

## Бүтэц

```
.claude-plugin/plugin.json      нэр, хувилбар, userConfig
skills/<slug>/SKILL.md          skill (+ scripts/, references/)
agents/                         subagent заагчид
hooks/hooks.json                SessionStart, PostToolUse
scripts/                        fm_common.py, fm_context.py, fm_lint.py, fm_setup.py
vault-template/                 /fm:setup-ийн хуулах vault
LICENSE  LICENSES/  THIRD_PARTY_NOTICES.md
```

Хөгжүүлэлт: `claude --plugin-dir plugins/fm`, `claude plugin validate --strict plugins/fm`, тест `python3 tests/test_hooks.py` (repo root-оос). Хувь нэмэр: [CONTRIBUTING.md](../../CONTRIBUTING.md). Хувилбарын түүх: [CHANGELOG.md](../../CHANGELOG.md).

## Шинэчлэх

`/plugin marketplace update founder-matrix` → `/reload-plugins`, эсвэл `/plugin` → Marketplaces → founder-matrix → **Enable auto-update**. `plugin.json`-ийн `version` нэмэгдэх үед шинэ хувилбар очно.

## Лиценз

Copyright (c) 2026 itge.e. All rights reserved. Founder Matrix баг болон SB+AI Season 2-ын оролцогчдод ашиглах эрхтэй; хувь нэмэр нь ижил нөхцлөөр itge.e-д лицензлэгдэнэ ([LICENSE](LICENSE)). kepano/obsidian-skills болон obsidian-second-brain-аас гаралтай хэсгүүд MIT лицензтэй: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

---

**English (short).** `fm` is the Claude Code plugin of Founder Matrix Second Brain (marketplace `founder-matrix`): a personal Obsidian vault engine (GTD, PARA, atomic notes, role-based Agents, private finance). Install with `/plugin marketplace add rollingbd/founder-matrix-os` and `/plugin install fm@founder-matrix`, set `vault_path`/`member`/`device` (or `~/.fmos/config.json`, `FM_VAULT`), then run `/fm:setup` for life onboarding (business and personal Areas, Projects, private Finance, People, References, Goals, Agents). Engine data lives in the vault at `_system/fm/`. Private items never leave the vault. Full guide: [root README](../../README.md).
