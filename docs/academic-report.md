# IPAJ Gaming: recomendação de produtos com regras de associação (Apriori)

**Disciplina:** Mineração de Dados · **Técnica:** Apriori (regras de associação)
**Integrantes:** Iran Pablo e Aloisio Junior

## 1. Introdução e objetivo

Em lojas online, parte das vendas complementares se perde quando o cliente não percebe quais produtos
combinam com o que já escolheu. O objetivo do trabalho foi construir um e-commerce gamer demonstrativo,
o **IPAJ Gaming**, com um **Carrinho Inteligente** (IPAJ CORE). Ele recomenda produtos a partir de regras
de associação mineradas com o algoritmo Apriori e mostra ao usuário a regra, a confiança e o lift de cada sugestão.

## 2. Dados

Como não havia histórico real disponível, foi construído um **simulador probabilístico reprodutível**
(semente 42) com um catálogo de 50 produtos em 12 categorias e 5.000 transações. Cada transação parte de um de
8 perfis de compra (ex.: PlayStation, periféricos de PC, streaming), recebe itens-semente com probabilidades
próprias e depois passa por 38 regras condicionais (p entre 0,15 e 0,65), aplicadas em duas passadas para
permitir encadeamento. Por fim recebe **ruído controlado**: até dois itens aleatórios (p = 0,25 cada) e 5% de
cestas totalmente aleatórias. As cestas têm em média 2,83 itens (de 1 a 9). Os dados foram divididos
aleatoriamente em **80% para treino (4.000)** e **20% para teste (1.000)**.

## 3. Metodologia

As transações de treino foram convertidas em matriz one-hot (`TransactionEncoder`) e processadas com
`apriori` e `association_rules` da biblioteca **mlxtend**. Parâmetros: **suporte mínimo de 1%**,
**confiança mínima de 30%**, **lift mínimo de 1,2**, itemsets de até 3 itens e consequente com um único produto.
Para recomendar, o sistema seleciona as regras cujo antecedente está contido no carrinho e cujo consequente
ainda não está, e ordena os candidatos por confiança e lift. Quando nenhuma regra se aplica, nada é recomendado.

A avaliação teve duas partes. (i) **Estabilidade:** suporte, confiança e lift de cada regra foram recalculados
no teste. (ii) **Recomendação (leave-one-out):** em cada cesta de teste com 2 ou mais itens, um item foi ocultado
e verificou-se se ele aparecia no Top-3. A comparação foi feita com uma linha de base que recomenda os itens
mais populares do treino.

## 4. Resultados

O Apriori gerou **248 itemsets frequentes** e **394 regras** (confiança de 0,30 a 1,00 e lift de 2,25 a 18,82).

| Métrica (média das regras) | Treino | Teste |
|---|---|---|
| Suporte | 0,0249 | 0,0233 |
| Confiança | 0,6383 | 0,6182 |
| Lift | 8,86 | 8,60 |

Todas as regras mantiveram lift > 1 no teste. Na avaliação leave-one-out (671 cestas), o IPAJ CORE alcançou
**Hit rate@3 de 58,72%**, contra **11,92%** da linha de base por popularidade. A cobertura foi de 95,53% dos
carrinhos e 74% dos produtos.

Exemplos de regras: *Webcam + Microfone USB → Ring Light* (confiança 84,1%, lift 16,26) e
*Nintendo Switch OLED → Cartão microSD* (65,1%, lift 10,76).

## 5. Discussão e limitações

A pequena queda entre treino e teste (cerca de 3% na confiança e no lift) indica que as regras generalizam.
O ganho sobre a linha de base (cerca de 4,9×) mostra que o Apriori capturou as dependências entre produtos e
não apenas a popularidade. As regras de confiança 100% são do tipo “acessório → console”, coerentes com o
gerador, mas pouco úteis na loja, pois o console normalmente já está no carrinho.

Limitações: (1) os dados são **simulados**, então os resultados medem a recuperação de padrões planejados e
não o comportamento de clientes reais; (2) 13 dos 50 produtos nunca são recomendados; (3) 4,5% dos carrinhos
de teste ficam sem recomendação; (4) os limiares foram definidos por critério de domínio, sem busca sistemática.
As compras da loja são demonstrativas e não há processamento de pagamento.

## 6. Conclusão

O projeto entrega um pipeline de mineração reprodutível, um motor de recomendação explicável e uma aplicação
web completa (React, FastAPI e PostgreSQL) que expõe as regras e métricas reais no Laboratório IA. Trabalhos
futuros: aplicar o método a dados reais, ajustar os limiares sistematicamente e comparar com FP-Growth.

## 7. Divisão de tarefas

> **Pendente de confirmação pelos integrantes.** Esta seção deve registrar quem fez cada parte, de acordo com o
> que de fato aconteceu e com o histórico de commits do GitHub. Não foi preenchida para não atribuir
> participações não confirmadas.

| Atividade | Responsável(is) |
|---|---|
| Dataset e simulador | *a confirmar* |
| Treinamento e avaliação do Apriori | *a confirmar* |
| Backend (FastAPI, banco) | *a confirmar* |
| Frontend (React, Laboratório IA) | *a confirmar* |
| Implantação (GitHub, Supabase, Render, Vercel) | *a confirmar* |
| Documentação e relatório | *a confirmar* |

## 8. Uso de inteligência artificial

O assistente **Kiro** (agente de IA do ambiente de desenvolvimento Kiro) foi usado para estruturar a arquitetura
do monorepo, escrever o código (simulador, pipeline Apriori, backend, frontend e testes), investigar erros e
redigir a documentação. Todos os resultados numéricos deste relatório vêm da execução real dos scripts
(`ml/artifacts/metrics.json`). Os integrantes devem acrescentar aqui outras ferramentas de IA que tenham usado.
