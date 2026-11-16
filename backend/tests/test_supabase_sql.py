"""Migrações 001-004 num PostgreSQL real, com um 'auth' mínimo que imita o Supabase.

Simula o que o navegador pode fazer com a chave pública (roles anon/authenticated):
comprar via create_order, ler o catálogo e ler apenas os próprios pedidos.
Roda só no job PostgreSQL da CI (TEST_POSTGRES_URL).
"""
import json
import os
import uuid
from contextlib import contextmanager

import pytest
from sqlalchemy import text

from app.core.config import REPO_ROOT, Settings
from app.database.connection import make_engine

PG_URL = os.environ.get("TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not PG_URL, reason="TEST_POSTGRES_URL não definido")
DB = REPO_ROOT / "database"

AUTH_STUB = """
CREATE SCHEMA IF NOT EXISTS auth;
CREATE TABLE IF NOT EXISTS auth.users (id uuid PRIMARY KEY);
CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS
  $$ SELECT nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN CREATE ROLE anon NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN CREATE ROLE authenticated NOLOGIN; END IF;
END $$;
GRANT USAGE ON SCHEMA public, auth TO anon, authenticated;
GRANT EXECUTE ON FUNCTION auth.uid() TO anon, authenticated;
"""


def _run_sql(engine, sql: str) -> None:
    raw = engine.raw_connection()
    try:
        raw.cursor().execute(sql)
        raw.commit()
    finally:
        raw.close()


@pytest.fixture(scope="module")
def eng():
    engine = make_engine(Settings(_env_file=None, database_url=PG_URL, database_sslmode="disable"))
    _run_sql(engine, "DROP TABLE IF EXISTS order_items, orders, users, products CASCADE;"
                     "DROP FUNCTION IF EXISTS public.create_order(jsonb, text);")
    _run_sql(engine, AUTH_STUB)
    for f in ("schema.sql", "migrations/002_revoke_public_roles.sql",
              "migrations/003_frontend_supabase_access.sql", "migrations/004_seed_products.sql"):
        sql = (DB / f).read_text(encoding="utf-8")
        _run_sql(engine, sql)
        _run_sql(engine, sql)  # idempotente: rodar duas vezes não falha
    yield engine
    engine.dispose()


@contextmanager
def _as(eng, role: str, sub: str | None = None):
    """Conexão agindo como a role do Supabase. Restaura a sessão antes de devolver ao pool."""
    conn = eng.connect()
    try:
        conn.execute(text("SELECT set_config('request.jwt.claim.sub', :s, false)"), {"s": sub or ""})
        conn.execute(text(f"SET ROLE {role}"))
        yield conn
    finally:
        conn.rollback()
        conn.execute(text("RESET ROLE"))
        conn.execute(text("SELECT set_config('request.jwt.claim.sub', '', false)"))
        conn.commit()
        conn.close()


def _order(conn, items, guest=None) -> dict:
    out = conn.execute(text("SELECT public.create_order(CAST(:i AS jsonb), :g)"),
                       {"i": json.dumps(items), "g": guest}).scalar()
    return out if isinstance(out, dict) else json.loads(out)


def _new_user(eng) -> str:
    uid = str(uuid.uuid4())
    with eng.begin() as c:
        c.execute(text("INSERT INTO auth.users (id) VALUES (CAST(:u AS uuid))"), {"u": uid})
    return uid


def test_catalog_is_seeded_and_publicly_readable(eng):
    with _as(eng, "anon") as c:
        assert c.execute(text("SELECT count(*) FROM products")).scalar() == 50
        assert str(c.execute(text("SELECT price FROM products WHERE id = 'P024'")).scalar()) == "119.00"


def test_guest_order_uses_database_prices(eng):
    with _as(eng, "anon") as c:
        o = _order(c, [{"product_id": "P024", "quantity": 2}, {"product_id": "P024", "quantity": 1}], "Visitante")
        c.commit()
    assert o["is_guest"] is True
    assert float(o["total"]) == 357.0  # 3 x 119,00, preço do banco
    assert [(i["product_id"], i["quantity"]) for i in o["items"]] == [("P024", 3)]


def test_logged_user_sees_only_own_orders(eng):
    alice, bob = _new_user(eng), _new_user(eng)
    with _as(eng, "authenticated", alice) as c:
        o = _order(c, [{"product_id": "P001", "quantity": 1},
                       {"product_id": "P014", "quantity": 1, "from_recommendation": True}])
        c.commit()
        assert o["is_guest"] is False
        rows = c.execute(text("SELECT id FROM orders")).scalars().all()
        assert rows == [o["id"]]
        flags = dict(c.execute(text("SELECT product_id, from_recommendation FROM order_items")).all())
        assert flags == {"P001": False, "P014": True}
    with _as(eng, "authenticated", bob) as c:
        assert c.execute(text("SELECT count(*) FROM orders")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM order_items")).scalar() == 0


@pytest.mark.parametrize("sql", [
    "SELECT * FROM orders", "SELECT * FROM order_items", "SELECT * FROM users",
    "INSERT INTO products (id, name, category, price) VALUES ('X1', 'x', 'x', 0)",
    "UPDATE products SET price = 0", "INSERT INTO orders (total) VALUES (0)",
])
def test_anon_cannot_touch_protected_data(eng, sql):
    with _as(eng, "anon") as c, pytest.raises(Exception, match="permission denied"):
        c.execute(text(sql))


@pytest.mark.parametrize("sql", [
    "INSERT INTO orders (total, auth_user_id) VALUES (0, NULL)", "UPDATE orders SET total = 0",
    "DELETE FROM order_items", "UPDATE products SET price = 1", "SELECT * FROM users",
])
def test_authenticated_cannot_write_directly(eng, sql):
    with _as(eng, "authenticated", _new_user(eng)) as c, pytest.raises(Exception, match="permission denied"):
        c.execute(text(sql))


@pytest.mark.parametrize("items,msg", [
    ([], "1 a 50 itens"),
    ([{"product_id": "P001", "quantity": 0}], "1 a 20"),
    ([{"product_id": "P001", "quantity": 21}], "1 a 20"),
    ([{"product_id": "P001", "quantity": 1.5}], "1 a 20"),
    ([{"product_id": "P001", "quantity": "2"}], "inválido"),
    ([{"product_id": "P001", "quantity": 1, "unit_price": 0.01, "from_recommendation": "sim"}], "inválido"),
    ([{"product_id": "NAO_EXISTE", "quantity": 1}], "inexistentes"),
])
def test_create_order_validates_input(eng, items, msg):
    with _as(eng, "anon") as c, pytest.raises(Exception, match=msg):
        _order(c, items)


def test_client_cannot_set_price(eng):
    with _as(eng, "anon") as c:
        o = _order(c, [{"product_id": "P001", "quantity": 1, "unit_price": 1}])
        c.commit()
    assert float(o["total"]) == 4499.0
