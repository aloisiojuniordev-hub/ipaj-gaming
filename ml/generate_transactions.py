"""Gera 5.000 transações simuladas de compras gamer.

Modelo probabilístico em três camadas:
1. Cenário de compra (perfil do cliente), sorteado por peso.
2. Itens-semente do cenário, cada um com probabilidade própria.
3. Regras condicionais (se A está na cesta, B entra com probabilidade p),
   aplicadas em duas passadas para permitir encadeamento.
Soma-se ruído controlado: itens aleatórios e cestas totalmente aleatórias.

Uso: python -m ml.generate_transactions [--seed 42] [--n 5000]
"""
import argparse
import csv
import random
from datetime import datetime, timedelta

from ml.config import N_TRANSACTIONS, SEED, TRANSACTIONS_CSV

# Cenário -> (peso, [(item, probabilidade)])
SCENARIOS = {
    "playstation": (0.16, [("P001", 0.50), ("P014", 0.15), ("P018", 0.10), ("P004", 0.25),
                           ("P005", 0.15), ("P006", 0.15), ("P038", 0.05)]),
    "xbox": (0.12, [("P002", 0.50), ("P015", 0.15), ("P007", 0.30), ("P008", 0.20)]),
    "switch": (0.14, [("P003", 0.45), ("P009", 0.25), ("P010", 0.30), ("P011", 0.20), ("P016", 0.10)]),
    "pc_perifericos": (0.22, [("P021", 0.30), ("P022", 0.20), ("P023", 0.10), ("P024", 0.30),
                              ("P025", 0.15), ("P026", 0.10), ("P019", 0.10)]),
    "setup": (0.10, [("P029", 0.40), ("P030", 0.25), ("P032", 0.15), ("P033", 0.10)]),
    "streaming": (0.08, [("P041", 0.40), ("P042", 0.35), ("P044", 0.10), ("P045", 0.05)]),
    "pc_build": (0.08, [("P046", 0.35), ("P049", 0.30), ("P050", 0.30), ("P047", 0.30), ("P048", 0.30)]),
    "casual": (0.10, [("P012", 0.30), ("P013", 0.30), ("P017", 0.10), ("P020", 0.10)]),
}

# (antecedente, consequente, probabilidade) - intervalo usado: 0,15 a 0,65
CONDITIONAL_RULES = [
    ("P001", "P014", 0.55), ("P001", "P004", 0.45), ("P001", "P018", 0.40),
    ("P001", "P035", 0.30), ("P001", "P038", 0.20), ("P001", "P039", 0.20),
    ("P002", "P015", 0.50), ("P002", "P007", 0.50), ("P002", "P038", 0.20),
    ("P003", "P037", 0.65), ("P003", "P036", 0.60), ("P003", "P016", 0.30),
    ("P003", "P010", 0.50), ("P003", "P040", 0.25),
    ("P021", "P024", 0.65), ("P022", "P024", 0.55), ("P023", "P025", 0.50),
    ("P024", "P027", 0.60), ("P025", "P028", 0.55), ("P021", "P027", 0.40),
    ("P024", "P019", 0.30),
    ("P029", "P038", 0.45), ("P030", "P031", 0.40), ("P029", "P031", 0.25),
    ("P032", "P034", 0.50), ("P033", "P034", 0.45),
    ("P041", "P042", 0.60), ("P042", "P043", 0.35), ("P041", "P043", 0.45), ("P044", "P042", 0.50),
    ("P046", "P050", 0.55), ("P049", "P050", 0.60), ("P046", "P047", 0.50), ("P047", "P048", 0.40),
    ("P012", "P046", 0.15), ("P013", "P046", 0.20),
    ("P004", "P014", 0.30), ("P009", "P016", 0.25),
]

NOISE_ITEM_PROB = 0.25      # chance de cada um de até 2 itens aleatórios
RANDOM_BASKET_PROB = 0.05   # cestas totalmente aleatórias


def load_product_ids() -> list[str]:
    from ml.generate_catalog import PRODUCTS
    return [p[0] for p in PRODUCTS]


def generate(n: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    ids = load_product_ids()
    names = list(SCENARIOS)
    weights = [SCENARIOS[s][0] for s in names]
    start = datetime(2025, 1, 1)
    rows = []

    for tid in range(1, n + 1):
        basket: set[str] = set()
        scenario = ""
        if rng.random() < RANDOM_BASKET_PROB:
            scenario = "aleatorio"
            basket.update(rng.sample(ids, rng.randint(1, 4)))
        else:
            scenario = rng.choices(names, weights=weights, k=1)[0]
            for item, p in SCENARIOS[scenario][1]:
                if rng.random() < p:
                    basket.add(item)
            for _ in range(2):  # duas passadas: permite encadeamento
                for ant, cons, p in CONDITIONAL_RULES:
                    if ant in basket and cons not in basket and rng.random() < p:
                        basket.add(cons)
            for _ in range(2):
                if rng.random() < NOISE_ITEM_PROB:
                    basket.add(rng.choice(ids))
        if not basket:  # nunca gerar cesta vazia
            basket.add(rng.choice(ids))

        when = start + timedelta(minutes=rng.randint(0, 365 * 24 * 60 - 1))
        rows.append({
            "transaction_id": f"T{tid:05d}",
            "timestamp": when.strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": scenario,
            "n_items": len(basket),
            "items": ";".join(sorted(basket)),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--n", type=int, default=N_TRANSACTIONS)
    args = parser.parse_args()

    rows = generate(args.n, args.seed)
    TRANSACTIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TRANSACTIONS_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    avg = sum(r["n_items"] for r in rows) / len(rows)
    print(f"{len(rows)} transações (seed={args.seed}, média {avg:.2f} itens/cesta) em {TRANSACTIONS_CSV}")


if __name__ == "__main__":
    main()
