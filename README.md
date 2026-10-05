# Founder Matrix Second Brain

**Founder Matrix Second Brain** нь таны амьдрал, ажлыг нэг Obsidian vault-д цэгцэлж, Claude Code-ийн **Agent**-уудаар (дүрүүдээр) удирддаг систем. Бизнес, хувийн амьдрал, төслүүд, хувийн санхүү, хүмүүс, лавлагаа, зорилго бүгд нэг дор, нэг дүрмээр байна.

Энэ нь **нэг repo**:

| Хэсэг | Юу вэ |
|---|---|
| `plugins/fm/` | Claude Code plugin **`fm`** (marketplace **`founder-matrix`**): skill-үүд (`/fm:…`), agent-ууд, hook-ууд, vault-ийн загвар |
| `tools/` | Нэмэлт хэрэгсэл: Discord relay (`tools/relay`), Figma bridge (`tools/figma`) г.м. Заавал биш |
| `docs/` | Дэлгэрэнгүй заавар (Discord relay, Figma bridge) |
| `tests/` | Python тест (`python3 tests/test_hooks.py` г.м.) |

**Хэнд зориулсан бэ:** Founder Matrix-ийн баг (Төвшин, Соёл…) болон **SB+AI Season 2**-ын сурагчид. Repo нь private, хэрэглэх эрхийг itge.e өгнө ([LICENSE](LICENSE)).

> Төлөв: **v0.2 (тест)**. Анхны багийн тест 2026-10-05. Алдаа, санал байвал [Issue](../../issues) нээгээрэй, засвараа PR-аар илгээгээрэй ([CONTRIBUTING.md](CONTRIBUTING.md)).

---

## `/fm:setup` танд юу өгөх вэ

`/fm:setup` таны хоосон (эсвэл байгаа) vault хавтсанд араг ясыг үүсгээд, тантай **нэг асуулт нэг удаа** ярилцаж амьдралаа эмхэлнэ. Байгаа файлыг хэзээ ч дарж бичихгүй, эхлээд dry-run харуулна.

| Хэсэг | Хаана | Юу |
|---|---|---|
| **Soul** | `01-Soul/SOUL.md` | Та хэн бэ, юуг эрхэмлэдэг, энэ жил юу бүтээх, юу хийхгүй |
| **Зорилго** | `07-Goals/` | Жилийн / улирлын зорилго, төслүүдтэй холбоотой |
| **GTD** | `02-GTD/` | Task (`tasks/`), өдрийн тэмдэглэл (`daily/`), уулзалт, самбар (Work, Personal) |
| **Төслүүд** | `03-Projects/` | Идэвхтэй / төлөвлөж буй / түр зогссон төслүүд (бизнес ба хувийн) |
| **Бизнесийн Area** | `04-Areas/Business/` | Компаниуд, хэрэгслүүд, бизнесийн санхүү |
| **Хувийн Area** | `04-Areas/Life/` | Эрүүл мэнд, гэр бүл, хувийн хөгжил г.м. |
| **Хувийн санхүү** 🔒 | `04-Areas/Business/finances/private/` | Сарын төлбөр, санхүүгийн бичлэг. **Vault-аас хэзээ ч гарахгүй** |
| **Хүмүүс** | `04-Areas/people/` | Хамтрагч, харилцагч, багийн гишүүн бүрийн тэмдэглэл |
| **Лавлагаа** | `05-Resources/` | `references/` (линк, нийтлэл), `library/`, `sources/`, `glossary/` |
| **Атом** | `06-Atomic/` | `decisions/` (шийдвэр), `knowledge/` (ойлголт) |
| **Agent (дүр)** | `04-Areas/AI Team/ai-workers/` | GTD, Project, Area, Resource, Санхүү 🔒, Content Writer, Creative Director, Tool Developer + төсөл тус бүрийн дүр |
| **Хөдөлгүүрийн өгөгдөл** | `_system/fm/` | `registry.json` (сешн ↔ дүр), `channels.json`, `discord.json`, `state/<төсөл>.md` (baton) |

**Бүх сешн нь Agent.** Тэд зөвхөн **дүрээрээ** ялгарна: GTD сешн өдөр тутмын task-ийг, Project сешн төслүүдийг, Санхүү сешн зөвхөн хувийн санхүүг хариуцна. Сешн бүрийг `/fm:role <slug>`-аар нэг дүрд холбоно.

---

## Суулгах (шинэ гишүүн)

Нийт 30–45 минут. Mac болон Windows-д алхам нь ижил, зөвхөн командууд нь өөр.

### 0. Шаардлага

| Юу | Mac | Windows |
|---|---|---|
| **Claude Code** (CLI, desktop апп) | Терминалд: `curl -fsSL https://claude.ai/install.sh \| bash` | PowerShell-д: `irm https://claude.ai/install.ps1 \| iex` |
| **Obsidian** | [obsidian.md](https://obsidian.md) | [obsidian.md](https://obsidian.md) |
| **Git** | `xcode-select --install` (эсвэл `brew install git`) | `winget install Git.Git` (Claude Code-д Git for Windows заавал хэрэгтэй) |
| **GitHub CLI** | `brew install gh` | `winget install GitHub.cli` |
| **Python 3.9+** | macOS-д `python3` аль хэдийн бий (Command Line Tools). Шалга: `python3 --version` | Доорх «Windows дээр `python3`» хэсгийг заавал унш |

Claude Code-ийн бүртгэл (Pro/Max эсвэл багийн эрх) хэрэгтэй. Анх `claude` гэж ажиллуулаад нэвтэрнэ.

#### Windows дээр `python3`

fm-ийн hook-ууд `python3` командыг shell-гүйгээр шууд дууддаг. python.org-ийн суулгагч зөвхөн `python.exe`, `py.exe` өгдөг тул `python3` олдохгүй байж болно. Аль нэгийг хий:

1. **uv** (санал болгох): `winget install astral-sh.uv` → шинэ PowerShell нээгээд `uv python install 3.12 --default`. `%USERPROFILE%\.local\bin`-д `python.exe`, `python3.exe` үүснэ; тэр хавтас PATH-д байх ёстой (`uv python update-shell`).
2. Microsoft Store-оос **Python 3.12** суулгах (жинхэнэ `python3.exe` өгнө). Settings → Apps → Advanced app settings → **App execution aliases** дотор `python3.exe` нь Store-ийн хоосон stub биш, суусан Python руу заасан эсэхийг шалга.
3. Python-ий хавтсанд `python.exe`-г хуулж `python3.exe` гэж нэрлэх.

Шалгах: **шинэ** PowerShell дээр `python3 --version` → `Python 3.x.x` гарах ёстой.

### 1. GitHub эрх

1. GitHub бүртгэлийнхээ нэрийг itge.e-д өг. Тэр таныг `rollingbd/founder-matrix-os` repo-д урина.
2. Имэйл эсвэл github.com/notifications дээр урилгыг **Accept** хий.
3. Терминал (Mac) / PowerShell (Windows) дээр:
   ```
   gh auth login
   gh auth setup-git
   ```
   Шалгах: `git ls-remote https://github.com/rollingbd/founder-matrix-os` алдаагүй ажиллах ёстой.

### 2. Vault хавтас бэлдэх

Vault = таны бүх тэмдэглэл байх нэг хавтас. Жишээ нь:

- Mac: `~/Documents/Second Brain` эсвэл Google Drive дотор `~/My Drive/Second Brain`
- Windows: `C:/Users/<нэр>/Documents/Second Brain` эсвэл `G:/My Drive/Second Brain`

Хоосон хавтас үүсгээд Obsidian дээр **Open folder as vault** гэж нээ. Хоёр төхөөрөмж дээр ажиллах бол Google Drive (Mirror files) зэрэг sync ашиглаж болно, гэхдээ **нэг зэрэг хоёр машин дээр бичихгүй** (Drive `(1)` давхар файл үүсгэнэ).

### 3. Plugin суулгах

Claude Code CLI-г (терминалд `claude`) нээгээд:

```
/plugin marketplace add rollingbd/founder-matrix-os
/plugin install fm@founder-matrix
/reload-plugins
```

Суулгах үед гурван тохиргоо асууна:

| Тохиргоо | Жишээ | Тайлбар |
|---|---|---|
| `vault_path` | `/Users/you/Documents/Second Brain` | **Заавал.** Vault хавтасны бүтэн зам |
| `member` | `Tuvshin` | Таны нэр/товч нэр. Task-ийн owner, STATUS-д гарна |
| `device` | `Mac` эсвэл `PC` | Энэ төхөөрөмжийн шошго, сешний гарчигт гарна |

`discord_token`, `notion_token`, `figma_token` хоосон үлдээж болно.

Суусны дараа desktop апп-ын Code хэсэг ч мөн адил `~/.claude` тохиргоог ашиглана.

### 4. Төхөөрөмжийн тохиргоо `~/.fmos/config.json`

Tools (relay г.м.) болон зарим script vault-аа энэ файлаас олно. Нэг удаа үүсгэ:

- Mac: `~/.fmos/config.json`
- Windows: `%USERPROFILE%\.fmos\config.json`

```json
{
  "vault": "/Users/you/Documents/Second Brain",
  "device": "Mac",
  "member": "Tuvshin"
}
```

Windows дээр замыг `/`-ээр бич: `"vault": "C:/Users/you/Documents/Second Brain"`. Түр өөр vault ашиглах бол `FM_VAULT` орчны хувьсагч энэ файлыг дарна.

### 5. Vault-аа эхлүүлэх

Claude Code-ийг **vault хавтас дотроос** нээ:

```
cd "/Users/you/Documents/Second Brain"     # Windows: cd "C:/Users/you/Documents/Second Brain"
claude
```

Дараа нь:

```
/fm:setup
```

Setup эхлээд юу үүсэхийг (dry-run) харуулна → та зөвшөөрнө → араг яс үүснэ → дараа нь тантай ярилцаж SOUL, зорилго, бизнес ба хувийн Area-ууд, эхний төслүүд, хүмүүс, санхүүгийн бүтэц, дүрүүдийг бөглөнө. Мэдэхгүй зүйлдээ «TBD» гэж хариулж болно, дараа нь нөхнө.

### 6. Obsidian тохиргоо (гараар, нэг удаа)

- Settings → Core plugins → **Templates** асаагаад template folder-ийг `_system/templates` болго.
- **Bases** core plugin-ийг асаа (`_system/bases/*.base` харагдацууд).
- Community plugins → **Kanban** суулга (`02-GTD/boards/`).

fm нь `.obsidian/` хавтсанд хэзээ ч хүрэхгүй. Obsidian-ийн тохиргоо бүрэн таных.

### 7. Эхний сешн

Шинэ сешн бүрт «дүргүй» гэж гарвал дүрээ сонго:

```
/fm:role gtd
```

Эхлэхэд GTD сешн нэг байхад хангалттай. Санхүүд тусдаа сешн нээгээд `/fm:role finance`.

---

## Өдөр тутмын хэрэглээ

| Команд | Хэзээ | Жишээ |
|---|---|---|
| `/fm:daily` | Өглөө өдрөө эхлүүлэх | «өдрөө эхлүүлье» |
| `/fm:inbox` | `00-Inbox`-ийг цэгцлэх (эхлээд төлөвлөгөө, баталсны дараа л зөөнө) | «inbox цэгцэл» |
| `/fm:task` | Task үүсгэх, авах 🙋, дуусгах ✅, жагсаах | «маргааш Бат-д нэхэмжлэл явуулах task үүсгэ» |
| `/fm:project` | Төсөл үүсгэх, төлөв солих, хаах, самбар цэгцлэх | «шинэ төсөл: вэбсайт» |
| `/fm:save` | Яриаг дуусгахдаа бүгдийг хадгалах (шийдвэр, task, хүн, линк) | «бүгдийг хадгал» |
| `/fm:track` | Ярианы дундуур checkpoint, яриа үргэлжилнэ | «одоог хүртэлхийг барьж ав» |
| `/fm:update` | Сешний төлөв: юу хийсэн → хаана зогссон → дараагийн алхам | «өдрийн дүгнэлт» |
| `/fm:finance` 🔒 | Сарын төлбөр, санхүүгийн бичлэг (зөвхөн Санхүү сешнд) | «энэ сард юу төлөөгүй вэ» |
| `/fm:role` | Сешнийг дүрд холбох, дүрүүдийг харах | `/fm:role project` |
| `/fm:clip` | Линкийг лавлагаа + атом болгох | «энэ линкийг атом болго» |
| `/fm:spawn` | Шинэ сешн үүсгэхээс өмнөх шалгалт | «төслийн сешн үүсгэе» |
| `/fm:canvas`, `/fm:bases`, `/fm:vault-cli` | Canvas зураг, Bases харагдац, Obsidian CLI | |

Slash команд санахгүй байсан ч болно: «хадгал», «inbox цэгцэл», «task үүсгэ» гэж монголоор бичихэд тохирох skill өөрөө ажиллана.

**Энгийн өдөр:** `/fm:daily` → ажил → шинэ зүйл бүрийг `00-Inbox`-д шидэх → `/fm:inbox` → оройд `/fm:update` «өдрийн дүгнэлт» → `/fm:save`.

---

## Нууцлалын загвар

- **Хувийн** гэдэг нь **vault-аас хэзээ ч гарахгүй** гэсэн үг: git, Discord, `_system/STATUS.md`, лог, daily note, атом руу хэзээ ч орохгүй.
- Хувийн гэж тооцогдох зүйл: `_system/fm/registry.json`-д `"private": true` гэсэн сешн/төсөл, мөн `finance`, `tax`, `gold` төслүүд, `04-Areas/Business/finances/private/` хавтас.
- Хувийн санхүүг зөвхөн `role: finance` сешн уншиж, бичнэ. Бусад дүр зөвхөн «N хувийн зүйл байна» гэж тоолно.
- Данс, картын дугаар, нууц үг, token хэзээ ч тэмдэглэлд бичигдэхгүй. Lint hook token шиг мөр болон хувийн хавтсаас гадуурх санхүүгийн тэмдэглэлийг **блоклоно**.
- Token-ууд (`*_token`) нь plugin-ийн `sensitive` тохиргоо тул OS keychain-д хадгалагдана, эсвэл таны home хавтсанд (`~/.fmos_discord_token` г.м.), **repo-д хэзээ ч биш**.
- Таны vault **таных**: repo-д vault-ийн агуулга хэзээ ч орохгүй. PR-д хувийн тэмдэглэл, token, харилцагчийн мэдээлэл оруулахыг хатуу хориглоно.
- Анхаар: vault хавтсаа бүхэлд нь (Google Drive г.м.) бусадтай share хийвэл хувийн хавтас ч хамт явна.

---

## Шинэчлэх

```
/plugin marketplace update founder-matrix
/reload-plugins
```

Эсвэл автоматаар: `/plugin` → Marketplaces → `founder-matrix` → **Enable auto-update**. Шинэ хувилбар юу авчирсныг [CHANGELOG.md](CHANGELOG.md)-ээс хар. Шинэчлэл таны vault-ийн байгаа файлыг дарж бичихгүй; шинэ загвар авах бол `/fm:setup`-ийг дахин ажиллуулахад зөвхөн дутуу файлуудыг нэмнэ.

`tools/`-ийг (relay, Figma) ашигладаг бол repo-гийн clone дотроо `git pull`.

---

## Асуудал шийдэх

| Шинж тэмдэг | Шалтгаан / шийдэл |
|---|---|
| `/plugin marketplace add` алдаа (`not found`, `authentication`) | Repo private. Урилгаа accept хийсэн эсэх, `gh auth login` + `gh auth setup-git` хийсэн эсэхээ шалга. `git ls-remote https://github.com/rollingbd/founder-matrix-os` ажиллах ёстой |
| `/fm:` команд харагдахгүй | `/reload-plugins` эсвэл Claude Code-ийг дахин нээ. `/plugin` → Installed дотор `fm` идэвхтэй эсэхийг шалга |
| Сешн эхлэхэд hook алдаа, `python3` олдсонгүй (Windows) | Дээрх «Windows дээр `python3`» хэсэг. Hook алдаа сешнийг блоклохгүй, гэхдээ context ачаалалт, lint ажиллахгүй |
| «Vault олдсонгүй» / буруу vault | Plugin-ийн `vault_path` тохиргоо (`/plugin` → Installed → fm), `~/.fmos/config.json`, эсвэл `FM_VAULT`-ийг шалга. Claude Code-ийг vault хавтас дотроос нээ |
| Сешн бүрт «дүргүй» гэж гарна | `/fm:role gtd` (эсвэл өөр дүр). Дүр `_system/fm/registry.json`-д хадгалагдана |
| Тэмдэглэл бичихэд «blocked» гэж гарна | Lint hook token эсвэл хувийн санхүүг буруу газар бичихийг зогсоосон. Мессежийг уншаад зөв хавтсанд бич |
| Google Drive дээр `файл (1).md` давхардал | Хоёр машин зэрэг бичсэн. Нэгийг нь үлдээж нэгтгэ, цаашид нэг удаа нэг машин дээр бич |
| Template, Kanban ажиллахгүй | Obsidian-д Templates (`_system/templates`), Bases, Kanban асаасан эсэх |

Шийдэгдэхгүй бол [Issue](../../issues/new/choose) нээ: OS, Claude Code-ийн хувилбар (`claude --version`), `python3 --version`, алдааны текстийг хавсарга (хувийн мэдээлэлгүйгээр).

---

## Нэмэлт (advanced)

### Discord relay (v0.2)

Сешнүүд (Mac ↔ PC, утаснаас) Discord-оор харилцаж, төлвөө хуваалцана. **Гишүүн бүр өөрийн bot, өөрийн Discord server**-тэй; өгөгдөл нь vault-ийн `_system/fm/`-д, тохиргоо нь `~/.fmos/config.json`-д. Хувийн сешн, төсөл Discord руу хэзээ ч орохгүй. Алхам: [docs/discord-relay.md](docs/discord-relay.md).

### Figma bridge (`tools/figma`)

Figma desktop + локал dev plugin-оор Claude Figma-д зурж, засаж, export хийнэ. Node.js хэрэгтэй, туршлагатай хэрэглэгчдэд. Алхам: [docs/figma-bridge.md](docs/figma-bridge.md).

---

## Хөгжүүлэгчид

Энэ repo нь анх itge.e-ийн Founder.Matrix vault-ийн **хөдөлгүүр** байсан (системийн тохиргоо, ажиллах зарчим, tools, Mac ↔ PC relay). Vault-ийн агуулга (тэмдэглэл) энд **орохгүй**.

| Хавтас | Юу |
|---|---|
| `.claude-plugin/marketplace.json` | marketplace `founder-matrix` |
| `plugins/fm/` | plugin `fm`: `skills/`, `agents/`, `hooks/`, `scripts/`, `vault-template/` ([plugins/fm/README.md](plugins/fm/README.md)) |
| `tools/` | relay, Figma/Framer bridge, sidepanel, notion, save-to-inbox… |
| `tests/` | `python3 tests/test_hooks.py`, `python3 tests/test_onboard.py` |
| `docs/` | Нэмэлт заавар |
| `relay/`, `state/`, `vault/`, `claude/` | itge.e-ийн v0 хөдөлгүүрийн файлууд (хуучин бүтэц). Гишүүд эдгээрийг ашиглахгүй, PR-аар өөрчлөхгүй. Гишүүн бүрийн хөдөлгүүрийн өгөгдөл өөрийнх нь vault-ийн `_system/fm/`-д байна |

Хөгжүүлэлт: `claude --plugin-dir plugins/fm` (суулгалгүй ачаална), `claude plugin validate --strict plugins/fm`. CI: [.github/workflows/ci.yml](.github/workflows/ci.yml) (Ubuntu, Windows, macOS × Python 3.9, 3.12). Хувь нэмэр оруулах: [CONTRIBUTING.md](CONTRIBUTING.md).

> ⚠️ Repo-д шинэ гишүүнд эрх өгөхөөс өмнө: git түүхэнд `state/`, `relay/registry.json` зэрэг itge.e-ийн хувийн мэдээлэл бий. Түүхийг цэвэрлэх (filter-repo + force-push) эсвэл цэвэр шинэ repo-оос тараах алхмыг itge.e батална.

## Лиценз

Copyright (c) 2026 itge.e. All rights reserved. Founder Matrix баг болон SB+AI Season 2-ын оролцогчдод ашиглах эрхтэй. Хувь нэмэр (PR) нь мөн ийм нөхцлөөр itge.e-д лицензлэгдэнэ. MIT лицензтэй гуравдагч талын хэсгүүд: [plugins/fm/THIRD_PARTY_NOTICES.md](plugins/fm/THIRD_PARTY_NOTICES.md). Бүтэн текст: [LICENSE](LICENSE).

---

## English (short)

**Founder Matrix Second Brain** organizes a member's whole life and work in one personal Obsidian vault (Mongolian content), run by role-based Claude Code **Agents**. One repo holds the Claude Code plugin **`fm`** (marketplace **`founder-matrix`**, in `plugins/fm/`) and optional tools (`tools/relay` Discord relay, `tools/figma` Figma bridge). It is for the Founder Matrix team and SB+AI Season 2 students; the repo is private.

- **What `/fm:setup` gives you:** a PARA + GTD vault with business and personal Areas, Projects, a private Finance module, People, References, Goals, atomic notes, and role notes (GTD, Project, Area, Resource, Finance, Content Writer, Creative Director, Tool Developer, per-project roles). Engine data lives in the vault at `_system/fm/`. It never overwrites existing files and shows a dry run first.
- **Install:** Claude Code + Obsidian + Git + GitHub CLI + Python 3.9+. `gh auth login && gh auth setup-git`, then in Claude Code: `/plugin marketplace add rollingbd/founder-matrix-os`, `/plugin install fm@founder-matrix` (set `vault_path`, `member`, `device`), create `~/.fmos/config.json` (`{"vault", "device", "member"}`; `FM_VAULT` overrides), open Claude Code in the vault folder, run `/fm:setup`, then `/fm:role gtd`.
- **Windows:** hooks call `python3` directly (no shell). Use `uv python install 3.12 --default`, Microsoft Store Python, or copy `python.exe` to `python3.exe`.
- **Daily:** `/fm:daily`, `/fm:inbox`, `/fm:task`, `/fm:project`, `/fm:save`, `/fm:track`, `/fm:update`, `/fm:finance` (private), `/fm:role`.
- **Privacy:** private items (registry `"private": true`, finance/tax/gold projects, `finances/private/`) never leave the vault: no git, Discord, STATUS, logs or atoms. Tokens live in the OS keychain or the home folder, never in the repo.
- **Update:** `/plugin marketplace update founder-matrix`, then `/reload-plugins`.
- **Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md). **License:** proprietary to itge.e, see [LICENSE](LICENSE); MIT notices in `plugins/fm/THIRD_PARTY_NOTICES.md`.
