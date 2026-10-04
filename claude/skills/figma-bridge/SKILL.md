---
name: figma-bridge
description: Draw, edit, animate (Smart Animate prototypes) and export in Figma through a free local bridge (Figma dev plugin + CLI) - no Figma MCP plan limits. Use whenever the user wants something created or changed inside Figma, Figma prototypes/animations, or bulk export of Figma frames/images (read-only bulk export can also use the REST CLI figma.py).
---

# Figma bridge (local, unlimited)

Tools live in the vault: `<OLD-VAULT>\_system\tools\figma\` (Mac: same path inside the vault).

| Need | Tool |
|---|---|
| Create / edit / animate in Figma | `fig.py run` → local plugin (full Figma Plugin API) |
| Export one node as PNG/SVG/PDF | `fig.py export <nodeId>` |
| Bulk read / export whole files, original image fills | `figma.py` (REST, token in `~/.figma_token`) |

Prefer these over the claude.ai Figma MCP connector - that one is capped on the user's Starter plan.

## Start-up — decision tree (follow exactly, every session)

⛔ NEVER use the Figma MCP connector (get_screenshot, use_figma…) — Starter plan limit, itge.e built this bridge to avoid it.

```
python fig.py status
├─ {'server': False}            → Bash run_in_background: cd <tools>/figma && node bridge/server.mjs ; wait 4s ; status again
├─ {'plugin': False}            → Figma desktop: computer-use open_application "Figma" (granted app).
│                                  The Claude Bridge panel is often already open — it reconnects by itself within ~5s after the
│                                  server starts; run status again. Still False → in Figma: ctrl+/ → type "Claude Bridge" → Enter.
│                                  No computer-use access / user away → tell itge.e on Discord, do not fall back to MCP.
├─ plugin True, file 'active': False → still works for run/export (tab need not be focused). If export errors with
│                                  "Unable to establish connection to Figma", click the file's tab in Figma once, retry.
└─ plugin True                  → ready
```

Node IDs written in vault notes go stale (frames get rebuilt). Never trust an id blindly:
`await figma.loadAllPagesAsync(); return figma.root.findAll(n => n.type==='FRAME' && /<name>/.test(n.name)).map(n => n.id+' '+n.name)`
`getNodeByIdAsync` returning null / "exportAsync of null" = stale id → search by name as above.

### Known files (2026-10-05)
| File | key | Pages that matter |
|---|---|---|
| **Second Brain** (Team project) | `FIGMA_FILE_KEY` | 🎨 Foundations · 🧩 Components base/Inai · 📱 Screens (🌐 Inai Website) · 📅 Цаглабар · 🖼 Moodboards (**MB · itge.e mindset 37:2526** = itge.e-ийн Soul) · 🔍 Research · 🪄 Poster Maker · 🗂 Post library |
| BYD-Website | `FIGMA_FILE_KEY` | BYD design system |
| Assets | `FIGMA_FILE_KEY` | studio assets |

Inai Website desktop frames (Second Brain): 149:5493 Нүүр · 172:8727 /products · 184:9059 /products/inai-second-brain · 184:9435 /work · 184:9609 /work/byd-mongolia · 184:9886 /about · 184:10125 /marketing · 184:10506 /journal · 184:10649 /second-brain · 184:10977 /learn · 229:888 /learn v2.
File keys of other files: `%APPDATA%\Figma\settings.json` → search `"/file/<key>"` next to `"title":"<name>"`.

### Sending results to itge.e
Export JPG (`fig.py export <id> --format JPG --scale 1 --out <scratchpad>\x.jpg`, keep < 10MB, else scale 0.75) and upload
to Discord as an attachment (POST /channels/{id}/messages multipart, token `~/.fmos_discord_token`). itge.e wants real
exported JPGs of frames, not desktop screenshots.

First-time plugin install: **Plugins → Development → Import plugin from manifest…** → `_system\tools\figma\bridge\plugin\manifest.json`.

## Running code

`python fig.py run "<js>"` or `python fig.py run -f script.js`. The code is the body of an async
function with `figma` (Plugin API) and `store` (persists while the plugin is open). `return` a value;
nodes serialize as `{id,type,name}`.

Rules that bite:
- Load fonts before touching text: `await figma.loadFontAsync({family:'Inter',style:'Regular'})`.
- Use async getters: `await figma.getNodeByIdAsync(id)`; for other pages `await page.loadAsync()`.
- Fills/strokes arrays are immutable - replace the whole array. Colors are 0-1 RGB: `{type:'SOLID',color:{r:1,g:0,b:0}}`.
- Images: `const img = await figma.createImageAsync(url)` (public URL) → `{type:'IMAGE',imageHash:img.hash,scaleMode:'FILL'}`.
- Write big scripts to a temp `.js` file and use `-f` (avoids shell quoting of Cyrillic/quotes).
- Verify visually: `fig.py export <id> --out C:\...\scratchpad\x.png`, then Read the PNG.

## Animation (prototype)

Figma animates between frames. Pattern for Smart Animate: duplicate frame A → B, keep layer **names identical**,
change position/size/opacity/color in B, then:

```js
await a.setReactionsAsync([{ trigger: { type: 'ON_CLICK' },  // or AFTER_TIMEOUT {timeout:0.8}, ON_HOVER, MOUSE_ENTER
  actions: [{ type: 'NODE', destinationId: b.id, navigation: 'NAVIGATE',
    transition: { type: 'SMART_ANIMATE', easing: { type: 'EASE_IN_AND_OUT' }, duration: 0.4 },
    preserveScrollPosition: false }] }]);
```
Other transitions: `DISSOLVE`, `MOVE_IN`/`MOVE_OUT`/`PUSH`/`SLIDE_IN`/`SLIDE_OUT` (+ `direction`, `matchLayers`).
Set a flow start: `figma.currentPage.flowStartingPoints = [{nodeId: a.id, name: 'Flow'}]`.
Figma cannot do timeline/scroll/parallax animation - that belongs in code or After Effects.

## Limits

- Only works while the Figma desktop app has the file open with the plugin running.
- Plugin API cannot publish libraries or change billing/sharing - user does those.
- Never put the REST token in the vault or in chat; `save-token.ps1` stores it in `~/.figma_token`.

## Website → Figma (html2fig)

`_system/tools/figma/html2fig/`: scrape a live page in the browser pane with `ext.js`
(`__prep()` then `__ext(root)`, POST to `http://127.0.0.1:3055/stash?name=x`; https sites must be
served through a local copy with `<base href>` because Chrome blocks https→localhost POSTs),
then `build.py lib` + `build.py page <stash>` draws every header/section/footer as a frame.
Images: plugin sandbox blocks network → `build.py preload()` downloads, converts webp→JPEG,
and ships base64 in the script (`figma.createImage`). Interactions: see `hero.py` (variant
carousel, AFTER_TIMEOUT + CHANGE_TO), `faq.py` (accordion, variants must HUG height),
`cards.js` (ON_HOVER variants, horizontal overflow + SCROLL_TO needs `SCROLL_ANIMATE`).
Overlay: frame.overlayPositionType/overlayBackgroundInteraction + navigation 'OVERLAY', close = {type:'CLOSE'}.
Fixed header: make it the last child and `frame.numberOfFixedChildren = 1`.

## Design-system rebuild (BYD pattern, preferred over raw html2fig)

`html2fig/byd/`: `00_lib.js` (store.D helpers: variables-bound fills/strokes/padding, text styles,
icons with SVG-accurate stroke scaling, CROP image fills emulating object-fit/position, CSS easings as
CUSTOM_CUBIC_BEZIER), `01` styles+icons, `02` atoms, `03` cards, `04` section components, `05` page.
`run.py` preloads images once and runs steps in order (`run.py 03 05` = only those).
Gotchas: text needs `fontName` set before `characters`; use `setTextStyleIdAsync`; a transparent
border must be a plain SOLID paint with opacity 0 (opacity on a variable-bound paint is ignored);
text-decoration is synced across all nodes bound to one TEXT property → per-variant underline via a
style or a separate rule; `findOne` hits frames before texts, so never give a frame and a text the same name.
Variant swap keeps an instance override (e.g. an image fill) only if that property is identical in both
variants — never re-set fills per variant for hover zooms; resize the layer instead and copy the Default fill.
Nested instances (a card inside a section component) lose image/text overrides on prototype variant
swaps even when fills match — bake content into the component with a variant property (Model=…) instead.
Setting reactions on an instance REPLACES its component's reactions: merge the main component's reactions first.
Drag-to-scroll: auto-layout frame + clipsContent + overflowDirection='HORIZONTAL' (content wider than frame).
Sections created by script stay 496×496 — content spills out and sections look overlapped. After filling a
section: shift children to start at padding 120, then `section.resizeWithoutConstraints(w, h)` to the content
bounds, and stack sections with a clear gap (≥240). One batch of work = one section.

## 2 төхөөрөмж — PC ↔ Mac (2026-10-02)
- BD Figma-тай компьютер дээр plugin-ий **📡** таб → **Асаах** → код `IP:3057#TOKEN` гарна (Хуулах товч).
- Нөгөө компьютерийн Claude: `python fig.py pair <код>` (→ `~/.fig_remote.json`). Үүнээс хойш бүх `fig.py` команд тэр Figma руу явна.
- `fig.py status` → `remote: True, url`. Буцах: `fig.py unpair`; түр локал: `fig.py --local …`. env `FIG_URL`/`FIG_TOKEN` давуу.
- Сервер зөвхөн /status /exec /comments /claude-ийг token-тэй гадагш нээнэ; Унтраах = порт хаагдана; «Кодыг солих» = хуучин код хүчингүй.
- 403 → код солигдсон: шинэ код ав. Холбогдохгүй → нөгөө талд 📡 асаалттай, ижил Wi-Fi эсэх; Windows firewall 3057-г асууж магадгүй.
- Өөр газар (өөр Wi-Fi) байвал: хоёр төхөөрөмжид Tailscale (нэг бүртгэл) → 📡 код Tailscale IP `100.x.x.x:3057#…`-ээр эхэнд гарна. Router/port тохиргоо хэрэггүй.
- **Хэн зурах вэ?** (📡): BD 💻 энэ / 🖥 нөгөө / Хоёулаа-г сонгоно. Эрхгүй тал `run` → 423 «Зурах эрх …-д байна».
  423 авбал зурахаа зогсоогоод BD-д хэл; эрхийг өөрөө бүү солих (plugin товч зөвхөн BD-ийнх).

## Олон файл зэрэг (2026-09-25)
- Plugin-ыг хэд хэдэн файлд зэрэг асааж болно; сервер файл бүрээс нэрийг нь асууж (`__who`) бүртгэнэ.
- `python fig.py status` → `files: [...]`, `current`.
- `python fig.py --doc "My Designs" run -f x.js` (нэрийн хэсэг ч болно, env `FIG_FILE`). `--doc`-гүй бол хамгийн сүүлд холбогдсон файл.
- FigJam дэмжинэ (manifest `editorType: ["figma","figjam"]`); FigJam-д `createSticky`, `createShapeWithText`, `createConnector`, `createSection`.
