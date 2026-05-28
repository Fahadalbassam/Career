# CareerFinder.ai — terminal CLI launcher (Windows PowerShell)
# Starts backend if needed, then opens the interactive CLI in a new window.

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$BackendDir = Join-Path $RepoRoot "backend"
$ApiBase = if ($env:CAREERFINDER_API_BASE) { $env:CAREERFINDER_API_BASE.TrimEnd("/") } else { "http://127.0.0.1:8000" }
$HealthUrl = "$ApiBase/health"
$MaxWaitSeconds = 60

function Test-BackendHealth {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

Write-Host "CareerFinder.ai terminal launcher" -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"
Write-Host "API:  $ApiBase"
Write-Host ""

if (-not (Test-BackendHealth)) {
    Write-Host "Backend not reachable at $HealthUrl" -ForegroundColor Yellow
    Write-Host "Starting backend in a new window ..." -ForegroundColor Yellow

    $backendCmd = "Set-Location -LiteralPath '$BackendDir'; python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    Start-Process powershell -ArgumentList @("-NoExit", "-Command", $backendCmd)

    $elapsed = 0
    $ready = $false
    while ($elapsed -lt $MaxWaitSeconds) {
        Start-Sleep -Seconds 2
        $elapsed += 2
        if (Test-BackendHealth) {
            $ready = $true
            break
        }
        Write-Host "  Waiting for backend ($elapsed s) ..."
    }

    if (-not $ready) {
        Write-Host ""
        Write-Host "ERROR: Backend did not respond at $HealthUrl within ${MaxWaitSeconds}s." -ForegroundColor Red
        Write-Host "Check the backend window for errors (Python, uvicorn, port 8000 in use)." -ForegroundColor Red
        exit 1
    }

    Write-Host "Backend is up." -ForegroundColor Green
} else {
    Write-Host "Backend already running." -ForegroundColor Green
}

Write-Host "Launching terminal CLI in a new window ..." -ForegroundColor Cyan
$cliCmd = "Set-Location -LiteralPath '$RepoRoot'; python scripts/careerfinder_cli.py"
Start-Process powershell -ArgumentList @("-NoExit", "-Command", $cliCmd)

Write-Host ""
Write-Host "CLI window opened. This launcher window can be closed." -ForegroundColor Green
