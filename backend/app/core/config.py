"""Configuração do backend via variáveis de ambiente (ver backend/.env.example)."""
import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

# O motor de recomendação vive em ml/ (raiz do monorepo); garante o import.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Modos do libpq que garantem conexão criptografada.
SECURE_SSLMODES = {"require", "verify-ca", "verify-full"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    environment: str = "development"
    # SQLite local por padrão; em produção é OBRIGATÓRIA a string PostgreSQL do Supabase.
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'ipaj_local.db').as_posix()}"
    # SSL da conexão PostgreSQL. "require" por padrão; "disable" só para Postgres local/CI.
    database_sslmode: str = "require"
    # Obrigatório em produção. O valor padrão serve apenas para desenvolvimento local.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 120
    cors_origins: str = "http://localhost:5173"
    artifacts_dir: Path = REPO_ROOT / "ml" / "artifacts"
    catalog_csv: Path = REPO_ROOT / "data" / "catalog" / "products.csv"
    seed_on_startup: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        # Supabase/Render fornecem "postgres://" ou "postgresql://"; usamos o driver psycopg 3.
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def is_postgres(self) -> bool:
        return self.sqlalchemy_url.startswith("postgresql+psycopg://")

    @property
    def safe_database_target(self) -> str:
        """Host/banco para logs, sem usuário nem senha."""
        return self.sqlalchemy_url.split("@")[-1].split("?")[0] if self.is_postgres else "SQLite local"


def validate_settings(s: Settings) -> Settings:
    """Recusa configurações inseguras em produção (falha na inicialização, não em silêncio)."""
    if s.environment != "production":
        return s
    problems = []
    if s.jwt_secret.startswith("dev-only") or len(s.jwt_secret) < 32:
        problems.append("JWT_SECRET ausente ou curto demais (mínimo 32 caracteres).")
    if not s.is_postgres:
        problems.append("DATABASE_URL deve ser uma string PostgreSQL (Supabase) em produção; "
                        "o fallback para SQLite perderia dados a cada deploy.")
    if s.is_postgres and s.database_sslmode not in SECURE_SSLMODES:
        problems.append(f"DATABASE_SSLMODE deve ser um de {sorted(SECURE_SSLMODES)} em produção.")
    if problems:
        raise RuntimeError("Configuração de produção inválida: " + " ".join(problems))
    return s


@lru_cache
def get_settings() -> Settings:
    return validate_settings(Settings())
