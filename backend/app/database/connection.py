"""Engine e sessão SQLAlchemy (PostgreSQL/Supabase em produção, SQLite local/testes)."""
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings


class Base(DeclarativeBase):
    pass


def engine_options(settings: Settings) -> dict:
    """Argumentos de create_engine para o banco configurado."""
    if not settings.is_postgres:
        return {"connect_args": {"check_same_thread": False}}
    return {
        # pool_pre_ping evita conexões mortas (pooler do Supabase / hibernação do Render).
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 5,
        "connect_args": {
            # connect_args prevalece sobre o sslmode da URL: a criptografia não depende
            # de quem copiou a string de conexão.
            "sslmode": settings.database_sslmode,
            # Sem prepared statements no servidor: compatível com o Transaction pooler
            # (porta 6543) do Supabase, que não os suporta. Inofensivo no Session pooler.
            "prepare_threshold": None,
        },
    }


def make_engine(settings: Settings) -> Engine:
    return create_engine(settings.sqlalchemy_url, **engine_options(settings))


engine = make_engine(get_settings())
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def ensure_schema(bind: Engine = engine) -> None:
    """Cria as tabelas que faltarem e, no PostgreSQL, ativa RLS em todas elas.

    Tudo ocorre em UMA transação: como DDL é transacional no PostgreSQL, nenhuma tabela
    fica visível sem RLS, nem por um instante, para a Data API pública do Supabase
    (roles anon/authenticated). O backend conecta como dono das tabelas e não é afetado.
    Idempotente: pode rodar em toda inicialização, antes ou depois de database/schema.sql.
    """
    with bind.begin() as conn:
        Base.metadata.create_all(conn)
        if conn.dialect.name == "postgresql":
            for table in Base.metadata.sorted_tables:
                conn.execute(text(f'ALTER TABLE "{table.name}" ENABLE ROW LEVEL SECURITY'))


def tables_without_rls(bind: Engine = engine) -> list[str]:
    """Tabelas do app sem RLS (PostgreSQL). Lista vazia = protegido. SQLite: sempre vazia."""
    if bind.dialect.name != "postgresql":
        return []
    names = [t.name for t in Base.metadata.sorted_tables]
    with bind.connect() as conn:
        rows = conn.execute(
            text("SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                 "WHERE n.nspname = current_schema() AND c.relname = ANY(:names) AND NOT c.relrowsecurity"),
            {"names": names},
        ).scalars().all()
    return sorted(rows)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
