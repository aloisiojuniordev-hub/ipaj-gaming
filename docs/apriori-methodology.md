# Metodologia — Apriori

## Conceitos

Para uma regra **A → B** sobre um conjunto de N transações:

| Medida | Definição | Leitura |
|---|---|---|
| Suporte(X) | nº de transações com X / N | Quão comum é o conjunto X |
| Suporte(A → B) | Suporte(A ∪ B) | Quão comum é a regra completa |
| Confiança | Suporte(A ∪ B) / Suporte(A) = P(B \| A) | Entre quem tem A, quantos têm B |
| Lift | Confiança / Suporte(B) | Quantas vezes B fica mais provável com A do que ao acaso (1 = independência) |
| Leverage | Suporte(A ∪ B) − Suporte(A)·Suporte(B) | Diferença absoluta para a independência |

O **Apriori** encontra os itemsets frequentes nível a nível (tamanho 1, 2, 3...). Ele usa a propriedade
antimonótona: se um conjunto é raro, todo superconjunto dele também é. Por isso candidatos com
subconjunto infrequente são descartados sem precisar ser contados.

## Implementação

Biblioteca: **mlxtend 0.23.4** (`mlxtend.frequent_patterns.apriori` e `association_rules`), com pandas 2.3.3.

Pipeline (`ml/train_apriori.py`):

1. Lê `data/processed/train.csv` (4.000 transações) e converte em listas de itens.
2. `TransactionEncoder` gera a matriz one-hot booleana (transações × 50 produtos).
3. `apriori(min_support=0.01, max_len=3, use_colnames=True)` gera os itemsets frequentes.
4. `association_rules(metric="confidence", min_threshold=0.30)` gera as regras.
5. Filtros adicionais: **lift ≥ 1,2** e **consequente com exatamente 1 item**.
6. Ordenação determinística (confiança ↓, lift ↓, antecedentes, consequentes).
7. Persistência em `ml/artifacts/` como listas de dicionários:
   - `rules.joblib`: antecedentes, consequentes, suporte, suporte do antecedente/consequente, confiança, lift, leverage;
   - `itemsets.joblib`: itens e suporte;
   - `metrics.json`: parâmetros, contagens, data do treino e (após `evaluate_apriori.py`) a avaliação.

## Parâmetros e justificativa

| Parâmetro | Valor | Justificativa |
|---|---|---|
| `min_support` | 0,01 (1% = 40 transações de treino) | Exige evidência mínima. Abaixo disso as regras ficam instáveis entre treino e teste. |
| `min_confidence` | 0,30 | A recomendação precisa acertar em pelo menos ~1 de cada 3 casos para fazer sentido no carrinho. |
| `min_lift` | 1,2 | Descarta associações que só refletem a popularidade do consequente. |
| `max_len` | 3 | Permite antecedentes de 2 itens (ex.: console + controle → jogo) com custo controlado. |
| Consequente | 1 item | Cada recomendação é um produto, com uma explicação direta. |

Os parâmetros ficam em `ml/config.py` (fonte única de verdade, usada também pelo notebook e pela avaliação).

## Resultado do treinamento

| Item | Valor |
|---|---|
| Itemsets frequentes | 248 (50 de tamanho 1, 105 de tamanho 2, 93 de tamanho 3) |
| Regras após filtros | 394 (138 com antecedente de 1 item, 256 com 2 itens) |
| Confiança | 0,303 a 1,000 |
| Lift | 2,25 a 18,82 |
| Suporte | 0,010 a 0,108 |

Todos os 50 produtos passam do suporte mínimo individualmente. Mesmo assim, só 37 aparecem como
consequente de alguma regra: os outros 13 nunca são recomendados (ver [avaliação](evaluation.md)).

Exemplos reais (maior lift):

| Se o carrinho tem | Recomenda | Suporte | Confiança | Lift |
|---|---|---|---|---|
| Braço Articulado + Cabo HDMI 2.1 | Monitor 24" 144 Hz | 1,58% | 96,9% | 18,82 |
| Headset HyperX Cloud II + Mousepad Extended RGB | Mouse Razer DeathAdder | 1,20% | 96,0% | 16,92 |
| Webcam Full HD + Microfone USB | Ring Light 10" | 2,65% | 84,1% | 16,26 |

Exemplos de recomendação para um único item (Top-3):

| Carrinho | Recomendações (confiança · lift) |
|---|---|
| PlayStation 5 Slim | DualSense Extra (71,7% · 7,22), EA FC 25 (61,8% · 7,44), Headset Pulse 3D (55,5% · 8,23) |
| Nintendo Switch OLED | microSD 128 GB (65,1% · 10,76), Mario Kart 8 (62,9% · 7,41), Capa Protetora (61,9% · 10,85) |
| Teclado Redragon Kumara | Mouse G203 (78,0% · 5,65), Mousepad Speed (75,4% · 6,05), Headset HyperX (41,7% · 4,66) |
| Placa de Vídeo RTX 4060 | Fonte 650 W (55,6% · 7,12), RAM 16 GB (46,0% · 7,84), SSD NVMe PC (33,3% · 5,51) |

## Motor de recomendação (IPAJ CORE)

`ml/recommendation_engine.py`:

```text
para cada regra (A → b):
    se A ⊆ carrinho e b ∉ carrinho:
        candidato[b] = regra de maior (confiança, lift) para b
ordenar candidatos por confiança ↓, lift ↓, id
retornar os primeiros `limit`
```

Antecedentes maiores tornam a recomendação mais específica. Com PS5 + DualSense no carrinho,
EA FC 25 sobe de 61,8% para 77,5% de confiança.

## Reprodução

```bash
python -m ml.train_apriori
python -m ml.evaluate_apriori
python notebooks/build_notebook.py --execute   # notebook com a análise completa
```
