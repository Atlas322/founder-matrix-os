# tools/n8n — FMOS automation "ears"

n8n listens to outside channels and posts to Discord; Claude agents wake via `relay.py watch`.

## Run (PC or Mac)
```
cp .env.example .env      # fill POSTGRES_PASSWORD + N8N_ENCRYPTION_KEY
docker compose up -d
open http://localhost:5678
```

## Workflows
Exported workflow JSON lives in `workflows/` (no credentials inside — n8n exports strip them).
Import: `docker compose exec n8n n8n import:workflow --input=/workflows/<file>.json`
Export: `docker compose exec n8n n8n export:workflow --all --output=/workflows/ --separate`

## Order
1. Notion comment → Discord (replaces `tools/relay/notion_watch.py`; run both 2 days, then disable the script)
2. Gmail → Discord · 3. Calendar 07:30 brief · 4. Telegram → Inbox · 5. IG/Meta

## Secrets (itge.e enters in n8n UI, never in repo)
Discord bot token · Notion integration token · Google OAuth · Telegram bot token · Meta app.
