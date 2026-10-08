# FM Office (3D прототип)

Цаглабар (Inai Operation App)-ын «Оффис» модуль. Vault = барилга, давхар = PARA, төсөл бүр = өрөө
(дотор нь одоогийн stage / Key Activity), агент сешн = ширээнд суугаа хүн. Three.js r160 (CDN, importmap), build алхамгүй.

## Ажиллуулах

```
python server.py --vault "D:/My Drive/Second Brain 2.0" --port 5191
```
→ http://localhost:5191 . Vault-ийн `.claude/launch.json`-д `fm-office` гэж бүртгэлтэй.
Тест: `python -m unittest discover -s tests`

## Өгөгдөл (зөвхөн уншина, юу ч бичихгүй)

| Юу | Хаанаас |
|---|---|
| Төслийн өрөө, status, stage | `03-Projects/{1-Active,2-Planning,3-On-hold}/<Name>/<Name>.md` frontmatter `status`, `stage: "[[…/activities/<Activity>]]"` |
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

## Discord мессежийг задлах

- Зохиогч: footer `-# 🖥️ PC · 🏛️ Architect` / `🍎 Mac · 📥 GTD`, хуучин prefix `🖥️ [Name · PC]`; footer-гүй бот → сувгийн эзэн (тэр төхөөрөмжийн).
  Хүн (bot биш, эсвэл «bd») → itge.e (Төв оффисын урд ширээнд).
- Хүлээн авагч: `→ PC (Architect)`, `→ Mac @mac`, `for pc`, `@architect`; хаяггүй бол itge.e → сувгийн эзэн, агент өөрийн сувагт → itge.e.
- Төрөл: `🙋` авлаа, `✅` дууслаа (ногоон pulse), `itge.e`, бусад `Discord`. Текст ≤80 тэмдэгт; түүхий JSON browser руу явахгүй.

## Нууцлал

- `04-Areas/Business/finances/private/`-ийг огт нээхгүй.
- `private: true` төсөл/сешн, нэр/group/role-д finance/санхүү/personal/home агуулсан сешн алгасна.
- Санхүү, private гэсэн лог мөрийг яриа болгохгүй.
- Discord: business / personal / 💰 / finance / санхүү сувгийг уншихгүй; агентын жагсаалтад байхгүй (private) сешний мессежийг алгасна.
- Business давхарын «Санхүүгийн сан» — зөвхөн түгжээтэй сейф, тоо байхгүй.

## Demo ба бодит

- Бодит: өрөө, stage, status, агент, төхөөрөмж, last_seen, лог дахь яриа (30 с тутам poll).
- Demo: «Demo» товч — бодит агентуудын хооронд санамсаргүй жишээ яриа (текст нь зохиомол) тоглуулна.
- Төв оффис / Wiki / Research өрөө, тавилга нь тогтмол зохиомол дүрслэл.
