# Figma bridge (`tools/figma`, advanced)

Figma bridge нь Claude-д Figma дотор зурах, засах, prototype анимэйшн хийх, frame-үүдийг export хийх боломж өгнө. Figma MCP-ийн хязгааргүй, бүрэн локал ажиллана: таны компьютер дээрх жижиг сервер ↔ Figma desktop-ийн dev plugin.

> **Заавал биш, туршлагатай хэрэглэгчдэд.** fm plugin Figma-гүйгээр бүрэн ажиллана.

## Шаардлага

- **Figma desktop** апп (browser хувилбар dev plugin ачаалахгүй).
- **Node.js 20+** (`node --version`). Сервер ямар ч npm сан шаардахгүй.
- Python 3.9+ (`python3`, Windows-д `python` эсвэл `py -3` байж болно).
- Repo-гийн clone: `git clone https://github.com/rollingbd/founder-matrix-os.git`.

## Нэг удаагийн тохиргоо

1. Figma desktop-д дурын файл нээ → **Plugins → Development → Import plugin from manifest…** → `<REPO>/tools/figma/bridge/plugin/manifest.json`.
2. (Заавал биш) REST-ээр бөөнөөр export хийх бол Figma-ийн **Personal Access Token**-ийг (Settings → Security) зөвхөн home хавтсандаа хадгал:
   - Mac: `printf '%s' 'ЭНД_TOKEN' > ~/.figma_token && chmod 600 ~/.figma_token`
   - Windows: `Set-Content -NoNewline -Encoding ascii "$HOME\.figma_token" 'ЭНД_TOKEN'`

   Эсвэл `FIGMA_TOKEN` орчны хувьсагч. Token-ийг vault, repo, чатад **хэзээ ч** бичихгүй.

## Ажиллуулах (сешн бүр)

1. Серверийг асаа (порт 3055, зөвхөн localhost):
   ```
   node tools/figma/bridge/server.mjs
   ```
   Claude Code-оос ажиллуулж байгаа бол background-оор асаахыг хүс.
2. Figma-д ажиллах файлаа нээгээд **Plugins → Development → Claude Bridge** ажиллуул.
3. Шалга:
   ```
   python3 tools/figma/fig.py status
   ```
   `'plugin': True` гарвал бэлэн.

## Хэрэглээ

| Команд | Юу хийнэ |
|---|---|
| `fig.py run "<js>"` / `fig.py run -f script.js` | Figma Plugin API-тай JS код ажиллуулах |
| `fig.py tree [nodeId]` | Бүтцийг харах |
| `fig.py find "нэр"` | Node хайх |
| `fig.py export <nodeId> --format PNG --out x.png` | Export |
| `fig.py --doc "Файлын нэр" …` | Олон файл нээлттэй үед аль нэгийг сонгох |
| `figma.py …` | REST (token хэрэгтэй): бүх файлыг бөөнөөр унших/export |

Claude-д зориулсан дэлгэрэнгүй дүрэм: `tools/figma/SKILL.md`.

## Анхаар

- `tools/figma/html2fig/` доторх script-үүд нь itge.e-ийн төслүүдийн жишээ; өөрийн төсөлд шууд ашиглахгүй.
- Харилцагчийн Figma файлын key, хуваалцсан имэйл зэргийг repo-д commit хийхгүй.
- Порт 3055 өөр программд эзлэгдсэн бол тэр программыг хаа (`fig.py` 3055-ыг ашиглана).
