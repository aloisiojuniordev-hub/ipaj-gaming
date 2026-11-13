#!/usr/bin/env bash
# IPAJ Gaming - setup local (Linux/macOS)
# Uso (na raiz do repositório): bash scripts/setup.sh [--retrain]
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Criando ambiente virtual Python (.venv)"
[ -d .venv ] || python3 -m venv .venv
PY=.venv/bin/python

echo "==> Instalando dependências Python (backend + ml)"
$PY -m pip install --upgrade pip
$PY -m pip install -r backend/requirements-dev.txt -r ml/requirements.txt

if [ "${1:-}" = "--retrain" ] || [ ! -f ml/artifacts/rules.joblib ]; then
  echo "==> Gerando dataset e treinando o Apriori"
  for m in ml.generate_catalog ml.generate_transactions ml.preprocess ml.train_apriori ml.evaluate_apriori; do
    $PY -m "$m"
  done
fi

echo "==> Arquivos de ambiente"
[ -f backend/.env ] || { cp backend/.env.example backend/.env; echo "   backend/.env criado (revise JWT_SECRET)"; }
[ -f frontend/.env.local ] || cp frontend/.env.example frontend/.env.local

echo "==> Instalando dependências do frontend"
(cd frontend && npm ci)

cat <<'EOF'

Pronto. Em dois terminais:
  cd backend  && ../.venv/bin/python -m uvicorn app.main:app --reload
  cd frontend && npm run dev
EOF
