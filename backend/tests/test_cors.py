"""CORS: o frontend no Netlify precisa chamar a API no Render; outras origens não."""
import pytest

from app.core.config import Settings, validate_settings

PREFLIGHT = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}


def _preflight(client, origin):
    return client.options("/api/recommendations", headers={"Origin": origin, **PREFLIGHT})


@pytest.mark.parametrize("origin", [
    "https://ipaj-gaming.netlify.app",                    # produção (configurada com barra final)
    "https://deploy-preview-12--ipaj-gaming.netlify.app",  # Deploy Preview (regex)
    "https://main--ipaj-gaming.netlify.app",               # branch deploy (regex)
    "http://localhost:5173",                               # desenvolvimento
])
def test_allowed_origins(client, origin):
    r = _preflight(client, origin)
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == origin
    # Requisição real do IPAJ CORE vinda do Netlify recebe o header e regras reais.
    real = client.post("/api/recommendations", json={"cart": ["P001"]}, headers={"Origin": origin})
    assert real.headers["access-control-allow-origin"] == origin
    assert real.json()["recommendations"]


@pytest.mark.parametrize("origin", [
    "https://evil.netlify.app",
    "https://ipaj-gaming.netlify.app.evil.com",   # regex é ancorada: sufixo não engana
    "https://evil.com/?x=ipaj-gaming.netlify.app",
    "http://ipaj-gaming.netlify.app",             # http não é aceito
])
def test_blocked_origins(client, origin):
    r = _preflight(client, origin)
    assert r.status_code == 400
    assert "access-control-allow-origin" not in r.headers


def test_trailing_slash_is_normalized():
    s = Settings(_env_file=None, cors_origins=" https://a.netlify.app/ , http://localhost:5173 ")
    assert s.cors_origin_list == ["https://a.netlify.app", "http://localhost:5173"]


def _prod(**kw):
    base = {"environment": "production", "jwt_secret": "x" * 48, "database_sslmode": "require",
            "database_url": "postgresql://u:p@host:5432/postgres", "cors_origins": "https://a.netlify.app",
            "cors_origin_regex": None}
    return Settings(_env_file=None, **{**base, **kw})


def test_production_rejects_wildcard_and_bad_regex():
    validate_settings(_prod())
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_settings(_prod(cors_origins="*"))
    with pytest.raises(RuntimeError, match="CORS_ORIGIN_REGEX"):
        validate_settings(_prod(cors_origin_regex="https://(unclosed"))
