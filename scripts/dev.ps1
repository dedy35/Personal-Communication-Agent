param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$apiDir = Join-Path $repoRoot "apps\api"
$webDir = Join-Path $repoRoot "apps\web"

Write-Host "[1/3] Starting PostgreSQL container..." -ForegroundColor Cyan
Push-Location $repoRoot
try {
    docker compose -f infra/docker-compose.yml up -d postgres
}
finally {
    Pop-Location
}

$backendInstall = ""
$frontendInstall = ""
if (-not $SkipInstall) {
    $backendInstall = "& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt; "
    $frontendInstall = "npm install; "
}

$backendCmd = "Set-Location '$apiDir'; if (-not (Test-Path '.venv')) { python -m venv .venv }; ${backendInstall}& '.\.venv\Scripts\alembic.exe' upgrade head; & '.\.venv\Scripts\uvicorn.exe' app.main:app --reload --host 0.0.0.0 --port 8000"
$frontendCmd = "Set-Location '$webDir'; ${frontendInstall}npm run dev -- --hostname 0.0.0.0 --port 3000"

Write-Host "[2/3] Launching backend in a new PowerShell window..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCmd | Out-Null

Start-Sleep -Seconds 1

Write-Host "[3/3] Launching frontend in a new PowerShell window..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCmd | Out-Null

Write-Host ""
Write-Host "Development services started." -ForegroundColor Green
Write-Host "- API: http://localhost:8000/health"
Write-Host "- Web: http://localhost:3000"
Write-Host ""
Write-Host "For phone/tablet access via Tailscale, use your laptop Tailnet IP." -ForegroundColor Yellow
