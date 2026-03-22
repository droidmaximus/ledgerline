# Complete Data Seeding Workflow for PageIndex
# This script orchestrates the entire process: fetch documents, ingest, and verify

param(
    [ValidateSet("fetch", "ingest", "verify", "full")]
    [string]$Mode = "full",
    [string]$DocumentDir = ".\sample-data"
)

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PageIndex Document Seeding Tool                               ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Helper function to run scripts
function Invoke-Script {
    param([string]$ScriptPath, [string]$Description)
    
    Write-Host ">> $Description" -ForegroundColor Cyan
    Write-Host "   Running: $ScriptPath" -ForegroundColor Gray
    Write-Host ""
    
    & $ScriptPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "! Script exited with code: $LASTEXITCODE" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# FETCH: Download sample documents
if ($Mode -in "fetch", "full") {
    Write-Host "📥 STEP 1: FETCH DOCUMENTS" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    
    $createPdf = ".\scripts\seed\create-test-pdf.py"
    if (Test-Path $createPdf) {
        Write-Host ">> Generating sample PDFs (create-test-pdf.py)" -ForegroundColor Cyan
        python $createPdf
        if ($LASTEXITCODE -ne 0) {
            Write-Host "! create-test-pdf.py exited with code: $LASTEXITCODE" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✗ Not found: $createPdf — add PDFs manually to $DocumentDir" -ForegroundColor Red
    }
    
    # Check results
    if (Test-Path $DocumentDir) {
        $pdfCount = @(Get-ChildItem -Path $DocumentDir -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
        if ($pdfCount -gt 0) {
            Write-Host "✓ Document fetch complete: Found $pdfCount PDF(s)" -ForegroundColor Green
        } else {
            Write-Host "⚠ No PDF files found yet in directory" -ForegroundColor Yellow
            Write-Host "  Run python scripts/seed/create-test-pdf.py or place PDFs in: $DocumentDir" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

# INGEST: Upload documents to the system
if ($Mode -in "ingest", "full") {
    Write-Host "📤 STEP 2: INGEST DOCUMENTS" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    
    $ingestScriptPath = ".\scripts\seed\ingest-documents.ps1"
    if (Test-Path $ingestScriptPath) {
        Invoke-Script -ScriptPath $ingestScriptPath -Description "Ingesting documents via API"
    } else {
        Write-Host "✗ Script not found: $ingestScriptPath" -ForegroundColor Red
    }
    Write-Host ""
}

# VERIFY: Test the ingested documents
if ($Mode -in "verify", "full") {
    Write-Host "✅ STEP 3: VERIFY SYSTEM" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "Verifying services..." -ForegroundColor Cyan
    Write-Host ""
    
    $services = @(
        @{ Port = 8080; Name = "Ingestion Service" },
        @{ Port = 8081; Name = "Parser Service" },
        @{ Port = 8082; Name = "Cache Service" },
        @{ Port = 8083; Name = "API Gateway" }
    )
    
    $allHealthy = $true
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -TimeoutSec 3 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "✓ $($service.Name) (Port $($service.Port)): HEALTHY" -ForegroundColor Green
            } else {
                Write-Host "✗ $($service.Name) (Port $($service.Port)): Status $($response.StatusCode)" -ForegroundColor Red
                $allHealthy = $false
            }
        } catch {
            Write-Host "✗ $($service.Name) (Port $($service.Port)): DOWN" -ForegroundColor Red
            $allHealthy = $false
        }
    }
    
    Write-Host ""
    
    if ($allHealthy) {
        Write-Host "✓ All services healthy!" -ForegroundColor Green
    } else {
        Write-Host "⚠ Some services are not healthy" -ForegroundColor Yellow
        Write-Host "Please ensure all services are running:" -ForegroundColor Gray
        Write-Host "  make run-ingestion &" -ForegroundColor Gray
        Write-Host "  make run-parser &" -ForegroundColor Gray
        Write-Host "  make run-cache &" -ForegroundColor Gray
        Write-Host "  make run-gateway &" -ForegroundColor Gray
    }
    
    Write-Host ""
}

# Final instructions
Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   Seeding Complete!                                            ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📚 Your system is now ready with financial documents!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Query documents via API:" -ForegroundColor Gray
Write-Host "     curl -X POST http://localhost:8083/query -H 'Content-Type: application/json' -d '{\"doc_id\": \"YOUR_DOC_ID\", \"question\": \"What is the revenue?\"}'" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Stream results via WebSocket:" -ForegroundColor Gray
Write-Host "     wscat -c ws://localhost:8083/ws" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Monitor cache statistics:" -ForegroundColor Gray
Write-Host "     curl http://localhost:8082/cache/stats" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. View Kafka UI:" -ForegroundColor Gray
Write-Host "     http://localhost:8090" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 PageIndex Docs: https://docs.pageindex.ai/" -ForegroundColor Cyan
