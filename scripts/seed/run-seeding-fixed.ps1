# Complete Data Seeding Workflow - Fixed Version
param(
    [ValidateSet("fetch", "ingest", "verify", "full")]
    [string]$Mode = "full",
    [string]$DocumentDir = ".\sample-data"
)

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "   PageIndex Document Seeding" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# FETCH: Download sample documents
if ($Mode -in "fetch", "full") {
    Write-Host "STEP 1: FETCH DOCUMENTS" -ForegroundColor Yellow
    Write-Host ""
    
    $createPdf = ".\scripts\seed\create-test-pdf.py"
    if (Test-Path $createPdf) {
        Write-Host "Running: python $createPdf" -ForegroundColor Cyan
        python $createPdf
    } else {
        Write-Host "ERROR: Not found: $createPdf" -ForegroundColor Red
    }
    Write-Host ""
}

# INGEST: Upload documents to the system
if ($Mode -in "ingest", "full") {
    Write-Host "STEP 2: INGEST DOCUMENTS" -ForegroundColor Yellow
    Write-Host ""
    
    $ingestScriptPath = ".\scripts\seed\ingest-documents.ps1"
    if (Test-Path $ingestScriptPath) {
        Write-Host "Running: $ingestScriptPath" -ForegroundColor Cyan
        & $ingestScriptPath
    } else {
        Write-Host "ERROR: Script not found: $ingestScriptPath" -ForegroundColor Red
    }
    Write-Host ""
}

# VERIFY: Test the ingested documents
if ($Mode -in "verify", "full") {
    Write-Host "STEP 3: VERIFY SYSTEM" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "Checking service health..." -ForegroundColor Cyan
    Write-Host ""
    
    $services = @(
        @{ Port = 8080; Name = "Ingestion" },
        @{ Port = 8081; Name = "Parser" },
        @{ Port = 8082; Name = "Cache" },
        @{ Port = 8083; Name = "Gateway" }
    )
    
    $allHealthy = $true
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 3 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "[OK] $($service.Name) (Port $($service.Port))" -ForegroundColor Green
            } else {
                Write-Host "[FAIL] $($service.Name) (Port $($service.Port)): Status $($response.StatusCode)" -ForegroundColor Red
                $allHealthy = $false
            }
        } catch {
            Write-Host "[DOWN] $($service.Name) (Port $($service.Port))" -ForegroundColor Red
            $allHealthy = $false
        }
    }
    
    Write-Host ""
    
    if ($allHealthy) {
        Write-Host "SUCCESS: All services healthy!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Some services not responding" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# Summary
Write-Host "========================================================================" -ForegroundColor Green
Write-Host "   SEEDING COMPLETE" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your system is ready for financial document queries!" -ForegroundColor Yellow
Write-Host ""
