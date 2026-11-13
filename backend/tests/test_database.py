"""Testes da configuração de banco e de segurança (SQLite sempre; PostgreSQL quando disponível)."""
import os

import pytest
from sqlalchemy import create_engine, inspect, text

from app.core.config import REPO_ROOT, Settings, validate_settings
from app.database.connection import Base, engine_options, ensure_schema, make_engine, tables_without_rls

PG_URL = os.environ.get("TEST_POSTGRES_URL")  # definido apenas no job PostgreSQL da CI
requires_pg = pytest.mark.skipif(not PG_URL, reason="TEST_POSTGRES_URL não definido")
APP_TABLES = {"products", "users", "orders", "order_items"}


def _body(path) -> str:
    """SQL sem as linhas de comentário iniciais (cabeçalho)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    while lines and (lines[0].startswith("--") or not lines[0].strip()):
        lines.pop(0)
    return "\n".join(lines).strip()


# ---------- Validação da configuração de produção ----------

def _prod(**kw) -> Settings:
    # Valores explícitos: não herdar DATABASE_SSLMODE etc. do ambiente (o job PostgreSQL da CI define disable).
    base = {"environment": "production", "jwt_secret": "x" * 48, "database_sslmode": "require",
            "database_url": "postgresql://u:p@host.pooler.supabase.com:5432/postgres"}
    return Settings(_env_file=None, **{**base, **kw})


def test_production_accepts_valid_postgres_config():
    s = validate_settings(_prod())
    assert s.is_postgres and s.database_sslmode == "require"
    assert s.sqlalchemy_url.startswith("postgresql+psycopg://")


def test_production_rejects_sqlite_fallback():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_settings(_prod(database_url="sqlite:///x.db"))


def test_production_rejects_insecure_sslmode():
    for mode in ("disable", "allow", "prefer"):
        with pytest.raises(RuntimeError, match="DATABASE_SSLMODE"):
            validate_settings(_prod(database_sslmode=mode))


def test_production_rejects_weak_jwt_secret():
    for secret in ("dev-only-insecure-secret-change-me", "curto"):
        with pytest.raises(RuntimeError, match="JWT_SECRET"):
            validate_settings(_prod(jwt_secret=secret))


def test_non_production_is_permissive():
    s = validate_settings(Settings(_env_file=None, environment="development", database_url="sqlite:///x.db"))
    assert not s.is_postgres


def test_postgres_prefix_normalization_and_safe_target():
    s = _prod(database_url="postgres://user:s3cr@host:5432/db?sslmode=require")
    assert s.sqlalchemy_url.startswith("postgresql+psycopg://user:s3cr@host")
    assert s.safe_database_target == "host:5432/db"
    assert "s3cr" not in s.safe_database_target


def test_postgres_engine_forces_ssl_and_disables_prepared_statements():
    s = _prod(database_url="postgresql://u:p@host/db?sslmode=disable")  # URL tenta desligar SSL
    opts = engine_options(s)
    assert opts["connect_args"] == {"sslmode": "require", "prepare_threshold": None}
    assert opts["pool_pre_ping"] is True
    # O SQLAlchemy dá precedência a connect_args sobre a query string da URL.
    eng = make_engine(s)  # create_engine não abre conexão
    url_args = eng.dialect.create_connect_args(eng.url)[1]
    assert url_args.get("sslmode") == "disable"  # o que viria da URL...
    assert {**url_args, **opts["connect_args"]}["sslmode"] == "require"  # ...é sobrescrito
    assert eng.dialect.name == "postgresql"
    eng.dispose()


def test_sqlite_engine_options():
    s = Settings(_env_file=None, environment="development", database_url="sqlite:///x.db")
    assert engine_options(s) == {"connect_args": {"check_same_thread": False}}


# ---------- Migrações ----------

def test_migration_001_is_self_contained_and_matches_schema():
    schema = REPO_ROOT / "database" / "schema.sql"
    mig = REPO_ROOT / "database" / "migrations" / "001_initial_schema.sql"
    assert "\\ir" not in _body(mig)
    assert _body(mig) == _body(schema)


def test_schema_sql_enables_rls_on_all_app_tables():
    sql = _body(REPO_ROOT / "database" / "schema.sql")
    for t in APP_TABLES:
        assert f"CREATE TABLE IF NOT EXISTS {t} " in sql
        assert f"ALTER TABLE {t}" in sql and "ENABLE ROW LEVEL SECURITY" in sql
    assert {t.name for t in Base.metadata.sorted_tables} == APP_TABLES


def test_ensure_schema_on_sqlite_is_idempotent(tmp_path):
    eng = create_engine(f"sqlite:///{(tmp_path / 'x.db').as_posix()}")
    ensure_schema(eng)
    ensure_schema(eng)
    assert APP_TABLES <= set(inspect(eng).get_table_names())
    assert tables_without_rls(eng) == []
    eng.dispose()


# ---------- PostgreSQL real (CI) ----------

@pytest.fixture
def pg_engine():
    eng = make_engine(Settings(_env_file=None, database_url=PG_URL, database_sslmode="disable"))
    with eng.begin() as conn:  # banco descartável da CI: começa limpo
        conn.execute(text("DROP TABLE IF EXISTS order_items, orders, users, products CASCADE"))
    yield eng
    eng.dispose()


@requires_pg
def test_pg_ensure_schema_enables_rls_atomically(pg_engine):
    ensure_schema(pg_engine)
    ensure_schema(pg_engine)  # idempotente
    assert APP_TABLES <= set(inspect(pg_engine).get_table_names())
    assert tables_without_rls(pg_engine) == []


@requires_pg
def test_pg_orm_tables_have_same_db_defaults_as_schema_sql(pg_engine):
    """Tabelas criadas pelo backend aceitam INSERT direto, como as do schema.sql."""
    ensure_schema(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("INSERT INTO products (id, name, category, price) VALUES ('T1', 'n', 'c', 1)"))
        uid = conn.execute(text("INSERT INTO users (name, email, password_hash) "
                                "VALUES ('a', 'd@example.com', 'h') RETURNING id")).scalar()
        oid = conn.execute(text("INSERT INTO orders (user_id, total) VALUES (:u, 1) RETURNING id"), {"u": uid}).scalar()
        conn.execute(text("INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
                          "VALUES (:o, 'T1', 1, 1)"), {"o": oid})
        row = conn.execute(text("SELECT o.status, o.created_at IS NOT NULL, i.from_recommendation, p.description "
                                "FROM orders o JOIN order_items i ON i.order_id = o.id "
                                "JOIN products p ON p.id = i.product_id")).one()
    assert tuple(row) == ("demo_confirmed", True, False, "")


@requires_pg
def test_pg_schema_sql_and_orm_are_compatible(pg_engine):
    """schema.sql aplicado depois do ORM (e vice-versa) não falha nem duplica nada."""
    sql = (REPO_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    ensure_schema(pg_engine)
    raw = pg_engine.raw_connection()
    try:
        cur = raw.cursor()
        cur.execute(sql)  # sem parâmetros: múltiplos comandos permitidos
        cur.execute(sql)  # idempotente
        raw.commit()
    finally:
        raw.close()
    ensure_schema(pg_engine)
    assert tables_without_rls(pg_engine) == []


@requires_pg
def test_pg_anon_role_cannot_read_users(pg_engine):
    """Simula a Data API do Supabase: uma role sem privilégio de dono não enxerga linhas."""
    ensure_schema(pg_engine)
    with pg_engine.begin() as conn:
        conn.execute(text("INSERT INTO users (name, email, password_hash) VALUES ('a', 'a@example.com', 'h')"))
        conn.execute(text("DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') "
                          "THEN CREATE ROLE anon NOLOGIN; END IF; END $$"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO anon"))
        conn.execute(text("GRANT SELECT ON users TO anon"))  # o Supabase concede isso por padrão
    with pg_engine.connect() as conn:
        conn.execute(text("SET ROLE anon"))
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 0  # RLS bloqueia
        conn.execute(text("RESET ROLE"))
        assert conn.execute(text("SELECT count(*) FROM users")).scalar() == 1  # dono enxerga
