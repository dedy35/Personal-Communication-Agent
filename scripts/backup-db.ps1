param(
    [string]$OutputDir
)

$ErrorActionPreference = "Stop"

function Get-EnvValue {
    param(
        [string]$FilePath,
        [string]$Key,
        [string]$DefaultValue
    )

    if (-not (Test-Path $FilePath)) {
        return $DefaultValue
    }

    $line = Get-Content $FilePath | Where-Object { $_ -match "^$Key=" } | Select-Object -First 1
    if (-not $line) {
        return $DefaultValue
    }

    $value = $line.Substring($line.IndexOf("=") + 1).Trim()
    if ([string]::IsNullOrWhiteSpace($value)) {
        return $DefaultValue
    }

    return $value
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$envFile = Join-Path $repoRoot ".env"

$dbName = Get-EnvValue -FilePath $envFile -Key "POSTGRES_DB" -DefaultValue "pca"
$dbUser = Get-EnvValue -FilePath $envFile -Key "POSTGRES_USER" -DefaultValue "pca_user"
$containerName = "pca-postgres"

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $repoRoot "backups\db"
}

New-Item -Path $OutputDir -ItemType Directory -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$dumpPath = Join-Path $OutputDir ("pca-backup-{0}.sql" -f $timestamp)

Write-Host "Creating PostgreSQL backup from container '$containerName'..." -ForegroundColor Cyan

$dumpSql = docker exec $containerName pg_dump -U $dbUser -d $dbName --no-owner --no-privileges
if ($LASTEXITCODE -ne 0) {
    throw "pg_dump failed. Make sure Docker is running and container '$containerName' is healthy."
}

[System.IO.File]::WriteAllText($dumpPath, $dumpSql, [System.Text.UTF8Encoding]::new($false))

Write-Host "Backup created: $dumpPath" -ForegroundColor Green
