# JARVIS AI Chatbot Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Find Python
$python = $null
$paths = @(
    (Get-ChildItem "$env:LOCALAPPDATA\Python\pythoncore-*\python.exe" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName),
    "$env:LOCALAPPDATA\Python\bin\python.exe",
    (Get-Command python -ErrorAction SilentlyContinue).Source
)
foreach ($p in $paths) {
    if ($p -and (Test-Path $p)) { $python = $p; break }
}

if (-not $python) {
    Write-Host "Python nao encontrado!"
    Read-Host "Pressione Enter"
    exit 1
}

Write-Host "[*] Usando: $python"
Write-Host "[*] Iniciando JARVIS..."
& $python main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Codigo: $LASTEXITCODE"
    Read-Host "Pressione Enter"
}