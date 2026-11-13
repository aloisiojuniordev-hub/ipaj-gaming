# Dataset

> **Os dados são simulados.** Não há compras reais. O simulador foi desenhado para conter padrões
> de associação plausíveis e ruído controlado, de modo que o Apriori tenha algo real a descobrir
> e que seja possível verificar se ele recupera o que foi planejado.

## Arquivos

| Arquivo | Conteúdo | Gerado por |
|---|---|---|
| `data/catalog/products.csv` | 50 produtos: `product_id, name, category, price, description` | `ml/generate_catalog.py` |
| `data/raw/transactions.csv` | 5.000 transações: `transaction_id, timestamp, scenario, n_items, items` | `ml/generate_transactions.py` |
| `data/processed/train.csv` | 4.000 transações (80%) | `ml/preprocess.py` |
| `data/processed/test.csv` | 1.000 transações (20%) | `ml/preprocess.py` |

`items` é a lista de IDs separados por `;`, ordenados e sem repetição (ex.: `P001;P004;P014`).
`scenario` é o perfil sorteado. Fica no CSV para auditoria e **não é usado** pelo Apriori.

## Catálogo

12 categorias: Consoles (3), Jogos (10), Controles (4), Headsets (3), Teclados (3), Mouses (3),
Mousepads (2), Monitores (3), Cadeiras (3), Acessórios (6), Streaming (5), Hardware (5).

## Modelo de geração

Cada transação passa por três camadas, com gerador `random.Random(42)`:

1. **Cenário de compra**, sorteado por peso:

   | Cenário | Peso | Itens-semente (probabilidade) |
   |---|---|---|
   | pc_perifericos | 0,22 | teclados, mouses, headset (0,10–0,30) |
   | playstation | 0,16 | PS5 (0,50), FC 25 (0,25), jogos/controle/headset (0,05–0,15) |
   | switch | 0,14 | Switch OLED (0,45), Mario Kart (0,30), Zelda (0,25)… |
   | xbox | 0,12 | Xbox (0,50), Forza (0,30), Starfield (0,20), controle (0,15) |
   | setup | 0,10 | monitores (0,25–0,40), cadeiras (0,10–0,15) |
   | casual | 0,10 | jogos de PC (0,30), base carregadora, headset G435 (0,10) |
   | streaming | 0,08 | webcam (0,40), microfone (0,35), placa de captura, kit |
   | pc_build | 0,08 | GPU (0,35), gabinete, fonte, RAM, SSD (0,30) |

2. **Regras condicionais** (38 regras “se A na cesta, adiciona B com probabilidade p”), com
   **p entre 0,15 e 0,65**. São aplicadas em duas passadas, o que permite encadeamento
   (ex.: teclado → mouse → mousepad). Exemplos: Switch → capa (0,65), Switch → microSD (0,60),
   teclado Kumara → mouse G203 (0,65), webcam → microfone (0,60), gabinete → fonte (0,60).

3. **Ruído controlado**:
   - até 2 itens aleatórios do catálogo, cada um com probabilidade 0,25;
   - 5% das transações são cestas totalmente aleatórias (1 a 4 itens), cenário `aleatorio`;
   - cestas vazias recebem 1 item aleatório.

Os timestamps são uniformes ao longo de 2025 e servem só para dar realismo. Não são usados na mineração.

## Estatísticas reais (semente 42)

| Métrica | Valor |
|---|---|
| Transações | 5.000 |
| Itens por cesta (média) | 2,83 |
| Itens por cesta (mín. / máx.) | 1 / 9 |
| Cestas com 1 item | 1.605 (32,1%) |
| Cestas com 2+ itens | 3.395 (67,9%) |
| Cestas aleatórias (ruído) | 266 (5,3%) |

Distribuição de tamanho: 1 → 1.605 · 2 → 877 · 3 → 835 · 4 → 740 · 5 → 526 · 6 → 260 · 7 → 116 · 8 → 37 · 9 → 4.

Itens mais frequentes: Mouse Logitech G203 (663), Mousepad Speed Médio (602), Controle DualSense Extra (494),
Cabo HDMI 2.1 8K (484), Headset HyperX Cloud II (453), PlayStation 5 Slim (437).

## Reprodução

```bash
python -m ml.generate_catalog
python -m ml.generate_transactions            # --seed 42 --n 5000 (padrões)
python -m ml.preprocess
```

Com a mesma semente o arquivo gerado é idêntico byte a byte (finais de linha LF). A CI do backend
regenera o dataset e falha se houver diferença em `data/`.

## Divisão treino/teste

`ml/preprocess.py` embaralha as transações com `random_state=42` e separa 20% para teste
(1.000) e 80% para treino (4.000). A divisão é por transação inteira, então nenhuma cesta aparece nos dois conjuntos.
