---
date: {{date:YYYY-MM-DD}}
type: finance-record
tags:
  - finance-record
ai-first: true
kind: expense
amount: 0
currency: MNT
txn-date: {{date:YYYY-MM-DD}}
due:
status: draft
scope: personal
private: true
project:
company:
doc:
recurs:
---

# {{title}}

## For future agent

Нэг санхүүгийн бичлэг = нэг файл. `kind`: invoice | payment | expense | subscription | salary. Анхдагч нь 🔒 хувийн: `scope: personal` + `private: true` → `04-Areas/Business/finances/private/`. Багийн бичлэг бол `scope: team` + `private: false` болгож `04-Areas/Business/finances/`-д хадгална (lint үүнийг л гадуур зөвшөөрнө). `salary` үргэлж хувийн.

- `date` = үүсгэсэн огноо, `txn-date` = гүйлгээний огноо — хольж болохгүй.
- `amount` цэвэр тоо, `currency` тусад нь («1 сая» гэх мэт текст биш).
- `status`: draft | sent | paid | overdue | cancelled.
- ⛔ Данс, картын дугаар, нууц үг бичихгүй.

## Тэмдэглэл
