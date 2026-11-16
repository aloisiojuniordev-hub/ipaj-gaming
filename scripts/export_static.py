"""Exporta os artefatos REAIS do Apriori e o catálogo para o frontend e para o Supabase.

Sem servidor Python em produção: o treino continua em Python (mlxtend, ml/train_apriori.py)
e este script publica o resultado como dados estáticos:

- frontend/src/data/catalog.json      catálogo (data/catalog/products.csv)
- frontend/src/data/rules.json        as regras de ml/artifacts/rules.joblib, sem alteração
- frontend/src/data/itemsets.json     ml/artifacts/itemsets.joblib
- frontend/src/data/metrics.json      ml/artifacts/metrics.json
- frontend/src/test/fixtures/expected_recommendations.json
      saídas do motor Python (ml/recommendation_engine.py) para conferir o motor TypeScript
- database/migrations/004_seed_products.sql   carga idempotente do catálogo no PostgreSQL

Uso (na raiz):  python scripts/export_static.py
O teste backend/tests/test_export_static.py falha se os arquivos versionados divergirem.
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import joblib  # noqa: E402

from ml.config import CATALOG_CSV, ITEMSETS_PATH, METRICS_PATH, RULES_PATH  # noqa: E402
from ml.recommendation_engine import RecommendationEngine  # noqa: E402

DATA = ROOT / "frontend" / "src" / "data"
FIXTURE = ROOT / "frontend" / "src" / "test" / "fixtures" / "expected_recommendations.json"
SEED_SQL = ROOT / "database" / "migrations" / "004_seed_products.sql"


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def _sql(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_outputs() -> dict[Path, str]:
    with CATALOG_CSV.open(encoding="utf-8", newline="") as fh:
        catalog = [{"id": r["product_id"], "name": r["name"], "category": r["category"],
                    "price": r["price"], "description": r["description"]} for r in csv.DictReader(fh)]
    rules = joblib.load(RULES_PATH)
    itemsets = joblib.load(ITEMSETS_PATH)
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    # Casos de conferência: todo produto sozinho + todo par frequente (itemsets de 2 itens).
    engine = RecommendationEngine(rules, itemsets)
    carts = [[p["id"]] for p in catalog] + [i["items"] for i in itemsets if len(i["items"]) == 2]
    expected = [{"cart": c, "recs": [{"product_id": r["product_id"], "confidence": r["confidence"],
                                      "lift": r["lift"], "because": r["because"]}
                                     for r in engine.recommend(c, limit=5)]} for c in carts]

    values = ",\n".join(
        f"  ({_sql(p['id'])}, {_sql(p['name'])}, {_sql(p['category'])}, {p['price']}, {_sql(p['description'])})"
        for p in catalog)
    seed = (
        "-- Migração 004 — carga do catálogo (50 produtos) a partir de data/catalog/products.csv.\n"
        "-- GERADO por scripts/export_static.py: não edite à mão.\n"
        "-- Idempotente e não destrutiva: insere ou atualiza; nunca apaga produtos.\n"
        "-- Os preços desta tabela são os usados pela função create_order (migração 003).\n\n"
        "INSERT INTO products (id, name, category, price, description) VALUES\n"
        f"{values}\n"
        "ON CONFLICT (id) DO UPDATE SET\n"
        "  name = EXCLUDED.name, category = EXCLUDED.category,\n"
        "  price = EXCLUDED.price, description = EXCLUDED.description;\n"
    )
    return {
        DATA / "catalog.json": _json(catalog),
        DATA / "rules.json": _json(rules),
        DATA / "itemsets.json": _json(itemsets),
        DATA / "metrics.json": _json(metrics),
        FIXTURE: _json(expected),
        SEED_SQL: seed,
    }


def main() -> None:
    for path, content in build_outputs().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"gerado {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
