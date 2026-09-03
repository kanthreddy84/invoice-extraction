# Test Async Invoice Processing

$API_URL = "http://127.0.0.1:8000"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=" * 70
Write-Host "TESTING ASYNC INVOICE PROCESSING"
Write-Host "=" * 70
Write-Host ""

# Step 1: Upload Document
Write-Host "STEP 1: Uploading invoice document..."
Write-Host "-" * 70

try {
    $pdfPath = Join-Path $scriptDir "data\raw\invoice_001.pdf"
    Write-Host "Using file: $pdfPath"

    $fileBytes = [System.IO.File]::ReadAllBytes($pdfPath)

    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"

    $body = ([System.Text.Encoding]::UTF8.GetBytes("--$boundary$LF"))
    $body += [System.Text.Encoding]::UTF8.GetBytes("Content-Disposition: form-data; name=`"file`"; filename=`"$(Split-Path -Leaf $pdfPath)`"$LF")
    $body += [System.Text.Encoding]::UTF8.GetBytes("Content-Type: application/pdf$LF$LF")
    $body += $fileBytes
    $body += [System.Text.Encoding]::UTF8.GetBytes("$LF--$boundary--$LF")

    $response = Invoke-WebRequest `
      -Uri "$API_URL/api/documents/upload" `
      -Method Post `
      -Body $body `
      -ContentType "multipart/form-data; boundary=$boundary"

    $uploadResult = $response.Content | ConvertFrom-Json
    Write-Host "Status: OK" -ForegroundColor Green
    Write-Host "Document ID: $($uploadResult.document_id)"
    Write-Host "Filename: $($uploadResult.filename)"
    Write-Host ""

    $documentId = $uploadResult.document_id
} catch {
    Write-Host "ERROR: Failed to upload document" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 2: Queue for Async Processing
Write-Host "STEP 2: Queuing document for async processing..."
Write-Host "-" * 70

try {
    $response = Invoke-WebRequest `
      -Uri "$API_URL/api/documents/$documentId/process-async" `
      -Method Post

    $taskInfo = $response.Content | ConvertFrom-Json
    Write-Host "Status: OK" -ForegroundColor Green
    Write-Host "Task ID: $($taskInfo.task_id)"
    Write-Host "Status: $($taskInfo.status)"
    Write-Host ""

    $taskId = $taskInfo.task_id
} catch {
    Write-Host "ERROR: Failed to queue document" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# Step 3: Check Queue Status
Write-Host "STEP 3: Checking queue status..."
Write-Host "-" * 70

try {
    $response = Invoke-WebRequest "$API_URL/api/tasks/queue-status"
    $queueStatus = $response.Content | ConvertFrom-Json
    Write-Host "Queue: $($queueStatus.queue_name)"
    Write-Host "Active Tasks: $($queueStatus.active_tasks)"
    Write-Host "Broker: $($queueStatus.broker)"
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to get queue status" -ForegroundColor Red
    Write-Host $_.Exception.Message
}

# Step 4: Poll Task Status
Write-Host "STEP 4: Monitoring task execution..."
Write-Host "-" * 70

$maxRetries = 30
$retryCount = 0
$completed = $false

while ($retryCount -lt $maxRetries -and -not $completed) {
    try {
        $response = Invoke-WebRequest "$API_URL/api/tasks/$taskId/status"
        $statusInfo = $response.Content | ConvertFrom-Json

        $status = $statusInfo.status

        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Status: $status" -ForegroundColor Cyan

        if ($status -eq "SUCCESS") {
            Write-Host ""
            Write-Host "STEP 5: Task Completed Successfully!" -ForegroundColor Green
            Write-Host "-" * 70

            if ($statusInfo.result) {
                $result = $statusInfo.result
                Write-Host "Processing Status: $($result.status)"
                Write-Host "Valid: $($result.is_valid)"
                Write-Host "Confidence: $($result.confidence * 100)%"
                Write-Host ""
                Write-Host "Extracted Data:"
                Write-Host "-" * 70

                if ($result.data) {
                    $data = $result.data
                    Write-Host "Invoice Number: $($data.invoice_number)"
                    Write-Host "Invoice Date: $($data.invoice_date)"
                    Write-Host "Vendor: $($data.vendor_name)"
                    Write-Host "Customer: $($data.customer_name)"
                    Write-Host "Total: $($data.total)"
                    Write-Host "Currency: $($data.currency)"
                }
            }

            $completed = $true
        } elseif ($status -eq "FAILURE") {
            Write-Host "ERROR: Task failed" -ForegroundColor Red
            Write-Host "Error: $($statusInfo.error)"
            $completed = $true
        } else {
            # Still processing
            Start-Sleep -Seconds 2
            $retryCount++
        }
    } catch {
        Write-Host "ERROR: Failed to check task status" -ForegroundColor Red
        Write-Host $_.Exception.Message
        $retryCount++
    }
}

if (-not $completed) {
    Write-Host "WARNING: Task did not complete within timeout" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" * 70
Write-Host "TEST COMPLETE"
Write-Host "=" * 70
