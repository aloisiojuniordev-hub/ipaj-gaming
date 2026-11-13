"""Caminhos e parâmetros centrais do pipeline. Fonte única de verdade."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CATALOG_CSV = ROOT / "data" / "catalog" / "products.csv"
TRANSACTIONS_CSV = ROOT / "data" / "raw" / "transactions.csv"
TRAIN_CSV = ROOT / "data" / "processed" / "train.csv"
TEST_CSV = ROOT / "data" / "processed" / "test.csv"

ARTIFACTS_DIR = ROOT / "ml" / "artifacts"
RULES_PATH = ARTIFACTS_DIR / "rules.joblib"
ITEMSETS_PATH = ARTIFACTS_DIR / "itemsets.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"

# Reprodutibilidade
SEED = 42
N_TRANSACTIONS = 5000
TEST_SIZE = 0.20

# Parâmetros do Apriori
MIN_SUPPORT = 0.01
MIN_CONFIDENCE = 0.30
MIN_LIFT = 1.2
MAX_LEN = 3

# Avaliação
TOP_K = 3
