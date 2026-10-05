# Third-party notices / Гуравдагч талын мэдэгдэл

The "fm" plugin (Founder Matrix OS) is proprietary to itge.e / Соёл (see LICENSE).
Some parts are derived from or adapted from the MIT-licensed projects below.
Their copyright notices and full license texts are kept in LICENSES/ as the
MIT License requires. Paths below are relative to plugins/fm/.

Энэ plugin-ий зарим хэсэг доорх MIT лицензтэй төслүүдээс гаралтай. Эх зохиогчийн
мэдэгдэл болон лицензийн бүрэн текст LICENSES/ хавтсанд хадгалагдана.

----------------------------------------------------------------------------

## 1. kepano/obsidian-skills

fm:canvas, fm:bases, fm:vault-cli and parts of fm:vault are derived from
"obsidian-skills" by Steph Ango (https://github.com/kepano/obsidian-skills),
Copyright (c) 2026 Steph Ango (@kepano), MIT License.
Renamed and modified. Not affiliated with or endorsed by Steph Ango or Obsidian.
Full license text: LICENSES/kepano-obsidian-skills.MIT.txt
Source snapshot: obsidian plugin v1.0.1 (claude.ai upload of kepano/obsidian-skills).

Derived files (paths relative to plugins/fm/):

  skills/canvas/SKILL.md
      from skills/json-canvas/SKILL.md
      changes: frontmatter name json-canvas -> canvas; Mongolian trigger sentence
      appended to description; attribution comment added as first body line.
  skills/canvas/references/EXAMPLES.md
      from skills/json-canvas/references/EXAMPLES.md (unmodified copy)

  skills/bases/SKILL.md
      from skills/obsidian-bases/SKILL.md
      changes: frontmatter name obsidian-bases -> bases; Mongolian trigger sentence
      appended to description; attribution comment added as first body line.
  skills/bases/references/FUNCTIONS_REFERENCE.md
      from skills/obsidian-bases/references/FUNCTIONS_REFERENCE.md (unmodified copy)

  skills/vault-cli/SKILL.md
      from skills/obsidian-cli/SKILL.md
      changes: frontmatter name obsidian-cli -> vault-cli; Mongolian trigger sentence
      appended to description; attribution comment added as first body line.

  skills/vault/references/obsidian-syntax.md
      from skills/obsidian-markdown/SKILL.md + references/CALLOUTS.md,
      references/EMBEDS.md, references/PROPERTIES.md
      changes: merged into one file; frontmatter removed; Mongolian intro note and
      attribution comment added; reference files appended as sections with headings
      demoted one level; links to references/*.md rewritten to in-file anchors.

Not derived (original fm work, links to the derived reference above):
  skills/vault/SKILL.md

Partly derived:
  skills/clip/SKILL.md
      the clean-markdown fetch step ("defuddle parse <url> --md", CLI from the
      upstream npm package "defuddle") follows kepano/obsidian-skills/defuddle;
      the defuddle skill itself is not copied. Marked with a derived-from comment.

----------------------------------------------------------------------------

## 2. obsidian-second-brain (Eugeniu Ghelbur)

Some fm skills adapt ideas and command flows from "obsidian-second-brain" by
Eugeniu Ghelbur (https://github.com/eugeniughelbur/obsidian-second-brain),
Copyright (c) 2026 Eugeniu Ghelbur, MIT License.
Renamed and modified. Not affiliated with or endorsed by Eugeniu Ghelbur or Obsidian.
Full license text: LICENSES/obsidian-second-brain.MIT.txt

fm replaces that plugin for Соёл members; none of its scripts, hooks or MCP
server are vendored. Skills marked with a "See THIRD_PARTY_NOTICES.md" comment:

- fm:save - the overall flow (scan the conversation for vault-worthy items, group them by kind, search before creating, propagate to the daily note, report what was saved) is adapted from the "obsidian-save" command of obsidian-second-brain by Eugeniu Ghelbur (https://github.com/eugeniughelbur/obsidian-second-brain), (c) 2026 Eugeniu Ghelbur, MIT License. Rewritten in Mongolian for a PARA + atomic-notes vault; no text copied.

- fm:daily - the create-from-template / inject-without-overwrite flow, user-focus-first ordering and the due-task pull are adapted from the "obsidian-daily" command of obsidian-second-brain by Eugeniu Ghelbur, (c) 2026 Eugeniu Ghelbur, MIT License. Rewritten in Mongolian; calendar step dropped; no text copied.

- fm:clip - the idea of turning a source into atomic notes with a confidence level and checking them against existing atoms follows the "atomic-notes" command shipped in the obsidian-second-brain folder (c) 2026 Eugeniu Ghelbur, MIT License; the clean-markdown fetch step is derived from kepano/obsidian-skills "defuddle" by Steph Ango, (c) 2026 Steph Ango, MIT License (marked with a derived-from comment in SKILL.md). Rewritten in Mongolian.

- fm:project - project create/update flow and the board-hygiene mode (stale/overdue
  triage, batch verdicts approved before applying) are adapted from the
  "obsidian-project" and "obsidian-board-hygiene" commands of obsidian-second-brain
  by Eugeniu Ghelbur, (c) 2026 Eugeniu Ghelbur, MIT License. Rewritten in
  Mongolian; no text copied.

----------------------------------------------------------------------------

## 3. Original fm work (not derived from third-party code)

- fm:inbox, fm:track, fm:update - not derived from third-party code; based on the vault owner's own commands (obsidian-inbox, obsidian-route, track, sync, jirge).
- fm:setup, fm:role, fm:spawn, fm:task, fm:finance - original fm work.
- fm:vault (SKILL.md itself), hooks/, scripts/, vault-template/ - original fm work.

"Obsidian" is a trademark of Dynalist Inc. fm is not affiliated with or endorsed
by Obsidian, Steph Ango or Eugeniu Ghelbur.
