from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Product
from app.schemas import ProductOut, RecommendationOut, RecommendationRequest, RecommendationResponse
from app.services.catalog import products_by_id
from app.services.recommender import get_engine
from app.utils.format import explain

router = APIRouter(prefix="/api/recommendations", tags=["IPAJ CORE"])


def _build(db: Session, cart: list[str], limit: int) -> RecommendationResponse:
    cart = list(dict.fromkeys(cart))  # remove duplicatas preservando ordem
    known = products_by_id(db, set(cart))
    unknown = [pid for pid in cart if pid not in known]
    if unknown:
        raise HTTPException(422, f"Produtos inexistentes no carrinho: {', '.join(unknown)}")

    raw = get_engine().recommend(cart, limit=limit)
    products = products_by_id(db, {r["product_id"] for r in raw} | {i for r in raw for i in r["because"]})
    recs = []
    for r in raw:
        product = products.get(r["product_id"])
        if product is None:  # regra aponta para item fora do catálogo atual
            continue
        because = [products[i] for i in r["because"] if i in products]
        recs.append(RecommendationOut(
            product=ProductOut.model_validate(product),
            confidence=r["confidence"], lift=r["lift"], support=r["support"],
            because=[ProductOut.model_validate(p) for p in because],
            explanation=explain([p.name for p in because], product.name, r["confidence"], r["lift"]),
        ))
    message = None
    if not cart:
        message = "Adicione produtos ao carrinho para ativar o IPAJ CORE."
    elif not recs:
        message = "Nenhuma regra de associação cobre esta combinação de produtos."
    return RecommendationResponse(cart=cart, recommendations=recs, message=message)


@router.post("", response_model=RecommendationResponse, summary="Recomendações para o carrinho")
def recommend_for_cart(body: RecommendationRequest, db: Session = Depends(get_db)):
    return _build(db, body.cart, body.limit)


@router.get("/product/{product_id}", response_model=RecommendationResponse,
            summary="Comprados juntos com um produto")
def recommend_for_product(product_id: str, limit: int = Query(default=4, ge=1, le=10),
                          db: Session = Depends(get_db)):
    if db.get(Product, product_id) is None:
        raise HTTPException(404, "Produto não encontrado.")
    return _build(db, [product_id], limit)
