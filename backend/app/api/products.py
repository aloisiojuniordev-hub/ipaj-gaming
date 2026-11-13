from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Product
from app.schemas import ProductOut

router = APIRouter(prefix="/api/products", tags=["Produtos"])


@router.get("", response_model=list[ProductOut], summary="Lista o catálogo com filtros")
def list_products(
    category: str | None = None,
    q: str | None = Query(default=None, max_length=80, description="Busca no nome"),
    sort: Literal["name", "price_asc", "price_desc"] = "name",
    db: Session = Depends(get_db),
):
    stmt = select(Product)
    if category:
        stmt = stmt.where(Product.category == category)
    if q:
        stmt = stmt.where(func.lower(Product.name).contains(q.lower()))
    order = {"name": Product.name, "price_asc": Product.price, "price_desc": Product.price.desc()}[sort]
    return db.scalars(stmt.order_by(order)).all()


@router.get("/categories", response_model=list[str], summary="Categorias disponíveis")
def categories(db: Session = Depends(get_db)):
    return db.scalars(select(Product.category).distinct().order_by(Product.category)).all()


@router.get("/{product_id}", response_model=ProductOut, summary="Detalhes de um produto")
def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(404, "Produto não encontrado.")
    return product
