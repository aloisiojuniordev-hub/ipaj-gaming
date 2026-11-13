"""Treina o Apriori (mlxtend) no conjunto de treino e persiste os artefatos.

Os artefatos são salvos como listas/dicionários simples (sem DataFrame),
de modo que o backend de produção não precisa de pandas nem mlxtend.

Uso: python -m ml.train_apriori
"""
import json
from datetime import UTC, datetime

import joblib
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

from ml.config import (
    ARTIFACTS_DIR,
    ITEMSETS_PATH,
    MAX_LEN,
    METRICS_PATH,
    MIN_CONFIDENCE,
    MIN_LIFT,
    MIN_SUPPORT,
    RULES_PATH,
    SEED,
    TEST_CSV,
    TRAIN_CSV,
)
from ml.preprocess import to_baskets


def mine(baskets: list[list[str]], min_support=MIN_SUPPORT, min_confidence=MIN_CONFIDENCE,
         min_lift=MIN_LIFT, max_len=MAX_LEN):
    """Retorna (itemsets, regras) como listas de dicionários."""
    encoder = TransactionEncoder()
    onehot = pd.DataFrame(encoder.fit(baskets).transform(baskets), columns=encoder.columns_)
    freq = apriori(onehot, min_support=min_support, use_colnames=True, max_len=max_len)
    itemsets = [
        {"items": sorted(row.itemsets), "support": round(float(row.support), 6)}
        for row in freq.itertuples()
    ]
    rules: list[dict] = []
    if len(freq) > 0:
        raw = association_rules(freq, metric="confidence", min_threshold=min_confidence)
        raw = raw[(raw["lift"] >= min_lift) & (raw["consequents"].apply(len) == 1)]
        # Colunas do mlxtend têm espaços ("antecedent support"): usar dicionários.
        for row in raw.to_dict("records"):
            rules.append({
                "antecedents": sorted(row["antecedents"]),
                "consequents": sorted(row["consequents"]),
                "support": round(float(row["support"]), 6),
                "antecedent_support": round(float(row["antecedent support"]), 6),
                "consequent_support": round(float(row["consequent support"]), 6),
                "confidence": round(float(row["confidence"]), 6),
                "lift": round(float(row["lift"]), 6),
                "leverage": round(float(row["leverage"]), 6),
            })
    rules.sort(key=lambda r: (-r["confidence"], -r["lift"], r["antecedents"], r["consequents"]))
    return itemsets, rules


def main() -> None:
    train_df = pd.read_csv(TRAIN_CSV, dtype=str)
    baskets = to_baskets(train_df)
    itemsets, rules = mine(baskets)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(rules, RULES_PATH)
    joblib.dump(itemsets, ITEMSETS_PATH)

    train_info = {
        "trained_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "n_train_transactions": len(baskets),
        "n_test_transactions": len(pd.read_csv(TEST_CSV, dtype=str)),
        "parameters": {"min_support": MIN_SUPPORT, "min_confidence": MIN_CONFIDENCE,
                       "min_lift": MIN_LIFT, "max_len": MAX_LEN},
        "n_itemsets": len(itemsets),
        "n_rules": len(rules),
    }
    # evaluate_apriori.py completa o restante; preservamos métricas existentes de avaliação.
    metrics = {}
    if METRICS_PATH.exists():
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        metrics.pop("evaluation", None)  # avaliação antiga não vale para o novo modelo
    metrics["training"] = train_info
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Itemsets: {len(itemsets)} | Regras: {len(rules)} | Artefatos em {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
