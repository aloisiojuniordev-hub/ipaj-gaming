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
from app.database import models  # noqa: E402, F401 - registra os modelos no metadata
from app.database.connection import SessionLocal, ensure_schema, tables_without_rls  # noqa: E402
from app.services.catalog import seed_products  # noqa: E402


def main() -> None:
    settings = get_settings()
    ensure_schema()  # cria o que faltar + RLS, na mesma transação
    with SessionLocal() as db:
        n = seed_products(db, settings.catalog_csv)
    missing = tables_without_rls()
    print(f"{n} produtos carregados em {settings.safe_database_target}")  # sem credenciais
    if missing:
        raise SystemExit(f"ATENÇÃO: tabelas sem RLS: {', '.join(missing)}")


if __name__ == "__main__":
    main()
