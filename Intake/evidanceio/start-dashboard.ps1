# Refreshes the dashboard data from the R2 Lakehouse (Iceberg) and starts the
# Evidence dev server (opens browser at http://localhost:3000).
# Byline: Claude Code - Opus 4.8 - 2026-06-23
$ErrorActionPreference = "Stop"
$cf = Get-Content "$env:USERPROFILE\.secrets\cloudflare.env" -Raw
$env:R2_CATALOG_TOKEN = [regex]::Match($cf, 'R2_CATALOG_TOKEN="([^"]+)"').Groups[1].Value
if (-not $env:R2_CATALOG_TOKEN) { Write-Host "R2_CATALOG_TOKEN missing in cloudflare.env" -ForegroundColor Red; pause; exit 1 }
$duck = (Get-Command duckdb -ErrorAction SilentlyContinue).Source
if (-not $duck) { $duck = "C:\Users\matts\AppData\Local\Microsoft\WinGet\Packages\DuckDB.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\duckdb.exe" }
$acct = "1a7406c497493a52128bb282f499e7b8"
$viz = "D:\casebible\viz"
$db = "$viz\sources\casebible\casebible.duckdb"

Write-Host "[1/3] Refreshing enrichment from the R2 Lakehouse..." -ForegroundColor Cyan
Remove-Item $db -ErrorAction SilentlyContinue
& $duck $db -c "INSTALL iceberg;LOAD iceberg;INSTALL httpfs;LOAD httpfs;CREATE SECRET cf (TYPE ICEBERG, TOKEN '$($env:R2_CATALOG_TOKEN)');ATTACH '${acct}_casebible-lakehouse' AS lake (TYPE ICEBERG, ENDPOINT 'https://catalog.cloudflarestorage.com/$acct/casebible-lakehouse');CREATE OR REPLACE TABLE enrichment AS SELECT * FROM lake.casebible.enrichment;"

Set-Location $viz
Write-Host "[2/3] Building dashboard data..." -ForegroundColor Cyan
npm run sources
Write-Host "[3/3] Starting dashboard (browser opens at http://localhost:3000)..." -ForegroundColor Cyan
npm run dev -- --open
