# 1. Vytvoření venv, pokud neexistuje
if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Output "✅ Virtuální prostředí vytvořeno."
} else {
    Write-Output "ℹ️ Virtuální prostředí už existuje."
}

# 2. Vytvoření příkazu do proměnné
$command = ".\venv\Scripts\Activate.ps1; pip install --upgrade pip; pip install -r requirements.txt"

# 3. Spuštění nového PowerShellu s tímto příkazem
Start-Process powershell -ArgumentList "-NoExit", "-Command", $command
