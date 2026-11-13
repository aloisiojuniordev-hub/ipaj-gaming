# Roteiro de apresentação (≈ 10 minutos)

## Antes de começar (15 min antes)

- [ ] Abrir `https://<backend>/health` para “acordar” o Render (plano gratuito hiberna).
- [ ] Abrir o site publicado em aba anônima (carrinho limpo).
- [ ] Deixar abertos: Laboratório IA, `docs/evaluation.md` e o notebook executado.
- [ ] Plano B: ambiente local rodando (`uvicorn` + `npm run dev`), caso a internet falhe.

## 1. Problema e proposta (1 min)

“Lojas online perdem vendas quando o cliente não percebe o que combina com o que já escolheu.
O IPAJ Gaming tem um **Carrinho Inteligente**: o IPAJ CORE minera o histórico de compras com o
**Apriori** e sugere produtos que costumam ser comprados juntos, sempre mostrando a regra que justifica.”

## 2. Dados (1,5 min), por Iran Pablo ou Aloisio Junior

- 50 produtos, 5.000 transações **simuladas** com semente 42, totalmente reproduzíveis.
- 8 perfis de compra + 38 regras probabilísticas (p de 0,15 a 0,65) + ruído (itens aleatórios e 5% de cestas aleatórias).
- Divisão 80/20: 4.000 para treino e 1.000 para teste.
- Mostrar `docs/dataset.md` ou a célula de exploração do notebook.

## 3. Algoritmo (2 min)

- Explicar suporte, confiança e lift com **uma regra real** do Laboratório:
  *Webcam + Microfone → Ring Light: suporte 2,65%, confiança 84,1%, lift 16,26*.
  “Em 84% das compras com webcam e microfone também havia ring light, um padrão 16 vezes mais forte que o acaso.”
- Parâmetros: suporte ≥ 1%, confiança ≥ 30%, lift ≥ 1,2 e itemsets de até 3 itens. Resultado: 248 itemsets e **394 regras**.

## 4. Demonstração ao vivo (3 min)

1. **Home**: cena 3D (grafo de associações) e números do IPAJ CORE.
2. **Catálogo** → adicionar **PlayStation 5 Slim**.
3. **Carrinho**: o IPAJ CORE sugere DualSense (71,7%), EA FC 25 (61,8%) e Headset Pulse 3D (55,5%).
4. Adicionar o **DualSense** pela recomendação. A sugestão do FC 25 sobe para **77,5%**, porque uma regra com
   antecedente de 2 itens é mais específica.
5. Esvaziar o carrinho e adicionar só *Cyberpunk 2077 (PC)*. Esse é um caso **sem recomendação**:
   nenhuma regra cobre o item e o sistema não inventa sugestões.
6. **Checkout demonstrativo**: pedido criado e itens marcados como “via IPAJ CORE”.
7. **Laboratório**: ordenar regras por lift, mexer no filtro de confiança e usar o simulador.

## 5. Avaliação (1,5 min)

- Regras estáveis: confiança média de 0,638 no treino e 0,618 no teste. Lift de 8,86 para 8,60.
- Leave-one-out no teste: **Hit rate@3 = 58,7%** contra **11,9%** da linha de base por popularidade (~4,9×).
- Cobertura: 95,5% dos carrinhos, mas só 74% dos produtos chegam a ser recomendados.

## 6. Limitações e fechamento (1 min)

- Dados simulados: o resultado mede a recuperação de padrões planejados.
- 13 produtos nunca são recomendados e não há pagamento real.
- Trabalhos futuros: dados reais, ajuste dos limiares e comparação com FP-Growth.

## Perguntas prováveis

| Pergunta | Resposta curta |
|---|---|
| Por que Apriori e não FP-Growth? | Exigência da disciplina. Além disso, com 50 itens e 4.000 transações o Apriori roda em segundos. Os dois geram os mesmos itemsets. |
| Por que lift mínimo de 1,2? | Para descartar regras que só refletem a popularidade do item recomendado. |
| As regras de 100% de confiança não são suspeitas? | São regras do tipo acessório → console, coerentes com o gerador. O motor não recomenda o que já está no carrinho. |
| O modelo é retreinado em produção? | Não. O treino é offline e os artefatos são versionados, para que o deploy seja igual ao avaliado. |
| Onde ficam os dados de clientes? | No PostgreSQL (Supabase), acessado só pelo backend. Senhas com bcrypt e RLS bloqueando a API pública. |
