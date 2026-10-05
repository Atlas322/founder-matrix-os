---
name: figma-bridge
description: Draw, edit, animate (Smart Animate prototypes) and export in Figma through a free local bridge (Figma dev plugin + CLI) - no Figma MCP plan limits. Use whenever the user wants something created or changed inside Figma, Figma prototypes/animations, or bulk export of Figma frames/images (read-only bulk export can also use the REST CLI figma.py).
---

# Figma bridge (local, unlimited)

Tools live in the vault at `_system/tools/figma/` (vault root-оос харьцангуй — PC, Mac аль алинд ижил).

| Need | Tool |
|---|---|
| Create / edit / animate in Figma | `fig.py run` → local plugin (full Figma Plugin API) |
| Export one node as PNG/SVG/PDF | `fig.py export <nodeId>` |
| Bulk read / export whole files, original image fills | `figma.py` (REST, token in `~/.figma_token`) |

Prefer these over the claude.ai Figma MCP connector - that one is capped on the user's Starter plan.

## Start-up checklist (every session)

1. `python fig.py status` → `{'plugin': True}` means ready.
2. If the server is down: start `node bridge/server.mjs` with Bash `run_in_background`.
3. If `plugin: False`: ask the user to open the Figma file and run **Plugins → Development → Claude Bridge**
   (first time only: **Plugins → Development → Import plugin from manifest…** →
   `_system\tools\figma\bridge\plugin\manifest.json`). Needs the Figma **desktop** app.

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

## Олон файл зэрэг (2026-09-25)
- Plugin-ыг хэд хэдэн файлд зэрэг асааж болно; сервер файл бүрээс нэрийг нь асууж (`__who`) бүртгэнэ.
- `python fig.py status` → `files: [...]`, `current`.
- `python fig.py --doc "My Designs" run -f x.js` (нэрийн хэсэг ч болно, env `FIG_FILE`). `--doc`-гүй бол хамгийн сүүлд холбогдсон файл.
- FigJam дэмжинэ (manifest `editorType: ["figma","figjam"]`); FigJam-д `createSticky`, `createShapeWithText`, `createConnector`, `createSection`.

## 💬 Comments (plugin панел, 2026-09-28)
BD plugin-ий 💬 табаас node сонгоод бичнэ → `bridge/stash/comments.json`.
- `fig.py comments [--wait 600]` — хариулаагүй thread-ууд (wait: шинэ коммент ирэх хүртэл long-poll)
- `fig.py reply <id> "текст"` — plugin-д шууд гарч, Figma notify харуулна
- `fig.py resolve <id>`
Figma-гийн жинхэнэ comment биш (Plugin API comment уншиж чаддаггүй; REST нь token шаарддаг).
- Камер Claude-ийн зурж буй газрыг үргэлж дагана (▶ toggle хасагдсан).
- Хариултад `@[S12 · Calendar](48:1529)` бичвэл дарахад тэр screen рүү очдог холбоос болно. (▶ харах/✕ товчийг BD хэрэггүй гэсэн — mention л хангалттай.)
- `fig.py delete <id>` — мессеж устгах (root id бол бүх thread).

### Дүрэм (2026-09-28, 06 Creative Director — бодит алдаанаас)
1. **Хариултад зурсан зүйлээ заавал `@[нэр](69:4297)` гэж дурд** — панелд дарж болох холбоос болно. ui.html одоо задгай `123:456` ID-г ч автоматаар холбоос болгодог (нөөц хамгаалалт), гэхдээ нэртэй mention нь илүү ойлгомжтой.
2. **`--doc` заавал заа:** `fig.py --doc "Second Brain" run -f x.js`. BD өөр файл (ж: «Про Байцаа») нээмэгц plugin тэр файлыг `current` болгодог тул заалгүй ажиллуулсан скрипт буруу файл руу очно.
3. **Коммент сешн рүү өөрөө мэдэгддэггүй.** `fig.py comments --wait 3500`-г арын процессоор байнга асаа. Хариулаагүй thread байвал long-poll шууд буцдаг тул бүгдийг хариулсны дараа дахин асаа.
4. `code.js`/`ui.html` засвар бүрийн дараа **plugin-ыг хааж нээнэ** — код нь нээх үед л ачаалагддаг.
5. **Урт хариултыг файлаар дамжуул:** `fig.py reply <id> "$(cat /tmp/r.txt)"`. Шууд бичвэл zsh нь `backtick` ба `$`-ыг команд болгон гүйцэтгээд текстийг эвддэг (2026-09-28-д тохиолдсон).
6. **Сешн эхлэхэд `fig.py comments` шалга.** Өөр сешн (PC/Mac)-ээс үлдсэн хариулаагүй thread байвал `--wait` шууд буцаж, сонсогч ажиллахгүй → BD-ээс асуугаад `fig.py resolve <root id>`, дараа нь сонсогчоо асаа (2026-09-28, Mac дээр тохиолдсон).
7. Панел markdown-lite ойлгоно: `код`, **тод**, «- » товчлол, ①②③.
7. **Зурсны дараа заавал давхцлыг шалга:** `fig.py --doc "<файл>" run -f _system/tools/figma/check_layout.js` → TEXT node-уудын огтлолцол ба хүрээнээс халалтыг жагсаана. 0 гартал зас. Гараар y тоолох нь давхцал үүсгэдэг (BD 2026-09-28: «текстүүд давхцаад байна, жигдлэгээ барих дээр муу»).
8. Байрлуулахдаа хэмжинэ: богино шошгод `textAutoResize='WIDTH_AND_HEIGHT'`, дараагийн элементэд `y = өмнөхийн y + өндөр + зай` (`autoW`, `below` туслах).

## Mac-тай синк (2026-09-28)
Plugin (code.js/ui.html) засах бүрт нөгөө төхөөрөмж рүү relay-ээр (`relay.py send`, хуучин `_system/relay/` архивласан) «plugin шинэчлэгдсэн» (server.mjs бол «server шинэчлэгдсэн», manifest бол «manifest») гэж нэг мөр бич — Mac-ийн 03 Sys Admin BD-д reopen/restart хийлгэнэ (#20).

## Board-ын дүрэм: section бүр auto layout (BD, 2026-09-28)
Section-ийг Figma API auto layout болгож чаддаггүй → section > `Stage · auto` (VERTICAL, hug) > толгой, тайлбар, `мөрүүд (wrap)` (HORIZONTAL WRAP) > `карт` (зураг + caption). Шинэ stage-ийг ийм бүтэцтэй үүсгэ; хуучныг `html2fig/board_autolayout.js`-ээр хөрвүүл. Stage хоорондын сумыг script дахин зурна.

UPDATE 2026-09-28: stage-ууд SECTION биш **auto layout FRAME** (нэг frame-ийн өргөнийг чирэхэд дотор нь цэгцрэнэ) — `html2fig/board_sections_to_frames.js`.

9. **Асуултаа ЭНД тавь, чатад биш.** BD Figma дотор ажиллаж байхад асуултыг коммент thread-д `reply`-ээр тавина, дараа нь `fig.py -d "Second Brain" comments --wait 540` гэж хариуг нь блоклон хүлээнэ. «Claude-ийн чатад хариулна уу» гэж бичихгүй. (BD 2026-09-28)

10. **`fig.py run` — файл бол ЗААВАЛ `-f`.** `run <текст>` нь кодыг өөрийг нь хүлээж авдаг; файлын замыг шууд өгвөл тэр зам нь JS болж задлагдаад «Invalid regular expression flags» гэсэн будлиантай алдаа өгнө. Зөв: `fig.py -d "Second Brain" run -f script.js -t 120`. (2026-09-28-нд энэ алдаанд нэлээд хугацаа алдсан)

## Second Brain файлын хуудасны бүтэц (2026-09-29, BD)
Cover · ━━ INAI · SECOND BRAIN (🎨 Foundations · 🧩 Components · base · 🧩 Components · Inai · 📱 Screens · 📅 Цаглабар) · ━━ SOCIAL TOOL · POSTER MAKER (🖼 Moodboards · 🔍 Research · задаргаа [genome, reference] · 🪄 Poster Maker [формат сан, maker v0, AI scaffold] · 🗂 Post library [бүх бүтээл, carousel-ууд]). Шинэ ажлыг тохирох хуудсанд нэм — хуудас бүү нэм.

**2026-09-29 цэвэрлэгээ:** файлд зөвхөн Inai (Second Brain + Social tool) үлдэнэ. Устгасан: System · workflow, Reference, Designo LMS эх, Just.Notion Brand Kit — Figma version history «before cleanup · 2026-09-29»-д байна.
- **Contrast check:** `html2fig/contrast_check.js` (`__ROOT__`-г section/frame id-аар солиод run) — TEXT + сумыг доорх давхаргатай WCAG-аар харьцуулна: том текст (≥48px, bold ≥40) 3:1, бусад 4.5:1, сум 3:1; зураг дээрхийг «гараар» гэж тэмдэглэнэ. Poster Maker-ийн бүтээл бүрт нийтлэхээс өмнө ажиллуул.
