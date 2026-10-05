# fm: Founder Matrix OS plugin (marketplace `soyol`)

`founder-matrix-os` repo нь Соёлын багийн дотоод **marketplace `soyol`** болно (`.claude-plugin/marketplace.json`). Одоогоор нэг plugin агуулна:

**`fm`, Founder Matrix OS.** Гишүүн бүрийн **хувийн Obsidian vault**-ийг GTD + PARA + атом тэмдэглэлээр ажиллуулах хөдөлгүүр. Багийн төслүүд ч мөн тэр хувийн vault дотор хөтлөгдөнө. Бүх сешн нь **Agent**, зөвхөн **дүрээрээ** (GTD, Project, Area, Resource, Content Writer, Creative Director, Tool Developer, Санхүү) ялгарна. Дүрийн тэмдэглэлүүд plugin-д биш, таны vault-ийн `04-Areas/AI Team/ai-workers/` дотор амьдарна.

> Төлөв: **TEST v0**: зөвхөн vault-ийн цөм хөдөлгүүр. Багийн гишүүдэд тараахаас өмнө Mac + PC дээр туршина.

## Юу орсон бэ (v0)

| Хэсэг | Агуулга |
|---|---|
| Skill (`/fm:…`) | `setup`, `role`, `vault`, `save`, `inbox`, `track`, `update`, `clip`, `daily`, `task`, `project`, `spawn`, `finance`, `bases`, `canvas`, `vault-cli` |
| Agent | `resource`, `content-writer`, `creative-director`, `tool-developer` (vault дахь дүрийн тэмдэглэл рүү заадаг нимгэн заагч) |
| Hook | SessionStart: `_system/BOOT.md` + дүрийн дүрмийг ачаална (≤10 KB). PostToolUse: тэмдэглэл бичих бүрт lint (frontmatter, огноо, файлын нэр), нууц түлхүүр болон хувийн санхүүг буруу газар бичихийг **блоклоно** |
| Vault загвар | `plugins/fm/vault-template/`: PARA хавтсууд, BOOT, 8 дүрийн тэмдэглэл, загварууд, Bases, хувийн санхүүгийн модуль. `/fm:setup` таны vault руу хуулна (байгаа файлыг хэзээ ч дарж бичихгүй) |

**v0.2-т хойшилсон:** Discord relay, Figma, Notion, видео үзэх, судалгаа, health check, calendar. `discord_token`, `notion_token`, `figma_token` тохиргоо одоо хоосон байж болно.

`/fm:update` нь хуучин `/sync`, relay status болон өдрийн дүгнэлтийг нэг команд болгосон (v0-д Discord-гүй).

## Гишүүн суулгах алхам

1. **GitHub эрх.** Энэ repo private. itge.e танд унших эрх өгсний дараа:
   ```
   gh auth login
   gh auth setup-git
   ```
2. **Claude Code дотор marketplace нэмэх:**
   ```
   /plugin marketplace add rollingbd/founder-matrix-os
   /plugin install fm@soyol
   /reload-plugins
   ```
   Суулгах үед `vault_path` (заавал: таны vault-ийн хавтас), `member` (нэр), `device` (жишээ нь `Mac`, `PC`) асууна. Дараа нь `/config`-оос өөрчилж болно.
3. **Vault бэлдэх:** vault хавтсаа Claude Code-оор нээгээд:
   ```
   /fm:setup
   ```
   Эхлээд dry-run харуулна, зөвшөөрсний дараа PARA бүтэц, `_system/BOOT.md`, дүрийн тэмдэглэлүүд, `_system/relay/registry.json`-ийг үүсгэнэ. Дараа нь `01-Soul/SOUL.md`-г нэг асуултаар бөглүүлнэ.
4. **Obsidian тохиргоо (гараар):** Settings → Core plugins → Templates асааж, template folder-ийг `_system/templates` болгоно. Kanban самбарт **Kanban** community plugin хэрэгтэй. fm нь `.obsidian/`-д хэзээ ч хүрэхгүй.
5. **Дүр сонгох:** шинэ сешн бүрт «дүргүй» гэж гарвал:
   ```
   /fm:role gtd        # эсвэл project, area, resource, finance ...
   ```

Шинэчлэл: `plugin.json`-ийн `version` (одоо `0.1.0`) нэмэгдэх үед гишүүдэд шинэ хувилбар очно. Custom marketplace-ийн auto-update анхдагчаар унтраалттай: `/plugin` → Marketplaces → soyol → Enable auto-update, эсвэл `/plugin marketplace update soyol`.

## Windows тэмдэглэл

- Hook-ууд `python3` командыг shell-гүй (exec form) дууддаг. python.org-ийн Windows installer зөвхөн `python.exe` болон `py.exe` өгдөг тул `python3` олдохгүй байж болно. Microsoft Store-ийн `python3` alias нь заримдаа зөвхөн Store-ийг нээдэг.
- Шийдэл (аль нэгийг):
  1. **uv** (санал болгох): `uv python install --default`. `%USERPROFILE%\.local\bin`-д `python.exe`, `python3.exe` үүсгэнэ; тэр хавтас PATH-д байх ёстой;
  2. Microsoft Store-оос Python 3 суулгах (жинхэнэ `python3.exe` өгнө; Settings → App execution aliases нь Store stub биш, жинхэнэ суулгалт руу заасан эсэхийг шалга);
  3. Python-ий хавтсанд `python.exe`-г `python3.exe` нэрээр хуулах.
- `python3` олдохгүй бол Claude Code hook алдаа гаргаад үргэлжилнэ: сешн блоклогдохгүй, гэхдээ context ачаалалт болон lint ажиллахгүй.
- Шалгах: PowerShell дээр `python3 --version`. Дэлгэрэнгүй: `plugins/fm/hooks/README.md`.
- Skill доторх script-үүдийг гараар ажиллуулахдаа `python3`-ийн оронд `python` эсвэл `py -3` бичиж болно. Бүх script цэвэр Python (pathlib, стандарт сан), bash/jq шаардахгүй, UTF-8 гаралттай.
- Python 3.9+ хангалттай.

## Нууцлалын загвар (privacy model)

- **Хувийн санхүү** нь vault бүрийн нэгдүгээр зэрэглэлийн модуль: `04-Areas/Business/finances/private/`, хувийн **Санхүү** дүр, сарын төлбөрийн tracker, Finance Record загвар.
- «Хувийн» гэдэг нь **vault-аас хэзээ ч гарахгүй** гэсэн үг (vault-аас хасна гэсэн үг биш):
  - git, Discord, `_system/STATUS.md`, лог, daily note, атом руу хэзээ ч орохгүй;
  - зөвхөн `role: finance` бүхий (`private: true`) сешн уншиж, бичнэ. Бусад дүр зөвхөн «N хувийн зүйл байна» гэж тоолно;
  - данс, картын дугаар, нууц үг хэзээ ч бичигдэхгүй;
  - lint hook санхүүгийн тэмдэглэлийг хувийн хавтсаас гадна бичихийг блоклоно.
- Нууц түлхүүрүүд (`*_token`) нь `sensitive` тохиргоо тул OS keychain-д хадгалагдана, хэзээ ч файлд бичигдэхгүй. Lint hook тэмдэглэлд token шиг мөр бичигдэхийг блоклоно.
- Анхаар: vault Google Drive-аар sync хийгддэг. Vault хавтсаа бүхэлд нь бусадтай share хийвэл хувийн хавтас ч хамт явна.

## Repo бүтэц

```
.claude-plugin/marketplace.json   marketplace "soyol"
plugins/fm/                        plugin "fm"
  .claude-plugin/plugin.json
  skills/  agents/  hooks/  scripts/  vault-template/
  LICENSE  LICENSES/  THIRD_PARTY_NOTICES.md
tests/test_hooks.py                python3 tests/test_hooks.py (repo root-оос)
```

Хөгжүүлэлт: `claude --plugin-dir plugins/fm` (суулгалгүй ачаална), `claude plugin validate plugins/fm`.

## Лиценз

Copyright (c) 2026 itge.e. All rights reserved. Licensed for use by members of Соёл. kepano/obsidian-skills болон obsidian-second-brain-аас гаралтай хэсгүүд MIT лицензтэй: `plugins/fm/THIRD_PARTY_NOTICES.md`.

---

## English (short)

The **founder-matrix-os** repo doubles as **soyol**, the private Claude Code marketplace of the Соёл team. Its one plugin, **`fm` (Founder Matrix OS)**, turns each member's personal Obsidian vault (Mongolian content) into a GTD + PARA + atomic-notes system run by role-based Agents. Role notes live in the vault, not in the plugin.

- **v0 (this):** vault engine core: 16 skills, 4 agents, SessionStart context hook, note lint hook (warns on frontmatter/date issues, blocks secrets and misplaced private finance), vault template and `/fm:setup`.
- **v0.2:** Discord relay, Figma, Notion, video watch, research, health checks, calendar.
- **Install:** `gh auth login && gh auth setup-git`, then `/plugin marketplace add rollingbd/founder-matrix-os`, `/plugin install fm@soyol`, `/fm:setup`.
- **Windows:** hooks call `python3` in exec form (no shell); run `uv python install --default`, or install Store Python, or copy `python.exe` to `python3.exe`.
- **Privacy:** personal finance is a private module inside every vault. It never leaves the vault (no git, Discord, STATUS, logs or atoms). Tokens are stored in the OS keychain.
- **License:** proprietary to itge.e / Соёл; MIT notices in `plugins/fm/THIRD_PARTY_NOTICES.md`.
