"""Fixtures: banco SQLite temporário, sem Supabase nem rede."""
import os
import tempfile
from pathlib import Path

# Configura o ambiente ANTES de importar a aplicação.
_tmp = Path(tempfile.mkdtemp(prefix="ipaj_test_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-not-used-anywhere-else-0123456789"
os.environ["SEED_ON_STARTUP"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:  # dispara o lifespan (cria tabelas e carrega catálogo)
        yield c


@pytest.fixture
def auth_headers(client):
    import uuid
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/users/register", json={"name": "Usuário Teste", "email": email, "password": "senha-segura-1"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
