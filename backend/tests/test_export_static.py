"""Os dados estáticos do frontend devem ser EXATAMENTE os artefatos reais do Apriori."""
import importlib.util
import json
import re

import joblib

from app.core.config import REPO_ROOT

_spec = importlib.util.spec_from_file_location("export_static", REPO_ROOT / "scripts" / "export_static.py")
export_static = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(export_static)


def test_versioned_static_files_are_up_to_date():
    stale = [str(p.relative_to(REPO_ROOT)) for p, content in export_static.build_outputs().items()
             if not p.exists() or p.read_text(encoding="utf-8") != content]
    assert not stale, f"Rode 'python scripts/export_static.py'. Desatualizados: {stale}"


def test_frontend_rules_are_the_real_apriori_artifact():
    rules_json = json.loads((REPO_ROOT / "frontend" / "src" / "data" / "rules.json").read_text(encoding="utf-8"))
    assert rules_json == joblib.load(REPO_ROOT / "ml" / "artifacts" / "rules.joblib")
    assert len(rules_json) == 394


# Comandos que apagam algo. "ON DELETE SET NULL" (regra de FK) NÃO é destrutivo e não casa aqui.
DESTRUCTIVE = re.compile(r"\bDROP\s+\w+|\bDELETE\s+FROM\b|\bTRUNCATE\b|\bALTER\s+TABLE\s+\w+\s+DROP\b", re.I)


def _sql_body(name: str) -> str:
    sql = (REPO_ROOT / "database" / "migrations" / name).read_text(encoding="utf-8")
    return "\n".join(line for line in sql.splitlines() if not line.lstrip().startswith("--"))


def test_seed_sql_has_whole_catalog_and_is_non_destructive():
    body = _sql_body("004_seed_products.sql")
    assert body.count("('P0") == 50
    assert "ON CONFLICT (id) DO UPDATE" in body
    assert not DESTRUCTIVE.search(body)


def test_migration_003_is_non_destructive():
    body = _sql_body("003_frontend_supabase_access.sql")
    assert not DESTRUCTIVE.search(body)
    assert "SECURITY DEFINER" in body and "SET search_path = ''" in body


def test_destructive_detector_is_not_fooled():
    assert DESTRUCTIVE.search("DROP TABLE x") and DESTRUCTIVE.search("delete from orders")
    assert not DESTRUCTIVE.search("REFERENCES auth.users (id) ON DELETE SET NULL")
