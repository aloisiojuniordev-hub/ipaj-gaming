"""Verificação estrutural do repositório IPAJ Gaming.

Checa: arquivos obrigatórios, integridade dos artefatos Apriori, dataset e ausência
de segredos óbvios em arquivos versionáveis. Não acessa rede nem banco.

Uso:
    python scripts/verify_project.py               # verificação completa
    python scripts/verify_project.py --artifacts-only
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED = [
    ".github/workflows/frontend-ci.yml", ".github/workflows/backend-ci.yml", ".github/pull_request_template.md",
    "frontend/package.json", "frontend/package-lock.json", "frontend/vite.config.ts", "frontend/tsconfig.json",
    "frontend/.env.example", "netlify.toml", "frontend/src/App.tsx", "frontend/src/main.tsx",
    "backend/app/main.py", "backend/app/api/products.py", "backend/app/api/recommendations.py",
    "backend/app/api/laboratory.py", "backend/app/api/orders.py", "backend/app/api/users.py",
    "backend/app/core/config.py", "backend/app/core/security.py", "backend/app/database/connection.py",
    "backend/app/database/models.py", "backend/requirements.txt", "backend/.env.example",
    "ml/generate_catalog.py", "ml/generate_transactions.py", "ml/preprocess.py", "ml/train_apriori.py",
    "ml/evaluate_apriori.py", "ml/recommendation_engine.py",
    "ml/artifacts/rules.joblib", "ml/artifacts/itemsets.joblib", "ml/artifacts/metrics.json",
    "data/raw/transactions.csv", "data/catalog/products.csv",
    "notebooks/apriori_analysis.ipynb", "database/schema.sql", "database/seed.py",
    "docs/architecture.md", "docs/dataset.md", "docs/apriori-methodology.md", "docs/evaluation.md",
    "docs/api.md", "docs/deployment.md", "docs/presentation-guide.md", "docs/academic-report.md",
    "scripts/setup.ps1", "scripts/setup.sh", ".gitignore", ".gitattributes", ".editorconfig",
    "README.md", "CONTRIBUTING.md", "render.yaml", ".env.example",
]

SECRET_PATTERNS = [
    re.compile(r"postgres(?:ql)?://[^:\s]+:(?!<SENHA>|<senha>)[^@\s<]{6,}@"),  # senha real em URL
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\."),  # JWT (ex.: chave Supabase)
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"sk_live_[A-Za-z0-9]{20,}"),
]
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "__pycache__", ".pytest_cache", ".ruff_cache"}
TEXT_EXT = {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yml", ".yaml", ".toml", ".txt", ".sql", ".sh",
            ".ps1", ".html", ".css", ".example", ".ipynb", ".cfg", ".ini"}

errors: list[str] = []


def check(cond: bool, msg: str) -> None:
    print(("  OK   " if cond else "  FALHA ") + msg)
    if not cond:
        errors.append(msg)


def verify_artifacts() -> None:
    import joblib

    print("Artefatos Apriori")
    art = ROOT / "ml" / "artifacts"
    rules = joblib.load(art / "rules.joblib")
    itemsets = joblib.load(art / "itemsets.joblib")
    metrics = json.loads((art / "metrics.json").read_text(encoding="utf-8"))
    tr = metrics.get("training", {})
    check(len(rules) == tr.get("n_rules") and len(rules) > 0, f"{len(rules)} regras coerentes com metrics.json")
    check(len(itemsets) == tr.get("n_itemsets") and len(itemsets) > 0, f"{len(itemsets)} itemsets coerentes")
    check("evaluation" in metrics, "metrics.json contém avaliação")
    p = tr.get("parameters", {})
    check(all(r["confidence"] >= p["min_confidence"] - 1e-9 and r["lift"] >= p["min_lift"] - 1e-9 for r in rules),
          "todas as regras respeitam confiança e lift mínimos")
    with (ROOT / "data" / "catalog" / "products.csv").open(encoding="utf-8") as fh:
        catalog = {row["product_id"] for row in csv.DictReader(fh)}
    used = {i for r in rules for i in r["antecedents"] + r["consequents"]}
    check(used <= catalog, "regras referenciam apenas produtos do catálogo")
    with (ROOT / "data" / "raw" / "transactions.csv").open(encoding="utf-8") as fh:
        n = sum(1 for _ in csv.DictReader(fh))
    check(n == tr.get("n_train_transactions", 0) + tr.get("n_test_transactions", 0),
          f"{n} transações = treino + teste")


def verify_files() -> None:
    print("Arquivos obrigatórios")
    for rel in REQUIRED:
        check((ROOT / rel).exists(), rel)


def verify_secrets() -> None:
    print("Varredura de segredos")
    found = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts) or not path.is_file():
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            found.append(f"{path.relative_to(ROOT)} (arquivo .env real; deve ficar fora do Git)")
            continue
        if path.suffix not in TEXT_EXT or path.stat().st_size > 2_000_000 or path.name == "verify_project.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                found.append(f"{path.relative_to(ROOT)} ({pat.pattern[:30]}...)")
    for f in found:
        print("  AVISO " + f)
    check(not [f for f in found if "arquivo .env real" not in f], "nenhum segredo detectado em arquivos de texto")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts-only", action="store_true")
    args = ap.parse_args()
    verify_artifacts()
    if not args.artifacts_only:
        verify_files()
        verify_secrets()
    print(f"\n{'APROVADO' if not errors else f'REPROVADO: {len(errors)} falha(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
