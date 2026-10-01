# Founder Matrix OS — сешн байгууллага (PARA)

BD-ийн зорилго (2026-10-02): **BD хаана ч (PC / Mac / утас) ажилласан сешнүүд нэг байгууллага шиг эмх цэгцтэй харилцаж, санах ойгоо шинэчлээд зөрөхгүй үргэлжилнэ.**

## 1. Нэг бүтэц — гурван газар ижил

| PARA групп | Claude апп sidebar (PC = Mac) | Discord суваг | Үүрэг |
|---|---|---|---|
| **Tasks** | Tasks | `#tasks` | богино, нэг удаагийн ажил |
| **Projects** | Projects | `#projects` | хугацаатай төсөл (probaitsaa, byd, inai-website…) |
| **Areas** | Areas | `#areas` | байнгын хариуцлага — **admin-ууд**: 00 Inbox, 01 Project, 02 Area, 03 System |
| **Resources** | Resources | `#resources` | лавлах, хэрэгсэл — Creative Director, Wiki |
| (бүгд) | — | `#org` | бүх сешн сонсоно, Mac ↔ PC ↔ BD |
| (төлөв) | — | `#status` | сешн бүрийн амьд төлөв |

Хувийн (Home) сешн: Areas-д, `--private` — Discord/status/git-д юу ч гарахгүй.

## 2. Сешн = ажилтан

`relay/registry.json`: `session_id → {name, group, project, device, private}`.
Нэг төсөл хоёр машин дээр **ижил `project` slug**-тай.

## 3. Харилцаа (Discord, git-гүй)

- Сонсох: hook (`SessionStart`, `UserPromptSubmit`) → `#org` + өөрийн группийн сувгийн шинэ мессеж.
- Тасралтгүй: `relay.py watch` (Monitor).
- Бичих: `relay.py send <org|group> "текст"` → `[сешний нэр] текст`.

## 4. Санах ой — төхөөрөмж солиход зөрөхгүй (baton)

- `state/<project>.md` — **ОДОО** (сүүлийн хүсэлт + хаана зогссон + 📌 дараагийн алхам) ба **ТҮҮХ**.
- `Stop` hook → `relay.py baton` (бичнэ, 5 мин тутам push). `relay.py next "…"` → дараагийн алхмыг тогтооно.
- `SessionStart` → тухайн төслийн ОДОО + сүүлийн 5 түүх контекст болж орно.

## 5. Хэрэгслүүд

| Төрөл | Юу |
|---|---|
| Resource tools | Claude (Code, skills, agents), Discord, GitHub (энэ repo) |
| Project tools | Figma bridge, Framer bridge, skills, Remotion, Poster Maker |
| Хадгалах газар | **Тодорхойгүй (BD шийднэ):** Obsidian vault · Notion · Google Drive. **Бодит байдал (2026-10-02):** Obsidian Sync дууссан → vault PC/Mac тусдаа, зөрж эхэлсэн; медиа → Drive. **Түр дүрэм:** vault = тухайн машины локал ажил; хоёр машинд хэрэгтэй бүхэн (код, тохиргоо, төлөв, шийдвэр) → энэ repo. Медиа/зураг repo-д орохгүй. |

## 6. Нээлттэй асуулт

- Vault-ийн агуулгын синк (git / Sync / Notion) — BD.
- Sidebar группийг машин хооронд автоматаар тулгах (одоо Claude бүр `ccd_sidebar`-аар гараар).
- PC + Mac нийлсэн sidebar панел (Discord `#status` дээр нэг самбар) — дараагийн алхам.
