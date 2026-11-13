# IPAJ Gaming - setup local (Windows PowerShell)
# Uso (na raiz do repositorio):  powershell -ExecutionPolicy Bypass -File scripts\setup.ps1 [-Retrain]
param([switch]$Retrain)
$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "==> Criando ambiente virtual Python (.venv)"
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "==> Instalando dependencias Python (backend + ml)"
& $py -m pip install --upgrade pip
& $py -m pip install -r backend\requirements-dev.txt -r ml\requirements.txt
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias Python" }

if ($Retrain -or -not (Test-Path "ml\artifacts\rules.joblib")) {
    Write-Host "==> Gerando dataset e treinando o Apriori"
    foreach ($m in "ml.generate_catalog", "ml.generate_transactions", "ml.preprocess", "ml.train_apriori", "ml.evaluate_apriori") {
        & $py -m $m
        if ($LASTEXITCODE -ne 0) { throw "Falha em $m" }
    }
}

Write-Host "==> Arquivos de ambiente"
if (-not (Test-Path "backend\.env")) { Copy-Item "backend\.env.example" "backend\.env"; Write-Host "   backend\.env criado (revise JWT_SECRET)" }
if (-not (Test-Path "frontend\.env.local")) { Copy-Item "frontend\.env.example" "frontend\.env.local" }

Write-Host "==> Instalando dependencias do frontend"
Push-Location frontend
npm ci
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Falha no npm ci" }
Pop-Location

Write-Host ""
Write-Host "Pronto. Em dois terminais:"
Write-Host "  cd backend;  ..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload"
Write-Host "  cd frontend; npm run dev"
