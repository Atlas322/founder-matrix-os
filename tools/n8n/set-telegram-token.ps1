# Clipboard дахь Telegram bot token-ийг tools/n8n/.env-д FMOS_TELEGRAM_TOKEN болгон бичнэ (.env gitignored).
$envFile = Join-Path $PSScriptRoot ".env"
$tok = (Get-Clipboard | Out-String).Trim()
if ($tok -notmatch '^\d+:[\w-]{30,}$') { Write-Host "Clipboard-д Telegram token алга (жишээ 123456:ABC...). BotFather-аас дахин хуул." -ForegroundColor Red; exit 1 }
$lines = @(Get-Content $envFile | Where-Object { $_ -notmatch '^FMOS_TELEGRAM_TOKEN=' })
$lines += "FMOS_TELEGRAM_TOKEN=$tok"
Set-Content -Path $envFile -Value $lines -Encoding ascii
Write-Host "OK: Telegram token .env-д хадгалагдлаа" -ForegroundColor Green
