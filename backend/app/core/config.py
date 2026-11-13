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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    environment: str = "development"
    # SQLite local por padrão; em produção use a string do Supabase (postgresql+psycopg://...).
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'ipaj_local.db').as_posix()}"
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
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.environment == "production" and settings.jwt_secret.startswith("dev-only"):
        raise RuntimeError("JWT_SECRET deve ser definido em produção.")
    return settings
