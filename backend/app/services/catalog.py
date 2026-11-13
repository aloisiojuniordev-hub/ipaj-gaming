"""Carga do catálogo (CSV -> banco) e utilitários de consulta."""
import csv
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Product


def seed_products(db: Session, csv_path: Path) -> int:
    """Insere/atualiza produtos a partir do CSV (idempotente). Retorna quantos foram gravados."""
    count = 0
    with Path(csv_path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            db.merge(Product(
                id=row["product_id"], name=row["name"], category=row["category"],
                price=Decimal(row["price"]), description=row["description"],
            ))
            count += 1
    db.commit()
    return count


def products_by_id(db: Session, ids: set[str]) -> dict[str, Product]:
    if not ids:
        return {}
    return {p.id: p for p in db.scalars(select(Product).where(Product.id.in_(ids)))}
