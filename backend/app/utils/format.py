"""Formatação de textos explicativos exibidos ao usuário (padrão pt-BR)."""


def pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def dec(value: float, places: int = 2) -> str:
    return f"{value:.{places}f}".replace(".", ",")


def explain(antecedent_names: list[str], consequent_name: str, confidence: float, lift: float) -> str:
    base = " + ".join(antecedent_names)
    return (
        f"{pct(confidence)} de quem levou {base} também levou {consequent_name} "
        f"(lift {dec(lift)}: {dec(lift, 1)}x a chance esperada ao acaso)."
    )
