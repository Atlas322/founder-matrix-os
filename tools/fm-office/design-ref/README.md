# design-ref

Figma «Second Brain» файлаас (зөвхөн уншиж) export хийсэн лавлагаа. PNG-үүд том тул `.gitignore`-д; дахин гаргах:
`python plugins/fm/tools/figma/fig.py export <id> --format PNG --scale <s> --out tools/fm-office/design-ref/<нэр>.png`

| Файл | Figma node | Юуг авсан |
|---|---|---|
| inai-home.png | 149:5493 · 03 Нүүр | хуудасны өнгө, «[01] LABEL», Spectral гарчиг цэгтэй, цэнхэр «↗» товч, ✓ tag |
| inai-products.png | 172:8727 · 07 /products | дөрвөлжин 1px карт, #E2DED3 толгой зурвас, шүүлтүүрийн tag, үнэ IBM Plex Mono |
| inai-second-brain.png, inai-about.png | 184:10649, 184:9886 | бичвэрийн хэмжээ, grid шугам |
| barilga.png | 402:24619 · 13 Оффис · Барилга | давхрын мөр (зүүн label + tile), удирдлагын самбар, Key Activity legend |
| shuud.png, guluur.png | 389:21571, 389:21797 | app shell: зүүн nav, дээд мөр (Шууд/Гулсуур/Барилга, «Агентад асуух…», «+ Task»), баруун «Одоо ажиллаж байна» |
| business-room.png, room-ka.png | 389:22279, 402:24520 | өрөөний тохижилт |
| ultra-planner.png | 291:1081 | shell-ийн хэмжээ |

Plugin API-аар уншсан утга (→ `../tokens.css`):
- Дэвсгэр `#F0EDE4`, зурвас `#E2DED3`, гүн `#CFC9BA`; ink `#080808` (+ .85/.55 текст, .10/.15/.20 хүрээ, .07 grid); body `#3D3D3A`; muted `#6B6860`; blue `#1B5CFF`, товчны «↗» `#0F47D6`.
- Хүрээ: 1px, ихэвчлэн ink@10%; цэнхэр tag хүрээ 2.2px. Radius: товч/input 6, карт 0.
- Фонт: Spectral Regular (72/64/48/30/28/24/22, ls −1…−2.5), Inter (Medium 13 товч/nav, Regular 13–16 бие lh145–150%, SemiBold 10–12 UPPERCASE ls .3–.5 label), IBM Plex Mono (тоо, үнэ, «001»).
- Figma Variables (🎨 Foundations) нь ихэнхдээ iOS kit + «Brand/*» (хуучин) тул бодит фреймийн утгыг үндэс болгосон.
