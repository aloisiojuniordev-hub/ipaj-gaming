"""Motor de recomendação (IPAJ CORE) baseado em regras de associação Apriori.

Depende apenas de joblib: seguro para rodar no backend de produção.
"""
from __future__ import annotations

from pathlib import Path

import joblib

from ml.config import ITEMSETS_PATH, RULES_PATH


class RecommendationEngine:
    def __init__(self, rules: list[dict], itemsets: list[dict] | None = None):
        self.rules = rules
        self.itemsets = itemsets or []
        self._rule_sets = [(set(r["antecedents"]), r["consequents"][0], r) for r in rules]

    @classmethod
    def load(cls, rules_path: Path = RULES_PATH, itemsets_path: Path = ITEMSETS_PATH):
        rules = joblib.load(rules_path)
        itemsets = joblib.load(itemsets_path) if Path(itemsets_path).exists() else []
        return cls(rules, itemsets)

    def recommend(self, cart: list[str], limit: int = 5) -> list[dict]:
        """Recomenda itens ausentes do carrinho.

        Para cada candidato escolhe-se a melhor regra aplicável (maior confiança,
        desempate por lift). Resultado ordenado por confiança, lift e id.
        Retorna lista vazia quando nenhuma regra se aplica (sem fallback inventado).
        """
        cart_set = set(cart)
        best: dict[str, dict] = {}
        for antecedent, consequent, rule in self._rule_sets:
            if consequent in cart_set or not antecedent <= cart_set:
                continue
            current = best.get(consequent)
            if current is None or (rule["confidence"], rule["lift"]) > (current["confidence"], current["lift"]):
                best[consequent] = rule
        ranked = sorted(best.items(), key=lambda kv: (-kv[1]["confidence"], -kv[1]["lift"], kv[0]))
        return [
            {
                "product_id": item,
                "confidence": rule["confidence"],
                "lift": rule["lift"],
                "support": rule["support"],
                "because": rule["antecedents"],
            }
            for item, rule in ranked[:limit]
        ]

    def top_rules(self, limit: int = 20, sort_by: str = "lift") -> list[dict]:
        if sort_by not in {"lift", "confidence", "support"}:
            raise ValueError("sort_by deve ser lift, confidence ou support")
        return sorted(self.rules, key=lambda r: (-r[sort_by], r["antecedents"], r["consequents"]))[:limit]
