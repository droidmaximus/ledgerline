#Requires -Version 5.1
<#
.SYNOPSIS
  Stop Ledgerline app processes listening on local dev ports (Windows).
.DESCRIPTION
  Kills listeners on 8080-8084 and optionally 3000 (frontend).
  Does not stop Docker; use 'make down' from the repo root for infra.
#>
param(
    [switch] $IncludeWeb
)

Write-Host "Stopping Ledgerline local processes (ports 8080-8084$(if ($IncludeWeb) { ', 3000' }))..." -ForegroundColor Yellow

$ports = @(8080, 8081, 8082, 8083, 8084)
if ($IncludeWeb) { $ports += 3000 }

foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $conns) {
        Write-Host "  Port $port : not in use" -ForegroundColor Gray
        continue
    }
    foreach ($c in $conns) {
        $proc = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Port $port : stopping $($proc.ProcessName) (PID $($proc.Id))" -ForegroundColor Yellow
            Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "Done. Run 'make down' in the repo root to stop Docker services." -ForegroundColor Green
