# Ingest Documents into PageIndex System
# This script uploads PDF files to the ingestion service and seeds the system with data

param(
    [string]$DocumentDir = ".\sample-data",
    [string]$IngestionUrl = "http://localhost:8080",
    [int]$TimeoutSeconds = 60
)

Write-Host "=== PageIndex Document Ingestion ===" -ForegroundColor Cyan
Write-Host "Ingestion Service: $IngestionUrl" -ForegroundColor Gray
Write-Host ""

# Verify ingestion service is healthy
Write-Host "⏳ Checking ingestion service health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$IngestionUrl/health" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Ingestion Service is HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "✗ Ingestion Service returned status: $($response.StatusCode)" -ForegroundColor Red
        Write-Host "Aborting ingestion." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Cannot reach ingestion service at $IngestionUrl" -ForegroundColor Red
    Write-Host "Please ensure the service is running: make run-ingestion" -ForegroundColor Yellow
    exit 1
}

# Check if PDF directory exists and has files
if (-not (Test-Path $DocumentDir)) {
    Write-Host "✗ Document directory not found: $DocumentDir" -ForegroundColor Red
    Write-Host "Run: python scripts/seed/create-test-pdf.py (from repo root) or add PDFs to $DocumentDir" -ForegroundColor Yellow
    exit 1
}

$pdfFiles = Get-ChildItem -Path $DocumentDir -Filter "*.pdf" -ErrorAction SilentlyContinue
if ($pdfFiles.Count -eq 0) {
    Write-Host "⚠ No PDF files found in: $DocumentDir" -ForegroundColor Yellow
    Write-Host "Run: python scripts/seed/create-test-pdf.py (from repo root) or add PDFs to $DocumentDir" -ForegroundColor Cyan
    exit 1
}

Write-Host "Found $($pdfFiles.Count) PDF file(s) to ingest:" -ForegroundColor Green
$pdfFiles | ForEach-Object { Write-Host "  • $($_.Name) ($([math]::Round($_.Length/1MB, 2)) MB)" -ForegroundColor Gray }
Write-Host ""

# Ingest each PDF
$successCount = 0
$failureCount = 0
$uploadedDocs = @()

foreach ($pdf in $pdfFiles) {
    $FileName = $pdf.Name
    $FilePath = $pdf.FullName
    $FileSize = [math]::Round($pdf.Length/1MB, 2)
    
    Write-Host "⏳ Uploading: $FileName ($FileSize MB)..." -ForegroundColor Yellow
    
    try {
        # Create multipart form data
        $fileStream = [System.IO.File]::OpenRead($FilePath)
        $form = @{
            file = $fileStream
        }
        
        $response = Invoke-WebRequest `
            -Uri "$IngestionUrl/documents/upload" `
            -Method POST `
            -Form $form `
            -TimeoutSec $TimeoutSeconds `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            $responseData = $response.Content | ConvertFrom-Json
            $docId = $responseData.doc_id
            
            Write-Host "✓ Uploaded: $FileName" -ForegroundColor Green
            Write-Host "  Document ID: $docId" -ForegroundColor Gray
            Write-Host "  Status: $($responseData.status)" -ForegroundColor Gray
            
            $uploadedDocs += @{
                FileName = $FileName
                DocId = $docId
                UploadTime = Get-Date
            }
            
            $successCount++
        } else {
            Write-Host "✗ Upload failed with status: $($response.StatusCode)" -ForegroundColor Red
            $failureCount++
        }
        
        $fileStream.Close()
    } catch {
        Write-Host "✗ Error uploading $FileName : $_" -ForegroundColor Red
        $failureCount++
    }
    
    # Small delay between uploads
    Start-Sleep -Milliseconds 500
}

# Summary
Write-Host ""
Write-Host "=== Ingestion Summary ===" -ForegroundColor Cyan
Write-Host "Total uploaded: $successCount" -ForegroundColor Green
Write-Host "Total failed: $failureCount" -ForegroundColor $(if ($failureCount -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($uploadedDocs.Count -gt 0) {
    Write-Host "Uploaded Documents:" -ForegroundColor Green
    $uploadedDocs | ForEach-Object {
        Write-Host "  • $($_.FileName)" -ForegroundColor Gray
        Write-Host "    ID: $($_.DocId)" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "⏳ Documents are now in the ingestion queue..." -ForegroundColor Yellow
    Write-Host "📝 Parser service will process them in the background" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Wait 30-60 seconds for parser to generate trees"
    Write-Host "2. Query: POST http://localhost:8083/query with doc_id + question"
    Write-Host "3. List docs: curl http://localhost:8083/documents"
    Write-Host ""
    
    # Provide document IDs for testing
    Write-Host "Test the ingested documents:" -ForegroundColor Cyan
    $uploadedDocs | ForEach-Object {
        Write-Host "  curl -X POST http://localhost:8083/query -H 'Content-Type: application/json' -d '{""doc_id"": ""$($_.DocId)"", ""question"": ""What is this document about?""}'" -ForegroundColor Gray
    }
} else {
    Write-Host "✗ No documents were successfully uploaded" -ForegroundColor Red
    Write-Host "Please check the ingestion service logs for details" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📊 Monitor progress:" -ForegroundColor Cyan
Write-Host "  • Ingestion logs: Check terminal running 'make run-ingestion'" -ForegroundColor Gray
Write-Host "  • Parser logs: Check terminal running 'make run-parser'" -ForegroundColor Gray
Write-Host "  • Cache health: curl http://localhost:8082/cache/stats" -ForegroundColor Gray
