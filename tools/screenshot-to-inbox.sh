#!/bin/bash
# Screenshot -> Second Brain 00-Inbox. AL CH app-aas ajillana (Messages g.m native app-uud) -
# browser extension-ees yalgaatai ni macOS-iin screencapture tab bish buh delgetsiig zurna.
# Zurag avsny daraa "Claude-d yuu hiilgeh ve?" gej asууna -> notod bichigdene.
#
# Holboh: Shortcuts.app -> "Run Shell Script" -> ene file-iig duudaad keyboard shortcut onoo (jishee Ctrl+Cmd+Opt+V).
# Ⓘ macOS Sonoma+ deer Screen Recording zovshoorol shaardana (System Settings > Privacy > Screen Recording).

set -e
VAULT="$HOME/Documents/CodeBase/Second Brain"
INBOX="$VAULT/00-Inbox"
ATT="$VAULT/_system/attachments"
mkdir -p "$ATT"
TS="$(date +%Y-%m-%d-%H%M%S)"
PNG="screenshot - $TS.png"

# Interactive: hereglegch muj songono (space daraad tsonh songo bolno). Esc darwal file uusehgui.
/usr/sbin/screencapture -i "$ATT/$PNG"
[ -f "$ATT/$PNG" ] || exit 0

# Claude-d yuu hiilgeh ve? (Cancel darwal hooson)
TASK="$(osascript -e 'try' -e 'text returned of (display dialog "Claude-д юу хийлгэх вэ? (хоосон орхиж болно)" default answer "" with title "Screenshot -> Inbox" buttons {"Cancel","Save"} default button "Save")' -e 'on error' -e 'return ""' -e 'end try' 2>/dev/null || echo "")"

NOTE="$INBOX/capture - $TS.md"
DAY="$(date +%Y-%m-%d)"
HM="$(date +%H:%M)"
{
cat <<EOF
---
date: $DAY
type: reference
status: draft
tags:
  - reference
  - inbox
  - screenshot
reftype: screenshot
source: screenshot
needs-claude: true
ai-first: true
---

## For future agent

Screenshot capture $DAY $HM - screenshot-to-inbox hotkey-eer avav (al ch app-aas). Doorh zurgiig unshaad "Claude-d daalgavar"-ыг guitsetge, daraa ni zov haltas ruu bairluul.

![[$PNG]]

## 🤖 Claude-d daalgavar

EOF
printf '%s\n' "$TASK"
cat <<'EOF'

## ✍️ Minii temdeglel

EOF
} > "$NOTE"

osascript -e "display notification \"$PNG\" with title \"Saved to Inbox\"" 2>/dev/null || true
