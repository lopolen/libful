param(
    [string]$Python = "",
    [string]$VenvDir = ".venv",
    [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

$EnvFile = "libful_api/config/database_url.env"
$Utf8NoBom = New-Object System.Text.UTF8Encoding -ArgumentList $false

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
        $DatabaseUrl = "sqlite:///./dev.db"
    } else {
        $DatabaseUrl = $env:DATABASE_URL
    }
}

if ([string]::IsNullOrWhiteSpace($Python)) {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($null -ne $pyLauncher) {
        $PythonCommand = @("py", "-3")
    } else {
        $PythonCommand = @("python")
    }
} else {
    $PythonCommand = @($Python)
}

function Invoke-Python {
    param([string[]]$Arguments)

    $Executable = $PythonCommand[0]
    $PrefixArgs = @()
    if ($PythonCommand.Count -gt 1) {
        $PrefixArgs = $PythonCommand[1..($PythonCommand.Count - 1)]
    }

    & $Executable @PrefixArgs @Arguments
}

Write-Host "==> Creating virtual environment in $VenvDir"
Invoke-Python @("-m", "venv", $VenvDir)

$VenvPython = Join-Path $VenvDir "Scripts/python.exe"

Write-Host "==> Upgrading pip"
& $VenvPython -m pip install --upgrade pip

Write-Host "==> Installing project dependencies"
& $VenvPython -m pip install -r requirements.txt

if (-not (Test-Path $EnvFile)) {
    Write-Host "==> Creating $EnvFile"
    $EnvDir = Split-Path -Parent $EnvFile
    if (-not (Test-Path $EnvDir)) {
        New-Item -ItemType Directory -Path $EnvDir | Out-Null
    }
    [System.IO.File]::WriteAllText((Join-Path $RootDir $EnvFile), "DATABASE_URL=$DatabaseUrl`n", $Utf8NoBom)
} else {
    Write-Host "==> Keeping existing $EnvFile"
}

Write-Host "==> Applying database migrations"
& $VenvPython -m alembic upgrade head

Write-Host "==> Checking GUI server syntax"
& $VenvPython -m py_compile libfull_gui/server.py

Write-Host "==> Writing installed package snapshot to requirements.lock.txt"
$InstalledPackages = & $VenvPython -m pip freeze
[System.IO.File]::WriteAllText((Join-Path $RootDir "requirements.lock.txt"), (($InstalledPackages -join "`n") + "`n"), $Utf8NoBom)

Write-Host ""
Write-Host "Setup complete."
Write-Host ""
Write-Host "Run the API with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  uvicorn libful_api.main:app --reload"
Write-Host ""
Write-Host "Open API docs:"
Write-Host "  http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Run the librarian/admin GUI in another terminal:"
Write-Host "  python libfull_gui/server.py"
Write-Host ""
Write-Host "Open GUI:"
Write-Host "  http://127.0.0.1:8080"
