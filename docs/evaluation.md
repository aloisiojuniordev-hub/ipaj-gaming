# Avaliação

Todos os números abaixo foram produzidos por `ml/evaluate_apriori.py` e estão em
`ml/artifacts/metrics.json` (semente 42, treino em 4.000 e teste em 1.000 transações).

## Metodologia

### 1. Estabilidade das regras (treino × teste)

Cada uma das 394 regras teve suporte, confiança e lift **recalculados** nas 1.000 transações de teste,
que o Apriori nunca viu. Se as médias ficam próximas, as regras generalizam e não são artefato do treino.

### 2. Qualidade da recomendação (leave-one-out)

Para cada transação de teste com 2 ou mais itens (671 cestas):

1. um item é ocultado (sorteio com semente fixa);
2. os itens restantes formam o “carrinho”;
3. o IPAJ CORE gera o Top-3;
4. **acerto** = o item oculto aparece no Top-3.

**Linha de base:** recomendar os 3 produtos mais populares do treino que ainda não estão no carrinho.

| Métrica | Definição |
|---|---|
| Hit rate@3 (todos) | acertos / cestas avaliadas |
| Hit rate@3 (cobertos) | acertos / cestas que receberam alguma recomendação |
| Precisão@3 (cobertos) | média de (acerto / nº de recomendações). Como só 1 item é ocultado, o teto é 33,3% com 3 recomendações |
| Cobertura de carrinhos | % das cestas avaliadas com pelo menos 1 recomendação |
| Cobertura de itens | % dos produtos que aparecem como consequente de alguma regra |

## Resultados

### Regras: treino × teste

| Média das 394 regras | Treino | Teste | Variação |
|---|---|---|---|
| Suporte | 0,0249 | 0,0233 | −6,4% |
| Confiança | 0,6383 | 0,6182 | −3,1% |
| Lift | 8,8599 | 8,6030 | −2,9% |

**100%** das regras mantêm lift > 1 no teste.

### Recomendação

| Métrica | IPAJ CORE (Apriori) | Linha de base (popularidade) |
|---|---|---|
| Hit rate@3 (todas as 671 cestas) | **58,72%** | 11,92% |
| Hit rate@3 (cestas cobertas) | 61,47% | — |
| Precisão@3 (cestas cobertas) | 26,39% | — |
| Cobertura de carrinhos | 95,53% | 100% (por construção) |
| Cobertura de itens | 74,00% (37 de 50) | — |

O Apriori acerta o item oculto cerca de **4,9 vezes mais** que a linha de base por popularidade.

## Discussão

- **Generalização:** a queda de treino para teste é pequena (3% na confiança e no lift). Faz sentido,
  porque as regras capturam a estrutura do gerador e não coincidências do conjunto de treino.
- **Regras “reversas”:** as regras de confiança 100% apontam para o console (ex.: Capa + Pro Controller → Switch).
  No simulador os acessórios de Switch quase só aparecem junto do console, então a regra é correta.
  Na loja, porém, o item recomendado costuma já estar no carrinho, e o motor nunca recomenda itens que o
  cliente já tem.
- **Lift alto** (até 18,8) aparece entre produtos de nicho com suporte individual baixo, como os acessórios
  de monitor e de streaming.

## Limitações observadas

1. **Dados simulados.** O hit rate mede quanto o Apriori recupera os padrões do próprio simulador.
   Não é estimativa de desempenho com clientes reais.
2. **13 produtos nunca são recomendados** (P005, P006, P008, P011, P012, P013, P017, P020, P023, P026, P033,
   P044, P045). São itens-semente de baixa probabilidade sem regras condicionais fortes, como jogos específicos,
   um dos teclados e a placa de captura.
3. **4,5% das cestas de teste não recebem recomendação**, porque nenhuma regra cobre aquela combinação.
   Por decisão de projeto não há fallback.
4. **Cestas de 1 item (32% do dataset)** não entram na avaliação leave-one-out, porque não sobra carrinho.
5. Os limiares (1% / 30% / 1,2) foram escolhidos por justificativa de domínio, sem busca exaustiva.
   Variar os limiares é um trabalho futuro.

## Reprodução

```bash
python -m ml.evaluate_apriori      # imprime e grava as métricas em metrics.json
```
