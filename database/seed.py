"""Carga inicial do catálogo (data/catalog/products.csv) no banco configurado.

Usa DATABASE_URL (Supabase) ou, se ausente, o SQLite local do backend.
Idempotente: produtos existentes são atualizados.

Uso (na raiz do repositório):
    python database/seed.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from app.database.connection import Base, SessionLocal, engine  # noqa: E402
from app.services.catalog import seed_products  # noqa: E402


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        n = seed_products(db, settings.catalog_csv)
    target = settings.sqlalchemy_url.split("@")[-1]  # não imprime credenciais
    print(f"{n} produtos carregados em {target}")


if __name__ == "__main__":
    main()
