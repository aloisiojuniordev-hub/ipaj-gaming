"""Gera notebooks/apriori_analysis.ipynb a partir de células definidas aqui.

Manter o notebook como código facilita revisão no Git. Para gerar e executar:
    python notebooks/build_notebook.py --execute
"""
import argparse
import sys
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
OUT = HERE / "apriori_analysis.ipynb"
sys.path.insert(0, str(HERE.parent))
from ml import config  # noqa: E402

cells = [
    ("md", """# IPAJ Gaming — Análise com Apriori

Notebook de mineração de dados do projeto **IPAJ Gaming** (Iran Pablo e Aloisio Junior).

Etapas: carregamento do dataset simulado → análise exploratória → divisão 80/20 →
itemsets frequentes → regras de associação → avaliação no teste.

Todas as funções vêm de `ml/`, as mesmas usadas pelo backend, para que o notebook
e o sistema publicado produzam exatamente os mesmos resultados."""),
    ("code", """import sys, json
from pathlib import Path
ROOT = Path.cwd().resolve()
if not (ROOT / "ml").exists():
    ROOT = ROOT.parent  # executando de dentro de notebooks/
sys.path.insert(0, str(ROOT))

import pandas as pd
from ml import config
from ml.preprocess import load_baskets, split, to_baskets
from ml.train_apriori import mine
pd.set_option("display.max_colwidth", 80)"""),
    ("md", "## 1. Dataset e catálogo"),
    ("code", """catalog = pd.read_csv(config.CATALOG_CSV)
tx = load_baskets(config.TRANSACTIONS_CSV)
names = dict(zip(catalog.product_id, catalog.name))
print(f"Produtos: {len(catalog)} | Transações: {len(tx)}")
tx.head()"""),
    ("code", """tx["n_items"] = tx["n_items"].astype(int)
print(tx["n_items"].describe().round(2))
tx["n_items"].value_counts().sort_index()"""),
    ("code", """tx["scenario"].value_counts(normalize=True).round(3)"""),
    ("code", """from collections import Counter
freq = Counter(i for b in to_baskets(tx) for i in b)
top = pd.DataFrame([(names[k], v, v / len(tx)) for k, v in freq.most_common(10)],
                   columns=["produto", "transações", "suporte"])
top.round(3)"""),
    ("md", "## 2. Divisão treino/teste (80/20, semente 42)"),
    ("code", """train_df, test_df = split(tx)
print(len(train_df), len(test_df))
assert set(train_df.transaction_id).isdisjoint(test_df.transaction_id)"""),
    ("md", f"""## 3. Apriori (mlxtend)

Parâmetros: suporte mínimo = {config.MIN_SUPPORT}, confiança mínima = {config.MIN_CONFIDENCE},
lift mínimo = {config.MIN_LIFT}, tamanho máximo = {config.MAX_LEN}."""),
    ("code", """itemsets, rules = mine(to_baskets(train_df))
print(f"Itemsets frequentes: {len(itemsets)} | Regras: {len(rules)}")
pd.Series([len(i["items"]) for i in itemsets]).value_counts().sort_index().rename("itemsets por tamanho")"""),
    ("code", """def label(ids): return " + ".join(names[i] for i in ids)
rules_df = pd.DataFrame([{"se": label(r["antecedents"]), "então": label(r["consequents"]),
                          "suporte": r["support"], "confiança": r["confidence"], "lift": r["lift"]}
                         for r in rules])
rules_df.sort_values("lift", ascending=False).head(15).round(3)"""),
    ("code", """rules_df.sort_values("confiança", ascending=False).head(10).round(3)"""),
    ("code", """rules_df[["suporte", "confiança", "lift"]].describe().round(3)"""),
    ("md", "## 4. Recomendação e avaliação"),
    ("code", """from ml.recommendation_engine import RecommendationEngine
engine = RecommendationEngine(rules, itemsets)
for cart in (["P001"], ["P003"], ["P021"], ["P046", "P049"], ["P050"]):
    recs = engine.recommend(cart, limit=3)
    shown = [(names[r["product_id"]], round(r["confidence"], 2)) for r in recs]
    print(label(cart), "->", shown or "sem regra aplicável")"""),
    ("md", """As métricas oficiais vêm de `ml/evaluate_apriori.py` (gravadas em `ml/artifacts/metrics.json`).
Recalculamos aqui a partir do artefato para conferência."""),
    ("code", """metrics = json.loads(config.METRICS_PATH.read_text(encoding="utf-8"))
ev = metrics["evaluation"]
pd.DataFrame({
    "métrica": ["Hit rate @3 (Apriori)", "Hit rate @3 (popularidade)", "Cobertura de carrinhos",
                "Cobertura de itens", "Precisão @3 (cobertos)"],
    "valor (%)": [ev["hit_rate_at_k_all_carts_pct"], ev["baseline_popularity_hit_rate_at_k_pct"],
                  ev["cart_coverage_pct"], ev["item_coverage_pct"], ev["precision_at_k_covered_pct"]],
})"""),
    ("code", """pd.DataFrame(ev["rule_quality"]["train"], index=["treino"]).T.join(
    pd.DataFrame(ev["rule_quality"]["test"], index=["teste"]).T).round(4)"""),
    ("code", """# Conferência: o notebook reproduz exatamente o artefato persistido.
import joblib
assert rules == joblib.load(config.RULES_PATH), "regras divergem do artefato"
print("Regras do notebook idênticas a ml/artifacts/rules.joblib")"""),
    ("md", """## 5. Conclusões e limitações

- As regras com maior lift recuperam as associações planejadas no simulador
  (ex.: Switch → capa/microSD, kit de PC → fonte), e mantêm confiança e lift semelhantes no teste,
  indicando que não há sobreajuste às transações de treino.
- O Apriori supera com folga a linha de base por popularidade no Hit rate @3.
- **Limitação principal:** os dados são simulados; o desempenho mede quão bem o algoritmo
  recupera padrões gerados pelo próprio simulador, não o comportamento de clientes reais.
- Itens raros (abaixo de 1% de suporte) nunca geram regras; nem toda combinação recebe recomendação."""),
]


def build() -> nbf.NotebookNode:
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.cells = [nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src) for kind, src in cells]
    return nb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    nb = build()
    if args.execute:
        from nbclient import NotebookClient
        NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(HERE)}}).execute()
    nbf.write(nb, OUT)
    print(f"Notebook gravado em {OUT} (executado={args.execute})")


if __name__ == "__main__":
    main()
