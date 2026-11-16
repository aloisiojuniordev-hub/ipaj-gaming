# IPAJ Gaming

**E-commerce gamer inteligente com sistema de recomendação baseado no algoritmo Apriori, desenvolvido por Iran Pablo e Aloisio Junior.**

| | |
|---|---|
| Integrantes | Iran Pablo e Aloisio Junior |
| Disciplina | Mineração de Dados |
| Técnica | Regras de associação com **Apriori** (mlxtend) |
| Stack | Python (mlxtend) · React + TypeScript · Supabase (PostgreSQL + Auth) · Netlify |

---

## Apresentação

**Problema.** Em uma loja online o cliente nem sempre percebe quais produtos combinam com o que já escolheu,
e a loja perde vendas complementares.

**Carrinho Inteligente.** O IPAJ Gaming recomenda produtos com base no que já está no carrinho. As
recomendações vêm de regras de associação mineradas do histórico de compras. Cada sugestão mostra a regra que
a justifica, junto com a confiança e o lift.

**A loja.** O catálogo tem 50 produtos gamer em 12 categorias, com busca, filtros, página de produto
(“frequentemente comprados juntos”), carrinho, checkout demonstrativo, cadastro e login. O checkout funciona
com conta ou como visitante.

**IPAJ CORE.** É o motor de recomendação. O treino roda com o Apriori em Python (mlxtend) e grava as
394 regras em `ml/artifacts/`. Elas são publicadas, sem alteração, junto com o site
(`scripts/export_static.py`). A cada mudança no carrinho, o motor procura as regras cujo antecedente está
contido nele. Se nenhuma regra se aplica, nada é recomendado: o sistema não inventa sugestões. Um teste
automático garante que o motor do site dá exatamente as mesmas respostas do motor Python.

## Demonstração

- **Site publicado:** *ainda não publicado.* O link será adicionado aqui depois do deploy (ver [docs/deployment.md](docs/deployment.md)).
- **Capturas de tela:** serão adicionadas a partir do site publicado.

Funcionalidades principais:

- Catálogo com busca, filtro por categoria e ordenação por preço
- Carrinho Inteligente com recomendações explicadas (confiança, lift e a regra usada)
- Página de produto com “frequentemente comprados juntos”
- **Laboratório IA**: métricas reais de treino e teste, tabela de regras com filtros, itemsets frequentes e simulador de carrinho
- Página “Como funciona” explicando o Apriori
- Cadastro e login (Supabase Auth) com histórico de pedidos salvo no PostgreSQL. Os itens que vieram de recomendação ficam marcados
- Cena 3D (Three.js) na página inicial representando o grafo de associações

## Tecnologias

| Área | Tecnologias |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, Three.js, Vitest + Testing Library |
| Mineração | Python, pandas, mlxtend (Apriori), joblib, Jupyter |
| Banco e login | Supabase: PostgreSQL (RLS + função `create_order`) e Supabase Auth, via `@supabase/supabase-js` |
| API de referência (local) | FastAPI, SQLAlchemy 2, Pydantic, PyJWT, bcrypt. Roda localmente e não é publicada |
| Deploy / CI | Netlify (site), GitHub Actions |

## Dataset

- **Origem:** simulada (não há compras reais), gerada por `ml/generate_transactions.py`.
- **Volume:** 5.000 transações e 50 produtos. As cestas têm em média 2,83 itens (de 1 a 9).
- **Estrutura** (`data/raw/transactions.csv`): `transaction_id, timestamp, scenario, n_items, items`,
  em que `items` são IDs separados por `;` (ex.: `P001;P004;P014`).
- **Regras de geração:**
  1. um de 8 perfis de compra (PlayStation, Xbox, Switch, periféricos de PC, setup, streaming, montagem de PC, casual) é sorteado por peso;
  2. os itens-semente do perfil entram, cada um com sua probabilidade;
  3. 38 regras condicionais (“se A na cesta, adiciona B”) são aplicadas em duas passadas.
- **Intervalos:** probabilidades das regras condicionais entre **0,15 e 0,65**. Pesos dos perfis entre 0,08 e 0,22.
- **Ruído controlado:** até 2 itens aleatórios por cesta (p = 0,25 cada) e 5% de cestas totalmente aleatórias.
- **Semente aleatória:** 42. O dataset é reproduzível byte a byte.
- **Como gerar:**

  ```bash
  python -m ml.generate_catalog
  python -m ml.generate_transactions      # opções: --seed 42 --n 5000
  ```

Detalhes em [docs/dataset.md](docs/dataset.md).

## Mineração de dados

- **Apriori:** encontra conjuntos de itens frequentes nível a nível. A poda vem da propriedade de que todo
  superconjunto de um conjunto raro também é raro. Depois, as regras A → B são derivadas desses conjuntos.
- **Preparação:** as cestas são deduplicadas e convertidas em matriz one-hot (`TransactionEncoder`).
- **Divisão 80/20:** embaralhamento com semente 42. São 4.000 transações de treino e 1.000 de teste, sem sobreposição.
- **Parâmetros:** suporte mínimo de 1%, confiança mínima de 30%, lift mínimo de 1,2, itemsets de até 3 itens e consequente com 1 item.
- **Itemsets:** 248 frequentes (50 de 1 item, 105 de 2 e 93 de 3).
- **Regras:** 394 (confiança de 0,30 a 1,00 e lift de 2,25 a 18,82).
- **Recomendações:** entre as regras com antecedente ⊆ carrinho e consequente ∉ carrinho, fica a melhor regra
  por produto. Os candidatos são ordenados por confiança e depois por lift.

Exemplo real: *PlayStation 5 Slim* → DualSense Extra (confiança 71,7%, lift 7,22), EA FC 25 (61,8%; 7,44)
e Headset Pulse 3D (55,5%; 8,23).

Metodologia completa em [docs/apriori-methodology.md](docs/apriori-methodology.md). A análise passo a passo
está em [notebooks/apriori_analysis.ipynb](notebooks/apriori_analysis.ipynb).

## Avaliação

Métricas reais, geradas por `ml/evaluate_apriori.py` e gravadas em `ml/artifacts/metrics.json`:

| Média das regras | Treino | Teste |
|---|---|---|
| Suporte | 0,0249 | 0,0233 |
| Confiança | 0,6383 | 0,6182 |
| Lift | 8,86 | 8,60 |

100% das regras mantêm lift > 1 no teste.

Na recomendação, avaliada por leave-one-out nas 671 cestas de teste com 2 ou mais itens:

| Métrica | Valor |
|---|---|
| Hit rate@3, IPAJ CORE | **58,72%** |
| Hit rate@3, linha de base (mais populares) | 11,92% |
| Cobertura de carrinhos | 95,53% |
| Cobertura de itens | 74% (37 de 50) |
| Precisão@3 nas cestas cobertas | 26,39% |

**Limitações observadas:** 13 produtos nunca são recomendados e 4,5% dos carrinhos ficam sem sugestão. Além
disso, como os dados são simulados, as métricas medem a recuperação de padrões que o próprio simulador planejou.
Ver [docs/evaluation.md](docs/evaluation.md).

## Instalação

### Pré-requisitos

- Python 3.12+ (testado com 3.13 localmente e 3.12 na CI)
- Node.js 20+ (testado com 24 localmente e 22 na CI)
- Git

### Setup automático

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Linux/macOS
bash scripts/setup.sh
```

### Setup manual

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    |   Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements-dev.txt -r ml/requirements.txt
cd frontend && npm ci && cd ..
```

### Variáveis de ambiente

```bash
cp frontend/.env.example frontend/.env.local   # preencha VITE_SUPABASE_PUBLISHABLE_KEY (chave pública)
```

Sem a chave, o site funciona normalmente: catálogo, recomendações Apriori e Laboratório. Só login e pedidos ficam indisponíveis.

A lista completa está em [docs/deployment.md](docs/deployment.md#variáveis-de-ambiente-resumo).

### Gerar dados e treinar (opcional, os artefatos já estão versionados)

```bash
python -m ml.generate_catalog
python -m ml.generate_transactions
python -m ml.preprocess
python -m ml.train_apriori
python -m ml.evaluate_apriori
python scripts/export_static.py   # publica as regras/métricas no site e gera database/migrations/004
```

Notebook: `pip install -r notebooks/requirements.txt` e depois `python notebooks/build_notebook.py --execute`.
Também dá para abrir `notebooks/apriori_analysis.ipynb` no Jupyter ou no VS Code.

### Executar

```bash
cd frontend
npm run dev          # http://localhost:5173
```

A API FastAPI em `backend/` é opcional e serve como referência local (`cd backend && uvicorn app.main:app --reload`,
docs em `/docs`). Ela usa SQLite local. **Não aponte essa API para o banco do Supabase:** na inicialização, ela
retira os privilégios públicos das tabelas, e o site deixaria de funcionar.

### Testes

```bash
cd backend  && ruff check app tests ../ml ../database ../scripts && pytest -q
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
python scripts/verify_project.py     # estrutura, artefatos e varredura de segredos
```

## Arquitetura

```text
ipaj-gaming/
├── ml/            simulador, pré-processamento, Apriori (mlxtend), avaliação, motor Python
│   └── artifacts/ rules.joblib · itemsets.joblib · metrics.json
├── frontend/      React + TypeScript (Vite)                → Netlify (netlify.toml)
│   └── src/data/  regras, itemsets, métricas e catálogo exportados dos artefatos
├── database/      schema.sql · migrations/ 001–004         → Supabase
├── backend/       API FastAPI de referência (local, não publicada)
├── data/          catalog/ · raw/ · processed/
├── notebooks/     apriori_analysis.ipynb
├── docs/          documentação técnica e acadêmica
└── scripts/       setup, export_static.py, verificação
```

- **Apriori:** a mineração é feita em Python e os artefatos são versionados. O site usa essas mesmas regras,
  então o que está publicado é exatamente o que foi avaliado.
- **Supabase:** o navegador usa só a chave **pública**.
  - Login: Supabase Auth.
  - Catálogo: leitura pública.
  - Pedidos: só pela função `create_order`, que valida a entrada e usa os **preços do banco**.
  - RLS: cada usuário lê apenas os próprios pedidos. Ninguém grava direto nas tabelas.

Diagrama e decisões técnicas em [docs/architecture.md](docs/architecture.md).

## Implantação

| Serviço | Papel | Configuração |
|---|---|---|
| **Supabase** | PostgreSQL + Auth | rodar no SQL Editor `schema.sql` e as migrações 002, 003 e 004 |
| **Netlify** | Site | `netlify.toml` na raiz: base `frontend`, `npm run build`, publish `dist`, fallback de SPA |

Variável no Netlify: `VITE_SUPABASE_PUBLISHABLE_KEY`, a chave **pública** do Supabase (`sb_publishable_...`).
`VITE_SUPABASE_URL` já está no `netlify.toml`. Nunca use a secret/service_role key no site.

O passo a passo completo está em [docs/deployment.md](docs/deployment.md).

## Uso de inteligência artificial

| Ferramenta | Finalidade |
|---|---|
| **Kiro** (agente de IA do ambiente de desenvolvimento Kiro) | Estruturação da arquitetura do monorepo, escrita de código (simulador, pipeline Apriori, backend, frontend, testes, CI), criação dos componentes visuais, investigação de erros e redação da documentação |

As métricas e os resultados vêm da execução real dos scripts. Os integrantes devem acrescentar aqui qualquer
outra ferramenta de IA que tenham usado.

## Autores

- **Iran Pablo**
- **Aloisio Junior**

A divisão de tarefas está registrada em [docs/academic-report.md](docs/academic-report.md#7-divisão-de-tarefas).
Guia de colaboração em [CONTRIBUTING.md](CONTRIBUTING.md).

## Limitações

- Os dados de compras são **simulados**.
- As compras do e-commerce são **demonstrativas**.
- **Não existe processamento real de pagamento.**
- As recomendações dependem das associações presentes no dataset.
- Nem toda combinação de produtos gera recomendação: 13 dos 50 produtos nunca são recomendados e cerca de 4,5% dos carrinhos de teste ficam sem sugestão.

## Licença

Nenhuma licença foi definida ainda. Os integrantes devem escolher uma (por exemplo, MIT) e adicionar um arquivo `LICENSE`.
