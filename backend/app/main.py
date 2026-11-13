"""Aplicação FastAPI da IPAJ Gaming."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select, text

from app.api import laboratory, orders, products, recommendations, users
from app.core.config import get_settings
from app.database import models  # noqa: F401 - registra os modelos no metadata antes do ensure_schema
from app.database.connection import SessionLocal, engine, ensure_schema, tables_without_rls
from app.database.models import Product
from app.services.catalog import seed_products
from app.services.recommender import ArtifactsUnavailable, get_engine

log = logging.getLogger("ipaj")


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    log.info("Banco: %s", settings.safe_database_target)
    # Cria tabelas que faltarem e ativa RLS na mesma transação (ver connection.ensure_schema).
    ensure_schema(engine)
    if settings.seed_on_startup:
        with SessionLocal() as db:
            if db.scalar(select(func.count()).select_from(Product)) == 0:
                n = seed_products(db, settings.catalog_csv)
                log.info("Catálogo carregado: %s produtos", n)
    try:
        log.info("IPAJ CORE carregado: %s regras", len(get_engine().rules))
    except ArtifactsUnavailable as exc:
        log.error("%s", exc)
    yield


app = FastAPI(
    title="IPAJ Gaming API",
    description="E-commerce gamer com recomendações baseadas no algoritmo Apriori (IPAJ CORE).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_origin_regex=get_settings().cors_origin_regex or None,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(ArtifactsUnavailable)
async def artifacts_unavailable(_: Request, exc: ArtifactsUnavailable):
    return JSONResponse(status_code=503, content={"detail": "Motor de recomendação indisponível."})


@app.get("/health", tags=["Infra"], summary="Health check (Render)")
def health():
    status = {"status": "ok", "database": "ok", "recommender": "ok"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        # Nunca deveria acontecer após ensure_schema; se acontecer, a Data API pode expor dados.
        if tables_without_rls(engine):
            status.update(status="degraded", database="rls_disabled")
    except Exception:  # noqa: BLE001 - health check deve reportar, não quebrar
        status.update(status="degraded", database="unavailable")
    try:
        status["rules_loaded"] = len(get_engine().rules)
    except ArtifactsUnavailable:
        status.update(status="degraded", recommender="unavailable")
    return status


@app.get("/", include_in_schema=False)
def root():
    return {"name": "IPAJ Gaming API", "docs": "/docs", "health": "/health"}


for r in (products.router, recommendations.router, laboratory.router, orders.router, users.router):
    app.include_router(r)
