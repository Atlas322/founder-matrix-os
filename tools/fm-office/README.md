# FM Office (2.5D + 3D прототип)

Цаглабар (Inai Operation App)-ын «Оффис» модуль. Vault = барилга, давхар = PARA, төсөл бүр = өрөө
(дотор нь одоогийн stage / Key Activity), агент сешн = ширээнд суугаа хүн. Three.js r160 (CDN, importmap), build алхамгүй.

## Хувилбарууд

- `/` — **2.5D** (үндсэн): батлагдсан C-style зурагнууд (`assets/img/*.webp`, ≤1600px).
  - **Барилга**: давхар бүр хүрээтэй хэсэг, төсөл = stage-ийн зурагтай tile (шатгүй/зогссон = саарал, архив = харанхуй), цех = «N төсөл».
  - **Өрөө** (tile дээр дарах): том зураг + parallax, агентын тэмдэг `assets/hotspots.json`-ийн ширээний цэгүүд дээр
    (ажиллаж = ногоон гэрэл, сул = бүдэг), өрөөний яриа bubble, хажуугийн карт. Esc / «Буцах».
  - **Оффис**: тойм зураг + бүсийн шошго + агентын цэг + SVG нум/bubble, «Яриа» самбар.
  - **Өрөө = дашбоард** (`GET /api/room?id=`): жижиг зураг + агентын цэг, нэр/шат/төлөв/due; Шат (5 Key Activity stepper +
    `milestones`), Task-ууд (`01-GTD/Tasks/`, fallback `02-GTD/tasks/`, `project:` холбоосоор; статусаар бүлэг, 7 хоногт дууссан),
    Сешнүүд (baton: хаана зогссон / дараагийн алхам; Discord, Мессеж илгээх, Сэрээх), Сүүлийн яриа, Холбоос (obsidian://, _BRAIN, figma/repo/url).
    Цех → тухайн шатны төслүүд + task-ын товч. Номын сан/Сейф → жижиг карт.
- **Илгээх** (`POST /api/send`, `sender.py`): `{room, kind: message|wake, channel, target, text, confirm: true}`.
  Сервер шалгана: confirm заавал, текст 1–1500, суваг = тухайн өрөөний төслийн суваг эсвэл `gtd` (finance/private хориотой),
  Origin = localhost, 10 с-д 1 / цагт 20. Relay-тэй ижил Discord API-аар (token `~/.fmos_discord_token` зөвхөн сервер)
  `<текст>
-# 🖥️ PC · FM Office` гэж бичнэ. «Сэрээх» = `#gtd`-д `→ <сешн> @pc|@mac: <текст>` (dispatcher сэрээнэ).
  UI: «Илгээх…» → «Баталгаажуул: #суваг руу илгээх» гэсэн 2 дахь товшилт.
- `/3d` — хуучин Three.js хувилбар (`index.html` + `main.js`).
- `assets/hotspots.json` — зураг бүрийн ширээний цэг, оффисын бүс (%), нэргүй. Тест: `tests/test_hotspots.py`.

## Ажиллуулах

```
python server.py --vault "D:/My Drive/Second Brain 2.0" --port 5191
```
→ http://localhost:5191 . Vault-ийн `.claude/launch.json`-д `fm-office` гэж бүртгэлтэй.
Тест: `python -m unittest discover -s tests`

## Өгөгдөл (зөвхөн уншина, юу ч бичихгүй)

| Юу | Хаанаас |
|---|---|
| Төслийн өрөө, status, stage | `02-Projects/<Name>/<Name>.md` (хуучин `{1-Active,2-Planning,3-On-hold}/` дэд хавтас ч уншина) frontmatter `status`, `stage: "[[…/activities/<Activity>]]"` |
| Архивын харанхуй өрөө | `99-Archive/Projects/*` |
| Key Activity цехийн ачаалал | тухайн stage-тэй төслийн тоо |
| Агент | `_system/fm/registry.json` → `sessions` |
| slug → төслийн нэр, Research slug-ууд | `_system/fm/fm-office.json` (vault-д; загвар нь `fm-office.example.json`). Repo-д төсөл, харилцагчийн нэр бичихгүй |
| last_seen / working | `_system/fm/state/<project>.md`-ийн `## ОДОО · <YYYY-MM-DD HH:MM> · <session name> (<PC/Mac>)` гарчиг |
| Discord суваг | `_system/fm/channels.json` (+ `discord.json`-ийн guild id) |
| Яриа (1) | relay Discord: `channels.json`-ийн сешн сувгууд + #gtd + идэвхтэй thread-ууд, сүүлийн 24 цаг, ≤50, 60 с cache (арын thread-ээр). Token (`~/.fmos_discord_token`) зөвхөн сервер талд (`discord_feed.py`) |
| Яриа (2) | өнөөдрийн `_system/logs/<YYYY-MM-DD>.md`-ийн `- **HH:MM** · A → B: текст` мөр |

**working** = тухайн сешний нэр (ба төхөөрөмж) таарсан `ОДОО` гарчиг сүүлийн 20 минутад шинэчлэгдсэн.
Хязгаар: state файлыг зөвхөн `/fm:save`/hook бичдэг тул сешн нээлттэй ч хадгалаагүй бол «сул» харагдана;
гарчиггүй сешн `last_seen = null` (тодорхойгүй). Бодит «одоо ажиллаж байна» дохио vault-д алга.
Лог дахь нэрийг агенттай нэр/project/role-оор тааруулна; таараагүй бол дуудлага зөвхөн bubble болно.

## Харагдац

- Ачаалахад Projects давхарт төвлөрнө; «Бүгд» бүх барилгыг дэлгэцэнд багтаана.
- Projects: stage → нэрээр эрэмбэлсэн 2–3 мөрийн grid; stage-гүй эсвэл on-hold/someday төсөл нь
  жижиг саарал «Шатгүй / Зогссон» бүлэгт (дээд мөрийн товчоор нууна).
- Өрөө/агентын шошго зөвхөн hover, сонголт эсвэл ойртуулсан үед; давхцвал нуугдана
  (эрэмбэ: сонгосон > ажиллаж буй агент > өрөө). Давхрын нэр үргэлж харагдана.

## Нэр ба цаг

- Харуулах нэр = одоогийн дүрийн бүтэц: `plugins/fm/sidebar.json` (role → «🏛️ Architect», «📥 GTD» …),
  дүрийн note-уудын `aliases:` (`_system/fm/agents/`, fallback `03-Areas/AI Team/ai-workers/`), vault-ийн
  `fm-office.json` → `names` (хуучин → шинэ). Ижил нэр + төхөөрөмжтэй сешнүүд нэг агент болно; PC/Mac нь badge.
  Хуучин нэрс (footer, хаяглалт)-ийг сервер талын `keys`-ээр тааруулна, client руу явуулахгүй.
- Discord-ийн UTC цагийг машины tz (UB = UTC+8) руу `astimezone()`-оор хөрвүүлнэ: `ts`, `hhmm`, `iso` (offset-той);
  24 цагийн цонх ч локал. Логийн мөр аль хэдийн локал тул шилжүүлэхгүй.

## Discord мессежийг задлах

- Зохиогч: footer `-# 🖥️ PC · 🏛️ Architect` / `🍎 Mac · 📥 GTD`, хуучин prefix `🖥️ [Name · PC]`; footer-гүй бот → сувгийн эзэн (тэр төхөөрөмжийн).
  Хүн (bot биш, эсвэл «bd») → itge.e (Төв оффисын урд ширээнд).
- Хүлээн авагч: `→ PC (Architect)`, `→ Mac @mac`, `for pc`, `@architect`; хаяггүй бол itge.e → сувгийн эзэн, агент өөрийн сувагт → itge.e.
- Төрөл: `🙋` авлаа, `✅` дууслаа (ногоон pulse), `itge.e`, бусад `Discord`. Текст ≤80 тэмдэгт; түүхий JSON browser руу явахгүй.

## Нууцлал

- `03-Areas/Business/finances/private/`-ийг огт нээхгүй.
- `private: true` төсөл/сешн, нэр/group/role-д finance/санхүү/personal/home агуулсан сешн алгасна.
- Санхүү, private гэсэн лог мөрийг яриа болгохгүй.
- Discord: business / personal / 💰 / finance / санхүү сувгийг уншихгүй; агентын жагсаалтад байхгүй (private) сешний мессежийг алгасна.
- Business давхарын «Санхүүгийн сан» — зөвхөн түгжээтэй сейф, тоо байхгүй.

## Demo ба бодит

- Бодит: өрөө, stage, status, агент, төхөөрөмж, last_seen, лог дахь яриа (30 с тутам poll).
- Demo: «Demo» товч — бодит агентуудын хооронд санамсаргүй жишээ яриа (текст нь зохиомол) тоглуулна.
- Төв оффис / Wiki / Research өрөө, тавилга нь тогтмол зохиомол дүрслэл.
