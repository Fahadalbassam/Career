# CareerFinder.ai — full stack dev launcher (backend + frontend in separate windows)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"

Write-Host "CareerFinder.ai full stack launcher" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Backend:  http://127.0.0.1:8000"
Write-Host "  Frontend: http://localhost:3000"
Write-Host "  Chat:     http://localhost:3000/chat"
Write-Host ""

$backendCmd = "Set-Location -LiteralPath '$BackendDir'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
$frontendCmd = "Set-Location -LiteralPath '$FrontendDir'; npm run dev"

Write-Host "Starting backend in a new window ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd)

Start-Sleep -Seconds 1

Write-Host "Starting frontend in a new window ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $frontendCmd)

Write-Host ""
Write-Host "Both servers launched. Close their windows to stop them." -ForegroundColor Green
Write-Host "This launcher window can be closed." -ForegroundColor Green
