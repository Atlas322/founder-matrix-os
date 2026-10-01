# Discord bot token-оо хуулчихаад (Ctrl+C) үүнийг ажиллуул. ~/.fmos_discord_token руу хадгална (repo/vault-аас гадна).
$t = (Get-Clipboard | Out-String).Trim()
if ($t.Length -lt 50 -or $t -notmatch '^[\w\-]+\.[\w\-]+\.[\w\-]+$') { Write-Host "Clipboard-д Discord token алга." -ForegroundColor Yellow; exit 1 }
Set-Content -Path "$HOME\.fmos_discord_token" -Value $t -NoNewline -Encoding ascii
Set-Clipboard -Value " "
Write-Host "Хадгаллаа: $HOME\.fmos_discord_token (clipboard цэвэрлэв)" -ForegroundColor Green
