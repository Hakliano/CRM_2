# 1. Vytvoření venv, pokud neexistuje
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Output "✅ Virtuální prostředí vytvořeno."
} else {
    Write-Output "ℹ️ Virtuální prostředí už existuje."
}

# 2. Spuštění nového PowerShellu s aktivací venv a instalací balíčků
$command = '.\venv\Scripts\Activate.ps1; pip install --upgrade pip; pip install -r requirements.txt'
Start-Process powershell -ArgumentList "-NoExit", "-Command `$command"
