"""Pré-processamento: valida transações, remove duplicatas de item e divide 80/20.

Uso: python -m ml.preprocess
"""
import pandas as pd

from ml.config import SEED, TEST_CSV, TEST_SIZE, TRAIN_CSV, TRANSACTIONS_CSV


def load_baskets(path=TRANSACTIONS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    df["items"] = df["items"].fillna("")
    return df[df["items"] != ""].reset_index(drop=True)


def split(df: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = SEED):
    """Divisão aleatória reprodutível (sem vazamento entre treino e teste)."""
    shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    n_test = int(round(len(shuffled) * test_size))
    return shuffled.iloc[n_test:].reset_index(drop=True), shuffled.iloc[:n_test].reset_index(drop=True)


def to_baskets(df: pd.DataFrame) -> list[list[str]]:
    return [sorted(set(s.split(";"))) for s in df["items"]]


def main() -> None:
    df = load_baskets()
    train, test = split(df)
    TRAIN_CSV.parent.mkdir(parents=True, exist_ok=True)
    train.to_csv(TRAIN_CSV, index=False, lineterminator="\n")
    test.to_csv(TEST_CSV, index=False, lineterminator="\n")
    print(f"Total={len(df)} | treino={len(train)} | teste={len(test)}")


if __name__ == "__main__":
    main()
