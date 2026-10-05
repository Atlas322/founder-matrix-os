---
date: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
type: agent-role
tags:
  - agent-role
ai-first: true
role: <english-kebab-slug>
owns: []
discord: ""
group: projects
skills:
  - "fm:project"
  - "fm:task"
  - "fm:save"
private: false
project:
aliases: []
---

# {{title}}

## For future agent

Нэг төслийн ажлын дүр (`type: agent-role`). Сешн энэ дүрд `/fm:role <slug>`-ээр холбогдоно; сешн ↔ дүрийн зураглал зөвхөн `_system/fm/registry.json`-д. Энэ дүр зөвхөн өөрийн төслийн хавтсанд бичнэ.

## Зорилго

## Эзэмшдэг хавтас

## Дүрэм

1. Ажлаа төслийн `_BRAIN.md`-ээс эхэл: яагаад, дууссан гэж юу вэ, юу хийж болохгүй.
2. Зөвхөн `owns` хавтсанд бичнэ. Бусад хавтас → тухайн дүрд task.
3. Шийдвэр, сургамж → атом ([[03 Resource]]); лог = зөвхөн холбоос.
4. Нийтлэх, илгээх, мөнгө хөдөлгөхөөс өмнө эзэн батална.
5. 🔒 `Life/`, `finances/private/`-ээс юу ч ашиглахгүй.

## Handoff

| Юу | Хэнд |
|---|---|
| Task, хуваарь | [[00 GTD]] |
| Төслийн төлөв, хаах | [[01 Project]] |
| Судалгаа, атом | [[03 Resource]] |
