#!/bin/bash
# Finder-d songoson file(uud)-iig Second Brain 00-Inbox ruu zoono (Downloads-oos gol tolov).
# Songolt baihgui bol Downloads-iin hamgiin shine zuiliig zoono.
# Holboh: Shortcuts.app -> "Run Shell Script" -> ene file -> keyboard shortcut onoo.
# NOTE: set -e ashiglahgui (nohtsolt file uildluud).

VAULT="$HOME/Documents/CodeBase/Second Brain"
INBOX="$VAULT/00-Inbox"
DL="$HOME/Downloads"
mkdir -p "$INBOX"

# Finder-iin songoltiig POSIX zamaar av (mor bur = neg file)
SEL="$(osascript <<'AS' 2>/dev/null
set out to ""
tell application "Finder"
  set sel to selection
  repeat with i in sel
    set out to out & (POSIX path of (i as alias)) & linefeed
  end repeat
end tell
return out
AS
)"

moved=0
last=""
move_one() {
  local f="$1"
  f="${f%/}"
  if [ ! -e "$f" ]; then return 0; fi
  local base dest
  base="$(basename "$f")"
  dest="$INBOX/$base"
  if [ -e "$dest" ]; then dest="$INBOX/$(date +%H%M%S)-$base"; fi
  if mv "$f" "$dest"; then moved=$((moved + 1)); last="$base"; fi
}

if [ -n "$(printf '%s' "$SEL" | tr -d '[:space:]')" ]; then
  while IFS= read -r f; do
    [ -n "$f" ] && move_one "$f"
  done <<EOF
$SEL
EOF
else
  newest="$(ls -t "$DL" 2>/dev/null | head -1)"
  [ -n "$newest" ] && move_one "$DL/$newest"
fi

if [ "$moved" -gt 0 ]; then
  msg="$moved файл 00-Inbox руу зөөв"
  [ "$moved" -eq 1 ] && msg="$last -> 00-Inbox"
  osascript -e "display notification \"$msg\" with title \"Move to Inbox\"" 2>/dev/null || true
else
  osascript -e 'display notification "Файл сонгоогүй / олдсонгүй" with title "Move to Inbox"' 2>/dev/null || true
fi
