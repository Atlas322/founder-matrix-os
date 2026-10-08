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
| last_seen / working | `_system/fm/state/<project>.md`-ийн `## ОДОО · <YYYY-MM-DD HH:MM> · <session name> (<PC/Mac>)` гарчиг |
| Discord суваг | `_system/fm/channels.json` (+ `discord.json`-ийн guild id) |
| Яриа | өнөөдрийн `_system/logs/<YYYY-MM-DD>.md`-ийн `- **HH:MM** · A → B: текст` мөр |

**working** = тухайн сешний нэр (ба төхөөрөмж) таарсан `ОДОО` гарчиг сүүлийн 20 минутад шинэчлэгдсэн.
Хязгаар: state файлыг зөвхөн `/fm:save`/hook бичдэг тул сешн нээлттэй ч хадгалаагүй бол «сул» харагдана;
гарчиггүй сешн `last_seen = null` (тодорхойгүй). Бодит «одоо ажиллаж байна» дохио vault-д алга.
Лог дахь нэрийг агенттай нэр/project/role-оор тааруулна; таараагүй бол дуудлага зөвхөн bubble болно.

## Нууцлал

- `04-Areas/Business/finances/private/`-ийг огт нээхгүй.
- `private: true` төсөл/сешн, нэр/group/role-д finance/санхүү/personal/home агуулсан сешн алгасна.
- Санхүү, private гэсэн лог мөрийг яриа болгохгүй.
- Business давхарын «Санхүүгийн сан» — зөвхөн түгжээтэй сейф, тоо байхгүй.

## Demo ба бодит

- Бодит: өрөө, stage, status, агент, төхөөрөмж, last_seen, лог дахь яриа (30 с тутам poll).
- Demo: «Demo» товч — бодит агентуудын хооронд санамсаргүй жишээ яриа (текст нь зохиомол) тоглуулна.
- Төв оффис / Wiki / Research өрөө, тавилга нь тогтмол зохиомол дүрслэл.
