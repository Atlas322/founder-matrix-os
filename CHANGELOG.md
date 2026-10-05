# Өөрчлөлтийн түүх (CHANGELOG)

Хувилбарын дугаар нь `plugins/fm/.claude-plugin/plugin.json`-ийн `version`. Гишүүд `/plugin marketplace update founder-matrix`-аар шинэчилнэ.

Формат: [Keep a Changelog](https://keepachangelog.com/), [SemVer](https://semver.org/). Ангилал: **Нэмсэн**, **Өөрчилсөн**, **Засварласан**, **Хассан**, **Нууцлал**.

---

## [0.2.0] — 2026-10-05 · Анхны багийн тест

Төвшин, Соёл болон дараа нь SB+AI Season 2-ын сурагчид суулгаж туршина.

### Нэмсэн

- **Амьдралын onboarding** (`/fm:setup`): араг ясаас гадна нэг асуулт нэг удаа ярилцаж SOUL, зорилго (`07-Goals/`), бизнесийн ба хувийн Area-ууд (`04-Areas/Business/`, `04-Areas/Life/`), эхний төслүүд, хүмүүс (`04-Areas/people/`), лавлагаа (`05-Resources/`), хувийн санхүүгийн бүтэц, дүрүүдийг (Agent) бөглөнө.
- **Vault доторх хөдөлгүүрийн өгөгдөл** `_system/fm/`: `registry.json`, `channels.json`, `discord.json`, `state/<төсөл>.md` (baton). Гишүүн бүрийн өгөгдөл өөрийнх нь vault-д.
- **Төхөөрөмжийн тохиргоо** `~/.fmos/config.json` (`vault`, `device`, `member`); `FM_VAULT` орчны хувьсагч vault-ийг дарна.
- **Ерөнхий (generic) Discord relay** (`tools/relay`): гишүүн бүр өөрийн bot, server-тэй; vault mode-д git commit/push хийхгүй; `fmconfig.py`-оор тохиргоо шалгах. Заавар: `docs/discord-relay.md`.
- Figma bridge-ийн заавар: `docs/figma-bridge.md`.
- **Баримт:** шинэ README (суулгах алхам Mac/Windows, өдөр тутмын хүснэгт, нууцлал, асуудал шийдэх), `CONTRIBUTING.md` (сурагчдын PR урсгал), PR болон Issue загварууд.
- **CI** (GitHub Actions): Ubuntu, Windows, macOS × Python 3.9, 3.12 дээр тестүүд, JSON шалгалт, `SKILL.md` frontmatter шалгалт, хувийн зам илрүүлэх; `claude plugin validate --strict plugins/fm` (auth шаардвал алгасна).
- Тестүүд: `tests/test_onboard.py`, `tools/relay/tests/test_relay_config.py`.

### Өөрчилсөн

- `_system/relay/` нь **архив** (хуучин чатын суваг). Шинэ өгөгдөл тэнд бичихгүй.
- Repo-гийн лиценз: root `LICENSE` нэмэгдэж, оролцогчдын хувь нэмрийн нөхцөл тодорхой болсон («Contributions are licensed to itge.e under the same terms»).
- `plugins/fm/README.md` суулгах команд (`fm@founder-matrix`) болон өгөгдлийн хавтас `_system/fm/`-тэй уялдсан.

### Нууцлал

- Хувийн = vault-аас хэзээ ч гарахгүй: registry-д `"private": true` эсвэл `finance` / `tax` / `gold` төслүүд git, Discord, STATUS, лог, атом руу орохгүй.
- Хуваалцах файлуудаас itge.e-ийн хувийн зам, ID-г хассан; CI тэдгээрийг дахин орохоос сэргийлнэ.

---

## [0.1.0] — 2026-10-05 · TEST v0

Анхны хувилбар: зөвхөн vault-ийн цөм хөдөлгүүр, itge.e-ийн Mac + PC дээр туршсан.

### Нэмсэн

- Marketplace **`founder-matrix`** (`.claude-plugin/marketplace.json`) ба plugin **`fm`** (Founder Matrix OS).
- 16 skill: `setup`, `role`, `vault`, `save`, `inbox`, `track`, `update`, `clip`, `daily`, `task`, `project`, `spawn`, `finance`, `bases`, `canvas`, `vault-cli`.
- 4 agent: `resource`, `content-writer`, `creative-director`, `tool-developer`.
- Hook: SessionStart (`_system/BOOT.md` + дүрийн дүрэм ачаалах), PostToolUse (тэмдэглэлийн lint; token болон буруу газрын хувийн санхүүг блоклох).
- Vault загвар (`plugins/fm/vault-template/`): PARA хавтсууд, BOOT, 8 дүрийн тэмдэглэл, загварууд, Bases, хувийн санхүүгийн модуль.
- `tests/test_hooks.py`.
- MIT мэдэгдэл: `plugins/fm/THIRD_PARTY_NOTICES.md`, `plugins/fm/LICENSES/`.

[0.2.0]: https://github.com/rollingbd/founder-matrix-os/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/rollingbd/founder-matrix-os/releases/tag/v0.1.0
