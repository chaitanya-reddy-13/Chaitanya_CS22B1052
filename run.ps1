# Single command to run both backend and frontend
# Usage: .\run.ps1

$ErrorActionPreference = "Stop"

Write-Host "Starting Binance Analytics App..." -ForegroundColor Cyan

# Get current directory
$rootDir = $PWD.Path

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install backend dependencies if needed
Write-Host "Checking backend dependencies..." -ForegroundColor Yellow
pip install -q -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}

# Check if frontend node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install frontend dependencies" -ForegroundColor Red
        exit 1
    }
    Set-Location $rootDir
}

Write-Host ""
Write-Host "Starting backend on http://localhost:8000..." -ForegroundColor Green

# Start backend in a new window with full path
$backendScript = @"
cd '$rootDir'
.\.venv\Scripts\Activate.ps1
Write-Host 'Backend starting on http://localhost:8000' -ForegroundColor Green
uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
"@

$backendScript | Out-File -FilePath "$env:TEMP\backend_start.ps1" -Encoding UTF8
Start-Process powershell -ArgumentList "-NoExit", "-File", "$env:TEMP\backend_start.ps1"

# Wait for backend to be ready
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts -and -not $backendReady) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 1 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "Backend is ready!" -ForegroundColor Green
        }
    } catch {
        $attempt++
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

if (-not $backendReady) {
    Write-Host ""
    Write-Host "Warning: Backend may not be ready. Frontend will start anyway." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting frontend on http://localhost:5173..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

# Start frontend in current window
Set-Location frontend
npm run dev

