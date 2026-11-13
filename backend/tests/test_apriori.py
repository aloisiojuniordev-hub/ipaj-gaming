"""Testes do motor Apriori e da integridade dos artefatos persistidos."""
import json

import joblib
import pytest

from app.core.config import REPO_ROOT
from ml.recommendation_engine import RecommendationEngine

ART = REPO_ROOT / "ml" / "artifacts"


@pytest.fixture(scope="module")
def artifacts():
    return joblib.load(ART / "rules.joblib"), joblib.load(ART / "itemsets.joblib"), \
        json.loads((ART / "metrics.json").read_text(encoding="utf-8"))


def test_artifacts_integrity(artifacts):
    rules, itemsets, metrics = artifacts
    params = metrics["training"]["parameters"]
    assert len(rules) == metrics["training"]["n_rules"] > 0
    assert len(itemsets) == metrics["training"]["n_itemsets"] > 0
    for r in rules:
        assert r["antecedents"] and len(r["consequents"]) == 1
        assert not set(r["antecedents"]) & set(r["consequents"])
        assert r["confidence"] >= params["min_confidence"] - 1e-9
        assert r["lift"] >= params["min_lift"] - 1e-9
        assert 0 < r["support"] <= r["antecedent_support"] <= 1
        # confiança = suporte(A∪B) / suporte(A)
        assert r["confidence"] == pytest.approx(r["support"] / r["antecedent_support"], abs=1e-4)
        # lift = confiança / suporte(B)
        assert r["lift"] == pytest.approx(r["confidence"] / r["consequent_support"], rel=1e-3)
    assert all(i["support"] >= params["min_support"] - 1e-9 for i in itemsets)
    assert "evaluation" in metrics


def test_engine_basic_contract():
    rules = [
        {"antecedents": ["A"], "consequents": ["B"], "support": .2, "confidence": .8, "lift": 2.0},
        {"antecedents": ["A"], "consequents": ["C"], "support": .1, "confidence": .5, "lift": 3.0},
        {"antecedents": ["A", "D"], "consequents": ["C"], "support": .05, "confidence": .9, "lift": 4.0},
        {"antecedents": ["X"], "consequents": ["Y"], "support": .1, "confidence": .99, "lift": 5.0},
    ]
    eng = RecommendationEngine(rules)
    assert [r["product_id"] for r in eng.recommend(["A"])] == ["B", "C"]
    # Com A+D, a regra mais forte para C (0,9) vence e C sobe para o topo.
    recs = eng.recommend(["A", "D"])
    assert [r["product_id"] for r in recs] == ["C", "B"]
    assert recs[0]["because"] == ["A", "D"]
    # Nunca recomenda o que já está no carrinho; sem regra aplicável -> vazio.
    assert all(r["product_id"] != "B" for r in eng.recommend(["A", "B"]))
    assert eng.recommend(["Z"]) == []
    assert len(eng.recommend(["A"], limit=1)) == 1


def test_engine_on_real_rules_recovers_planted_association(artifacts):
    eng = RecommendationEngine(artifacts[0], artifacts[1])
    # O simulador planta Switch -> capa (p=0,65) e microSD (p=0,60).
    ids = [r["product_id"] for r in eng.recommend(["P003"], limit=5)]
    assert "P037" in ids and "P036" in ids


def test_metrics_beat_popularity_baseline(artifacts):
    ev = artifacts[2]["evaluation"]
    assert ev["hit_rate_at_k_all_carts_pct"] > ev["baseline_popularity_hit_rate_at_k_pct"]
    assert ev["rule_quality"]["pct_rules_lift_gt_1_in_test"] > 90
