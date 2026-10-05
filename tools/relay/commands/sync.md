---
description: FMOS — бүх сешн (PC+Mac) нэг газраас мэдээлэл аваад өөрийн төлөвөө шинэчилнэ
---
FMOS-ийн нэг эх сурвалж = vault `_system/STATUS.md` (+ дэлгэрэнгүй түүх `_system/logs/<өнөөдөр>.md`). Discord бол зөвхөн мэдэгдлийн суваг.

Дарааллаар хий:
1. **Өөрийн мөрөө шинэчил** — нэг өгүүлбэрээр «юу хийсэн → хаана зогссон → дараагийн алхам»:
   `python <repo>/tools/relay/relay.py next "<өгүүлбэр>" --sid <өөрийн cli session id>`
   (`<repo>` = энэ repo-г clone хийсэн хавтас. Mac дээр `python3`. Vault/төхөөрөмж/нэр: `~/.fmos/config.json`, шалгах: `python <repo>/tools/relay/fmconfig.py`.)
2. **Hub-ийг дахин үүсгэ:** `python <repo>/tools/relay/relay.py hub`
3. **Уншаад** vault `_system/STATUS.md` + өнөөдрийн `_system/logs/`-ийг уншиж, ЭНЭ сешнд хамаатай өөрчлөлт (өөр сешн чамаас юм хүлээж байгаа, давхардсан ажил, шийдвэр) байвал BD-д 3 мөрөөр хэл.
4. Өнөөдрийн лог руу нэг мөр нэм (Read → Edit, хэзээ ч Write-аар дарж бичихгүй): `**HH:MM** - sync · <сешний нэр>: <өгүүлбэр>`.
5. Өөрийн Discord суваг руу нэг мөр: `relay.py send <суваг> "🔄 sync: <өгүүлбэр>" --sid <sid>`.

Аргумент өгвөл ($ARGUMENTS) түүнийг 1-р алхамын өгүүлбэр болгон ашигла.
