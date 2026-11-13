# Implantação — GitHub, Supabase, Render e Vercel

Ordem recomendada: **GitHub → Supabase → Render → Vercel → ajustar CORS no Render**.

> Nenhuma URL de produção aparece aqui porque o projeto ainda não foi publicado.
> Depois do deploy, registre as URLs reais no README.

---

## 1. GitHub

Pré-requisitos: [Git](https://git-scm.com/downloads) e, opcionalmente, o [GitHub CLI](https://cli.github.com/).

No Windows:

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
# feche e reabra o terminal
```

Configure a identidade (cada integrante, na própria máquina):

```bash
git config --global user.name "Seu Nome"
git config --global user.email "email-do-github@example.com"
```

Primeiro commit (na raiz do projeto):

```bash
git init
git branch -M main
python scripts/verify_project.py      # confere arquivos e procura segredos ANTES do commit
git add .
git status                            # confirme que nenhum .env, .venv, node_modules ou *.db aparece
git commit -m "feat: estrutura inicial IPAJ Gaming"
```

Criar o repositório remoto e enviar:

```bash
# Opção A: GitHub CLI
gh auth login
gh repo create ipaj-gaming --public --source=. --remote=origin \
  --description "IPAJ Gaming — E-commerce gamer inteligente com sistema de recomendação baseado no algoritmo Apriori, desenvolvido por Iran Pablo e Aloisio Junior."
git push -u origin main

# Opção B: crie o repositório vazio em https://github.com/new (sem README, sem .gitignore) e:
git remote add origin https://github.com/<usuario>/ipaj-gaming.git
git push -u origin main
```

Depois:

- **Settings → Collaborators**: adicione o outro integrante.
- **Settings → Branches**: proteja `main` (exigir PR, 1 aprovação e status checks *Frontend CI* / *Backend CI*).
- **Actions**: confirme que os dois workflows rodaram e passaram.

---

## 2. Supabase (PostgreSQL)

1. Crie um projeto em <https://supabase.com/dashboard> e **guarde a senha do banco** (ela não é mostrada de novo).
2. **SQL Editor → New query**: cole o conteúdo de `database/schema.sql` e execute.
   Isso cria tabelas, índices, restrições e ativa RLS.
3. **Connect** (ou Project Settings → Database) → **Connection string → URI**.
   Use o **Session pooler** (porta 5432), compatível com IPv4, que o Render exige:
   ```
   postgresql://postgres.<ref>:<SENHA>@aws-0-<regiao>.pooler.supabase.com:5432/postgres?sslmode=require
   ```
4. Carga inicial do catálogo. São duas opções equivalentes:
   - automática: o backend carrega `products.csv` na primeira inicialização se a tabela estiver vazia (`SEED_ON_STARTUP=true`);
   - manual, da sua máquina:
     ```bash
     # PowerShell: $env:DATABASE_URL="postgresql://..."   |   bash: export DATABASE_URL="postgresql://..."
     python database/seed.py
     ```

**Segurança:** a string de conexão contém a senha. Ela fica só no painel do Render e no `backend/.env`
local, que é ignorado pelo Git. O frontend nunca recebe credenciais do banco. Com RLS ativado e sem
políticas, a API REST pública do Supabase não lê nem grava nas tabelas.

**Restauração do ambiente:** rode `schema.sql` de novo (é idempotente) e depois `python database/seed.py`.
Contas e pedidos demonstrativos não têm backup automático no plano gratuito. Para isso, use
*Database → Backups* nos planos pagos, ou `pg_dump "$DATABASE_URL" > backup.sql`.

---

## 3. Render (backend FastAPI)

### Opção A: Blueprint (recomendada)

1. <https://dashboard.render.com> → **New → Blueprint** → conecte o repositório GitHub.
2. O Render lê `render.yaml` e cria o serviço `ipaj-gaming-api`.
3. Preencha as variáveis marcadas como `sync: false`:
   - `DATABASE_URL`: a string do Supabase (passo 2.3);
   - `CORS_ORIGINS`: por enquanto `http://localhost:5173`. Depois do passo 4, troque pela URL da Vercel.
4. `JWT_SECRET` é gerado automaticamente pelo Blueprint.

### Opção B: Web Service manual

| Campo | Valor |
|---|---|
| Runtime | Python 3 |
| Branch | `main` |
| Root Directory | *(vazio, raiz do repositório)* |
| Build Command | `pip install -r backend/requirements.txt` |
| Start Command | `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Auto-Deploy | On Commit |

Variáveis: `PYTHON_VERSION=3.12.8`, `ENVIRONMENT=production`, `DATABASE_URL`, `JWT_SECRET`
(gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"`), `CORS_ORIGINS`, `SEED_ON_STARTUP=true`.

**Por que não `Root Directory = backend`?** O backend importa `ml/recommendation_engine.py` e lê
`ml/artifacts/` e `data/catalog/`, que ficam fora de `backend/`. Rodar a partir da raiz garante que esses
arquivos estejam no ambiente. O `buildFilter` do Blueprint evita redeploys quando só o frontend muda.

Validação: abra `https://<servico>.onrender.com/health`. A resposta deve ser
`"status": "ok"` e `"rules_loaded": 394`.

**Plano gratuito:** confira as condições atuais em <https://render.com/pricing> antes de publicar.
Serviços gratuitos hibernam sem tráfego, e a primeira requisição depois disso pode levar dezenas de segundos.
Abra `/health` alguns minutos antes da apresentação.

---

## 4. Vercel (frontend)

1. <https://vercel.com/new> → importe o repositório do GitHub.
2. Configure:

| Campo | Valor |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm ci` |

3. **Environment Variables**: `VITE_API_URL = https://<servico>.onrender.com` (sem barra no final).
   Variáveis `VITE_` vão para o JavaScript público, então **nunca coloque segredos nelas**.
4. Deploy. Pushes na `main` passam a publicar automaticamente, e PRs ganham *preview deployments*.

O fallback de rotas da SPA está em `frontend/vercel.json`: tudo é reescrito para `index.html`, então
`/laboratorio` e `/produto/P001` funcionam ao recarregar a página.

---

## 5. Fechar o ciclo

1. No Render, atualize `CORS_ORIGINS` com a URL de produção da Vercel, por exemplo
   `https://ipaj-gaming.vercel.app`. Para aceitar também os previews, liste as URLs separadas por vírgula.
2. O Render redeploya sozinho. Teste no site publicado:
   - [ ] catálogo carrega (API + banco);
   - [ ] adicionar PS5 ao carrinho mostra recomendações do IPAJ CORE;
   - [ ] Laboratório mostra 394 regras e as métricas;
   - [ ] cadastro, login e checkout criam o pedido. Confira em Supabase → Table Editor → `orders`.
3. Atualize no README a seção *Demonstração* com as URLs reais.

## Variáveis de ambiente (resumo)

| Variável | Onde | Obrigatória | Exemplo |
|---|---|---|---|
| `VITE_API_URL` | Vercel | sim | `https://<servico>.onrender.com` |
| `DATABASE_URL` | Render | sim (produção) | `postgresql://postgres.<ref>:<SENHA>@...pooler.supabase.com:5432/postgres?sslmode=require` |
| `JWT_SECRET` | Render | sim (produção) | valor aleatório de 48+ caracteres |
| `CORS_ORIGINS` | Render | sim | `https://<projeto>.vercel.app` |
| `ENVIRONMENT` | Render | sim | `production` |
| `SEED_ON_STARTUP` | Render | não (padrão `true`) | `true` |
| `JWT_EXPIRES_MINUTES` | Render | não (padrão `120`) | `120` |
| `PYTHON_VERSION` | Render | recomendado | `3.12.8` |
