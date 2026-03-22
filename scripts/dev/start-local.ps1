#Requires -Version 5.1
<#
.SYNOPSIS
  Start Ledgerline microservices from the repo (Windows).
.DESCRIPTION
  Spawns separate PowerShell windows for ingestion, parser, cache, evaluation-service, and API gateway.
  Expects Docker infra (make up) and a configured repo-root .env (Postgres on 5433 for evaluations).
.PARAMETER WithWeb
  Also start the Next.js app in web/ on port 3000.
.PARAMETER SkipHealthWait
  Do not poll /health on 8080-8084 after startup.
#>
param(
    [switch] $WithWeb,
    [switch] $SkipHealthWait
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName

function Start-ServiceWindow {
    param(
        [string] $Title,
        [string] $WorkingDirectory,
        [string] $CommandLine
    )
    $inner = @"
`$host.UI.RawUI.WindowTitle = '$Title'
Set-Location -LiteralPath '$WorkingDirectory'
$CommandLine
"@
    Start-Process powershell -ArgumentList @("-NoExit", "-NoProfile", "-Command", $inner) | Out-Null
}

Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $RepoRoot ".env"))) {
    Write-Warning "No .env at repo root. Copy .env.example to .env and set API keys / buckets."
}

$ing = Join-Path $RepoRoot "services\ingestion-service"
$par = Join-Path $RepoRoot "services\parser-service"
$cac = Join-Path $RepoRoot "services\cache-service"
$eval = Join-Path $RepoRoot "services\evaluation-service"
$gw = Join-Path $RepoRoot "services\api-gateway"

Write-Host "[1/5] Ingestion (8080)..." -ForegroundColor Green
$ingCmd = @"
if (Test-Path -LiteralPath '.\ingestion-service.exe') { & '.\ingestion-service.exe' }
else { go run ./cmd/main.go }
"@
Start-ServiceWindow -Title "Ledgerline Ingestion 8080" -WorkingDirectory $ing -CommandLine $ingCmd
Start-Sleep -Seconds 2

Write-Host "[2/5] Parser (8081)..." -ForegroundColor Cyan
Start-ServiceWindow -Title "Ledgerline Parser 8081" -WorkingDirectory $par -CommandLine "python -m app.main"
Start-Sleep -Seconds 2

Write-Host "[3/5] Cache (8082)..." -ForegroundColor Yellow
Start-ServiceWindow -Title "Ledgerline Cache 8082" -WorkingDirectory $cac -CommandLine "python -m app.main"
Start-Sleep -Seconds 2

Write-Host "[4/5] Evaluation (8084)..." -ForegroundColor DarkCyan
Start-ServiceWindow -Title "Ledgerline Evaluation 8084" -WorkingDirectory $eval -CommandLine "python -m app.main"
Start-Sleep -Seconds 2

Write-Host "[5/5] API Gateway (8083)..." -ForegroundColor Magenta
$gwCmd = @"
if (Test-Path -LiteralPath '.\api-gateway.exe') { & '.\api-gateway.exe' }
else { go run ./cmd/main.go }
"@
Start-ServiceWindow -Title "Ledgerline Gateway 8083" -WorkingDirectory $gw -CommandLine $gwCmd
Start-Sleep -Seconds 2

if ($WithWeb) {
    $web = Join-Path $RepoRoot "web"
    Write-Host "[6/6] Web (3000)..." -ForegroundColor Blue
    Start-ServiceWindow -Title "Ledgerline Web 3000" -WorkingDirectory $web -CommandLine "npm run dev"
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "Service windows launched. Ensure 'make up' (Docker) is running first." -ForegroundColor Green
Write-Host ""

if (-not $SkipHealthWait) {
    Write-Host "Waiting 20s before health checks..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
    Write-Host "Health check:" -ForegroundColor Cyan
    foreach ($p in @(8080, 8081, 8082, 8084, 8083)) {
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:$p/health" -UseBasicParsing -TimeoutSec 5
            Write-Host "  OK  :$p" -ForegroundColor Green
        }
        catch {
            Write-Host "  FAIL :$p" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "Kafka UI: http://localhost:8090 | MinIO: http://localhost:9000" -ForegroundColor Gray
}
