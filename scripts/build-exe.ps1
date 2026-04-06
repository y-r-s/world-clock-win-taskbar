Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Ensure script runs from repository root regardless of caller location.
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Host "Installing/updating build dependency: pyinstaller"
python -m pip install --upgrade pyinstaller

Write-Host "Building WorldClock.exe"
pyinstaller `
  --noconfirm `
  --clean `
  --onefile `
  --windowed `
  --name WorldClock `
  main.py

Write-Host "Build complete: dist\\WorldClock.exe"
