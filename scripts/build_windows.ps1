Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location (Join-Path $PSScriptRoot '..')

if (-not (Test-Path '.venv')) {
    python -m venv .venv
}

& .\.venv\Scripts\Activate.ps1
pip install -r parking_app\requirements.txt
python -m PyInstaller --clean --noconfirm parking_accounting.spec
