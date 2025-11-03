# Single command to run both backend and frontend
# Usage: .\run.ps1

Write-Host "Starting Binance Analytics App..." -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Install backend dependencies if needed
if (-not (Test-Path ".venv\Scripts\pip.exe")) {
    Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
    pip install -r backend\requirements.txt
}

# Check if frontend node_modules exists
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

Write-Host "Starting backend on http://localhost:8000" -ForegroundColor Green
Write-Host "Starting frontend on http://localhost:5173" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop both services" -ForegroundColor Yellow
Write-Host ""

# Start backend in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\Activate.ps1; uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000 --reload"

# Wait a moment for backend to start
Start-Sleep -Seconds 2

# Start frontend in current window
Set-Location frontend
npm run dev

