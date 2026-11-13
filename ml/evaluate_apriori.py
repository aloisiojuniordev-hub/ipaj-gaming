"""Avalia o Apriori no conjunto de teste e grava as métricas reais em metrics.json.

Protocolo:
- Regras: suporte/confiança/lift recalculados no teste e comparados ao treino.
- Recomendação: para cada cesta de teste com >= 2 itens, um item é ocultado
  (aleatório, semente fixa); o restante é o "carrinho". Verifica-se se o item
  oculto aparece no Top-K. Linha de base: Top-K itens mais populares do treino.

Uso: python -m ml.evaluate_apriori
"""
import json
import random
from collections import Counter
from statistics import mean

import joblib
import pandas as pd

from ml.config import ITEMSETS_PATH, METRICS_PATH, RULES_PATH, SEED, TEST_CSV, TOP_K, TRAIN_CSV
from ml.preprocess import to_baskets
from ml.recommendation_engine import RecommendationEngine


def rule_stats(rule: dict, baskets: list[set]) -> dict:
    n = len(baskets)
    ant = set(rule["antecedents"])
    cons = set(rule["consequents"])
    n_ant = sum(1 for b in baskets if ant <= b)
    n_both = sum(1 for b in baskets if (ant | cons) <= b)
    n_cons = sum(1 for b in baskets if cons <= b)
    support = n_both / n
    confidence = n_both / n_ant if n_ant else 0.0
    lift = confidence / (n_cons / n) if n_cons else 0.0
    return {"support": support, "confidence": confidence, "lift": lift}


def avg(values):
    return round(mean(values), 4) if values else 0.0


def main() -> None:
    rules = joblib.load(RULES_PATH)
    itemsets = joblib.load(ITEMSETS_PATH)
    engine = RecommendationEngine(rules, itemsets)
    train = [set(b) for b in to_baskets(pd.read_csv(TRAIN_CSV, dtype=str))]
    test = [set(b) for b in to_baskets(pd.read_csv(TEST_CSV, dtype=str))]

    # --- 1. Qualidade das regras: treino x teste ---
    train_stats = [rule_stats(r, train) for r in rules]
    test_stats = [rule_stats(r, test) for r in rules]
    rule_quality = {
        "n_rules": len(rules),
        "train": {k: avg([s[k] for s in train_stats]) for k in ("support", "confidence", "lift")},
        "test": {k: avg([s[k] for s in test_stats]) for k in ("support", "confidence", "lift")},
        "pct_rules_lift_gt_1_in_test": round(
            100 * sum(1 for s in test_stats if s["lift"] > 1) / max(len(rules), 1), 2),
    }

    # --- 2. Recomendação (leave-one-out) ---
    rng = random.Random(SEED)
    popularity = [i for i, _ in Counter(i for b in train for i in b).most_common()]
    n_eval = n_covered = hits_engine = hits_covered = hits_baseline = 0
    precisions = []
    for basket in test:
        if len(basket) < 2:
            continue
        items = sorted(basket)
        hidden = rng.choice(items)
        cart = [i for i in items if i != hidden]
        n_eval += 1
        recs = [r["product_id"] for r in engine.recommend(cart, limit=TOP_K)]
        base = [i for i in popularity if i not in cart][:TOP_K]
        if hidden in base:
            hits_baseline += 1
        if recs:
            n_covered += 1
            hit = hidden in recs
            hits_covered += hit
            hits_engine += hit
            precisions.append(int(hit) / len(recs))

    catalog_items = {i for b in train for i in b}
    rec_items = {r["consequents"][0] for r in rules}
    evaluation = {
        "top_k": TOP_K,
        "n_test_carts_evaluated": n_eval,
        "cart_coverage_pct": round(100 * n_covered / n_eval, 2) if n_eval else 0.0,
        "hit_rate_at_k_all_carts_pct": round(100 * hits_engine / n_eval, 2) if n_eval else 0.0,
        "hit_rate_at_k_covered_carts_pct": round(100 * hits_covered / n_covered, 2) if n_covered else 0.0,
        "precision_at_k_covered_pct": round(100 * avg(precisions), 2),
        "baseline_popularity_hit_rate_at_k_pct": round(100 * hits_baseline / n_eval, 2) if n_eval else 0.0,
        "item_coverage_pct": round(100 * len(rec_items) / len(catalog_items), 2),
        "rule_quality": rule_quality,
        "limitations": "Dados simulados; hit rate mede recuperação de associações geradas pelo simulador.",
    }

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8")) if METRICS_PATH.exists() else {}
    metrics["evaluation"] = evaluation
    METRICS_PATH.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(evaluation, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
