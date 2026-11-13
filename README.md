# IPAJ Gaming

**E-commerce gamer inteligente com sistema de recomendação baseado no algoritmo Apriori, desenvolvido por Iran Pablo e Aloisio Junior.**

| | |
|---|---|
| Integrantes | Iran Pablo e Aloisio Junior |
| Disciplina | Mineração de Dados |
| Técnica | Regras de associação com **Apriori** (mlxtend) |
| Stack | React + TypeScript · FastAPI · PostgreSQL (Supabase) · Vercel · Render |

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

**IPAJ CORE.** É o motor de recomendação. O treino roda offline com o Apriori e grava as regras em
`ml/artifacts/`. O backend carrega essas regras e, a cada mudança no carrinho, procura as que têm o
antecedente contido nele. Se nenhuma regra se aplica, nada é recomendado: o sistema não inventa sugestões.

## Demonstração

- **Site publicado:** *ainda não publicado.* O link será adicionado aqui depois do deploy (ver [docs/deployment.md](docs/deployment.md)).
- **Capturas de tela:** serão adicionadas a partir do site publicado.

Funcionalidades principais:

- Catálogo com busca, filtro por categoria e ordenação por preço
- Carrinho Inteligente com recomendações explicadas (confiança, lift e a regra usada)
- Página de produto com “frequentemente comprados juntos”
- **Laboratório IA**: métricas reais de treino e teste, tabela de regras com filtros, itemsets frequentes e simulador de carrinho
- Página “Como funciona” explicando o Apriori
- Cadastro e login (JWT) com histórico de pedidos. Os itens que vieram de recomendação ficam marcados
- Cena 3D (Three.js) na página inicial representando o grafo de associações

## Tecnologias

| Área | Tecnologias |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router, Three.js, Vitest + Testing Library |
| Backend | Python, FastAPI, SQLAlchemy 2, Pydantic, PyJWT, bcrypt, Uvicorn |
| Mineração | pandas, mlxtend (Apriori), joblib, Jupyter |
| Banco | PostgreSQL no Supabase (SQLite local e nos testes) |
| Deploy / CI | Vercel (frontend), Render (backend), GitHub Actions |

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
cp backend/.env.example backend/.env           # sem DATABASE_URL, usa SQLite local
cp frontend/.env.example frontend/.env.local   # VITE_API_URL=http://localhost:8000
```

A lista completa está em [docs/deployment.md](docs/deployment.md#variáveis-de-ambiente-resumo).

### Gerar dados e treinar (opcional, os artefatos já estão versionados)

```bash
python -m ml.generate_catalog
python -m ml.generate_transactions
python -m ml.preprocess
python -m ml.train_apriori
python -m ml.evaluate_apriori
```

Notebook: `pip install -r notebooks/requirements.txt` e depois `python notebooks/build_notebook.py --execute`.
Também dá para abrir `notebooks/apriori_analysis.ipynb` no Jupyter ou no VS Code.

### Executar

```bash
# Terminal 1: backend em http://localhost:8000 (docs em /docs)
cd backend
uvicorn app.main:app --reload

# Terminal 2: frontend em http://localhost:5173
cd frontend
npm run dev
```

Na primeira execução o backend cria as tabelas e carrega o catálogo sozinho.

### Testes

```bash
cd backend  && ruff check app tests ../ml ../database ../scripts && pytest -q
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
python scripts/verify_project.py     # estrutura, artefatos e varredura de segredos
```

## Arquitetura

```text
ipaj-gaming/
├── frontend/      React + TypeScript (Vite)                → Vercel
├── backend/       FastAPI (api, core, database, schemas)   → Render
├── ml/            simulador, pré-processamento, Apriori, avaliação, motor
│   └── artifacts/ rules.joblib · itemsets.joblib · metrics.json
├── data/          catalog/ · raw/ · processed/
├── notebooks/     apriori_analysis.ipynb
├── database/      schema.sql · migrations/ · seed.py      → Supabase
├── docs/          documentação técnica e acadêmica
└── scripts/       setup e verificação
```

- **React ↔ FastAPI:** chamadas `fetch` com JSON para `VITE_API_URL`. O CORS é restrito às origens em `CORS_ORIGINS`
  e a autenticação usa `Authorization: Bearer <JWT>`.
- **PostgreSQL:** guarda catálogo, usuários e pedidos demonstrativos. Os preços dos pedidos vêm sempre do banco.
  Só o backend acessa o banco, e o RLS bloqueia a API pública do Supabase.
- **Artefatos do Apriori:** são gerados offline e versionados. O backend só precisa de `joblib` e do
  `recommendation_engine.py` (não usa pandas nem mlxtend em produção), então o que roda publicado é exatamente
  o que foi avaliado.

Diagrama e decisões técnicas em [docs/architecture.md](docs/architecture.md). Endpoints em [docs/api.md](docs/api.md).

## Implantação

| Serviço | Papel | Configuração |
|---|---|---|
| **Supabase** | PostgreSQL | rodar `database/schema.sql` no SQL Editor e usar a string do *Session pooler* |
| **Render** | Backend | Blueprint `render.yaml`, health check em `/health` |
| **Vercel** | Frontend | Root `frontend`, preset Vite, `npm run build`, saída `dist`, fallback de SPA em `vercel.json` |

Variáveis necessárias:

- **Render:** `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS`, `ENVIRONMENT=production`, `SEED_ON_STARTUP`, `DATABASE_SSLMODE`, `PYTHON_VERSION`.
- **Vercel:** `VITE_API_URL`. Ela é pública, então nunca deve conter segredos.

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
