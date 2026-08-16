$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/kriskarter/cod2-chat-translator.git"
$Source = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Target = Join-Path $env:TEMP "cod2-chat-translator-publish"

function Find-Git {
    $cmd = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $root = Join-Path $env:LOCALAPPDATA "GitHubDesktop"
    if (Test-Path $root) {
        $candidates = Get-ChildItem $root -Directory -Filter "app-*" -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "resources\app\git\cmd\git.exe" }
        foreach ($p in $candidates) { if (Test-Path $p) { return $p } }
    }
    throw "Git was not found. Install/open GitHub Desktop first."
}

$Git = Find-Git
Write-Host "Using Git: $Git"
if (Test-Path $Target) { Remove-Item $Target -Recurse -Force }
& $Git clone $RepoUrl $Target
if ($LASTEXITCODE -ne 0) { throw "git clone failed" }

# Copy project into the clean clone, preserving .git and excluding local build/user data.
$excludeDirs = @('.git','.buildvenv','.venv','build','dist','release','__pycache__')
Get-ChildItem $Target -Force | Where-Object { $_.Name -ne '.git' } | Remove-Item -Recurse -Force
Get-ChildItem $Source -Force | Where-Object { $excludeDirs -notcontains $_.Name } | ForEach-Object {
    Copy-Item $_.FullName -Destination $Target -Recurse -Force
}
Get-ChildItem $Target -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Remove-Item (Join-Path $Target 'config.json') -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $Target 'config.backup.json') -Force -ErrorAction SilentlyContinue

Push-Location $Target
try {
    & $Git add -A
    $status = & $Git status --porcelain
    if (-not $status) {
        Write-Host "Nothing to publish. Repository is already up to date."
        exit 0
    }
    & $Git commit -m "Release source v1.11.1"
    if ($LASTEXITCODE -ne 0) { throw "git commit failed" }
    & $Git push origin main
    if ($LASTEXITCODE -ne 0) { throw "git push failed. GitHub may ask you to sign in via Git Credential Manager." }
    Write-Host "Source pushed to kriskarter/cod2-chat-translator"
} finally {
    Pop-Location
}
