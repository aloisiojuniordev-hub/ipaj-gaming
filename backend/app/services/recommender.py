"""Carrega os artefatos do Apriori uma única vez e expõe o motor para a API."""
import json
from functools import lru_cache

from app.core.config import get_settings
from ml.recommendation_engine import RecommendationEngine


class ArtifactsUnavailable(RuntimeError):
    pass


@lru_cache
def get_engine() -> RecommendationEngine:
    d = get_settings().artifacts_dir
    rules, itemsets = d / "rules.joblib", d / "itemsets.joblib"
    if not rules.exists():
        raise ArtifactsUnavailable(f"Artefatos do Apriori não encontrados em {d}. Rode ml/train_apriori.py.")
    return RecommendationEngine.load(rules, itemsets)


@lru_cache
def get_metrics() -> dict:
    path = get_settings().artifacts_dir / "metrics.json"
    if not path.exists():
        raise ArtifactsUnavailable(f"metrics.json não encontrado em {path.parent}.")
    return json.loads(path.read_text(encoding="utf-8"))
