Param(
    [switch]$NoFrontend,
    [switch]$NoBackend
)

Write-Host "Starting Binance analytics project..." -ForegroundColor Cyan

if (-not $NoBackend) {
    Write-Host "Launching FastAPI backend" -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","backend.app.main:app","--reload","--host","0.0.0.0","--port","8000" -WorkingDirectory (Get-Location)
}

if (-not $NoFrontend) {
    Write-Host "Launching React frontend" -ForegroundColor Green
    Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory (Join-Path (Get-Location) "frontend")
}

Write-Host "Processes started. Use Stop-Process to terminate when finished." -ForegroundColor Yellow



