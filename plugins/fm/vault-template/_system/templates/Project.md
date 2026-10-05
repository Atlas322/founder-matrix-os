---
date: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
type: project
tags:
  - project
ai-first: true
status: active
context: work
area:
goal:
start:
due:
people: []
parent:
subprojects: []
---

# {{title}}

> 📋 Ажлын гарын авлага: [[_BRAIN]]

## For future agent

Энэ төслийн амьд note: явц, одоогийн байдал, task, шийдвэр. Доорх харагдацууд `project:` / `projects:` / `parent:` холбоосоор автоматаар шинэчлэгдэнэ — гараар бүү жагса. Статик гарын авлага (яагаад, дуусах шалгуур, юу хийж болохгүй) [[_BRAIN]]-д.

## Тойм

Нэг догол мөр: юуны тухай төсөл, одоо ямар байна.

## 📋 Task-ууд

```base
filters:
  and:
    - file.inFolder("02-GTD/tasks")
    - type == "task"
    - status != "completed"
    - status != "cancelled"
    - list(project).contains(this)
views:
  - type: table
    name: Энэ төслийн task
    order:
      - file.basename
      - status
      - owner
      - priority
      - due
```

## 🔑 Шийдвэр ба атомууд

```base
filters:
  and:
    - file.inFolder("06-Atomic")
    - list(projects).contains(this)
views:
  - type: table
    name: Атомууд
    order:
      - file.basename
      - type
      - status
      - date
```

## 🤝 Уулзалтууд

```base
filters:
  and:
    - type == "meeting"
    - list(project).contains(this)
views:
  - type: table
    name: Уулзалтууд
    order:
      - file.basename
      - status
      - met
```

## Холбоос

- Гарын авлага: [[_BRAIN]]
