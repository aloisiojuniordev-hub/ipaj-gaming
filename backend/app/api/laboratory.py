"""Laboratório IA: expõe métricas, regras e itemsets reais do Apriori."""
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas import ItemsetOut, ProductOut, RuleOut
from app.services.catalog import products_by_id
from app.services.recommender import get_engine, get_metrics

router = APIRouter(prefix="/api/laboratory", tags=["Laboratório IA"])


@router.get("/metrics", summary="Métricas reais de treino e avaliação (metrics.json)")
def metrics():
    return get_metrics()


@router.get("/rules", response_model=list[RuleOut], summary="Regras de associação")
def rules(
    sort_by: Literal["lift", "confidence", "support"] = "lift",
    limit: int = Query(default=20, ge=1, le=500),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0),
    min_lift: float = Query(default=0.0, ge=0.0),
    product_id: str | None = Query(default=None, description="Regras que envolvem este produto"),
    db: Session = Depends(get_db),
):
    selected = []
    for r in get_engine().top_rules(limit=len(get_engine().rules), sort_by=sort_by):
        if r["confidence"] < min_confidence or r["lift"] < min_lift:
            continue
        if product_id and product_id not in r["antecedents"] + r["consequents"]:
            continue
        selected.append(r)
        if len(selected) >= limit:
            break
    products = products_by_id(db, {i for r in selected for i in r["antecedents"] + r["consequents"]})

    def to_out(ids):
        return [ProductOut.model_validate(products[i]) for i in ids if i in products]

    return [
        RuleOut(antecedents=to_out(r["antecedents"]), consequents=to_out(r["consequents"]),
                support=r["support"], confidence=r["confidence"], lift=r["lift"], leverage=r["leverage"])
        for r in selected
    ]


@router.get("/itemsets", response_model=list[ItemsetOut], summary="Itemsets frequentes")
def itemsets(min_size: int = Query(default=1, ge=1, le=3), limit: int = Query(default=30, ge=1, le=300),
             db: Session = Depends(get_db)):
    chosen = sorted((i for i in get_engine().itemsets if len(i["items"]) >= min_size),
                    key=lambda i: (-i["support"], i["items"]))[:limit]
    products = products_by_id(db, {p for i in chosen for p in i["items"]})
    return [
        ItemsetOut(items=[ProductOut.model_validate(products[p]) for p in i["items"] if p in products],
                   support=i["support"])
        for i in chosen
    ]
