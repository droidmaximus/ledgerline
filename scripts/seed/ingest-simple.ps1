# Ingest Documents into PageIndex System - Simple Version
param(
    [string]$DocumentDir = ".\sample-data",
    [string]$IngestionUrl = "http://localhost:8080",
    [int]$TimeoutSeconds = 60
)

Write-Host ""
Write-Host "=== PageIndex Document Ingestion ===" -ForegroundColor Cyan
Write-Host "Ingestion Service: $IngestionUrl" -ForegroundColor Gray
Write-Host ""

# Verify service is healthy
Write-Host "Checking ingestion service health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$IngestionUrl/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "OK: Ingestion Service is HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "FAIL: Service returned status $($response.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "FAIL: Cannot reach service at $IngestionUrl" -ForegroundColor Red
    exit 1
}

# Check for PDFs
if (-not (Test-Path $DocumentDir)) {
    Write-Host "ERROR: Directory not found" -ForegroundColor Red
    exit 1
}

$pdfFiles = Get-ChildItem -Path $DocumentDir -Filter "*.pdf" -ErrorAction SilentlyContinue
if ($pdfFiles.Count -eq 0) {
    Write-Host "WARNING: No PDFs found in $DocumentDir" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found $($pdfFiles.Count) PDF(s):" -ForegroundColor Green
foreach ($pdf in $pdfFiles) {
    $sizeMB = [math]::Round($pdf.Length/1MB, 2)
    Write-Host "  - $($pdf.Name) ($sizeMB MB)" -ForegroundColor Gray
}
Write-Host ""

# Ingest each PDF
$successCount = 0
$failureCount = 0
$uploadedDocs = @()

foreach ($pdf in $pdfFiles) {
    $FileName = $pdf.Name
    $FilePath = $pdf.FullName
    
    Write-Host "Uploading: $FileName..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest `
            -Uri "$IngestionUrl/documents/upload" `
            -Method POST `
            -ContentType "multipart/form-data" `
            -InFile $FilePath `
            -TimeoutSec $TimeoutSeconds `
            -UseBasicParsing `
            -ErrorAction Stop
        
        if ($response.StatusCode -eq 200) {
            Write-Host "OK: Uploaded $FileName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "FAIL: Status $($response.StatusCode)" -ForegroundColor Red
            $failureCount++
        }
    } catch {
        Write-Host "ERROR: $_" -ForegroundColor Red
        $failureCount++
    }
    
    Start-Sleep -Milliseconds 500
}

# Summary
Write-Host ""
Write-Host "=== Ingestion Summary ===" -ForegroundColor Cyan
Write-Host "Uploaded: $successCount" -ForegroundColor Green
Write-Host "Failed: $failureCount" -ForegroundColor $(if ($failureCount -gt 0) { "Red" } else { "Green" })
Write-Host ""
Write-Host "Documents are now processing in the backend." -ForegroundColor Yellow
Write-Host "Parser service will generate tree structures." -ForegroundColor Gray
Write-Host ""
