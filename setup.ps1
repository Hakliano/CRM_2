# 1. Vytvoření venv, pokud neexistuje
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Output "✅ Virtuální prostředí vytvořeno."
} else {
    Write-Output "ℹ️ Virtuální prostředí už existuje."
}

# 2. Aktivace v novém procesu PowerShell a instalace requirements
Start-Process powershell -ArgumentList "-NoExit", "-Command `"& { .\venv\Scripts\Activate.ps1; pip install -r requirements.txt }`""
