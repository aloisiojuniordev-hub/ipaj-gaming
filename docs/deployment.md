# Implantação — GitHub, Supabase, Render e Netlify

Ordem recomendada: **GitHub → Supabase → Render → Netlify → ajustar CORS no Render**.

| Camada | Serviço | Configuração no repositório |
|---|---|---|
| Frontend (React/Vite) | **Netlify** | `netlify.toml` (raiz) |
| Backend (FastAPI + Apriori) | **Render** | `render.yaml` (raiz) |
| Banco (PostgreSQL) | **Supabase** | `database/schema.sql` |

O Apriori roda **somente no backend**. O Netlify só serve os arquivos estáticos do React, que chamam a API do Render.

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
   Isso cria tabelas, índices, restrições e ativa RLS. Confira no **Table Editor** que as 4 tabelas
   aparecem sem o aviso "RLS disabled".
   *Rede de segurança:* se o backend subir antes deste passo, ele mesmo cria as tabelas e ativa RLS
   na mesma transação (`ensure_schema`). Mesmo assim, rodar o `schema.sql` é o caminho recomendado,
   porque ele também é a referência das migrações.
   *Opcional (recomendado):* em **Project Settings → Data API**, remova `public` de *Exposed schemas*.
   O projeto não usa a Data API, já que o frontend fala só com o FastAPI.
3. **Connect** (ou Project Settings → Database) → **Connection string → URI**.
   Use o **Session pooler** (porta 5432), compatível com IPv4, que o Render exige:
   ```
   postgresql://postgres.<ref>:<SENHA>@aws-0-<regiao>.pooler.supabase.com:5432/postgres?sslmode=require
   ```

   | Modo do Supabase | Funciona? |
   |---|---|
   | Direct connection (`db.<ref>.supabase.co`) | Não no Render: endereço só IPv6 |
   | **Session pooler** (porta 5432) | **Sim, recomendado** |
   | Transaction pooler (porta 6543) | Sim: o backend desativa prepared statements para ser compatível |

   O backend força SSL (`DATABASE_SSLMODE=require`, que prevalece sobre o `sslmode` da URL).
   Com `ENVIRONMENT=production`, ele **não inicia** se `DATABASE_URL` não for PostgreSQL, se o SSL
   estiver desligado ou se `JWT_SECRET` tiver menos de 32 caracteres. Isso evita o fallback
   silencioso para um SQLite efêmero.
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
   - `CORS_ORIGINS`: por enquanto `http://localhost:5173`. Depois do passo 4, troque pela URL do Netlify.
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
(gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"`), `CORS_ORIGINS`, `SEED_ON_STARTUP=true`,
`DATABASE_SSLMODE=require`.

**Por que não `Root Directory = backend`?** O backend importa `ml/recommendation_engine.py` e lê
`ml/artifacts/` e `data/catalog/`, que ficam fora de `backend/`. Rodar a partir da raiz garante que esses
arquivos estejam no ambiente. O `buildFilter` do Blueprint evita redeploys quando só o frontend muda.

Validação: abra `https://<servico>.onrender.com/health`. A resposta deve ser
`"status": "ok"`, `"database": "ok"` e `"rules_loaded": 394`. Se aparecer `"database": "rls_disabled"`,
alguma tabela do app está sem RLS: rode `database/schema.sql` de novo.

**Plano gratuito:** confira as condições atuais em <https://render.com/pricing> antes de publicar.
Serviços gratuitos hibernam sem tráfego, e a primeira requisição depois disso pode levar dezenas de segundos.
Abra `/health` alguns minutos antes da apresentação.

---

## 4. Netlify (frontend)

A configuração de build já está versionada em `netlify.toml`, na raiz do repositório:

| Campo | Valor | Observação |
|---|---|---|
| Base directory | `frontend` | o Netlify roda `npm install` e o build dentro dela |
| Build command | `npm run build` | `tsc -b && vite build` |
| Publish directory | `dist` | relativo à base, ou seja, `frontend/dist` |
| Node | 22 | `NODE_VERSION` em `[build.environment]` |
| Fallback de SPA | `/*` → `/index.html` (200) | `/catalogo`, `/carrinho`, `/laboratorio` funcionam ao recarregar |
| Headers | anti-clickjacking, `nosniff`, cache imutável em `/assets/*` | |

Como o arquivo já define tudo, **não preencha** valores diferentes no painel: o `netlify.toml` tem prioridade.

### Conectar ao GitHub (painel)

1. Acesse <https://app.netlify.com> e entre com **GitHub**.
2. **Add new project → Import an existing project → GitHub**. Autorize o app do Netlify
   no repositório `aloisiojuniordev-hub/ipaj-gaming`, se ele pedir.
3. Selecione `ipaj-gaming` e a branch **`main`**. Os campos de build aparecem preenchidos a partir do `netlify.toml`:
   base `frontend`, comando `npm run build`, publish `frontend/dist`.
4. **Environment variables → Add a variable**:
   `VITE_API_URL = https://<servico>.onrender.com` (sem barra no final), escopo *Builds*, todos os contextos.
   Variáveis `VITE_` vão para o JavaScript público, então **nunca coloque segredos nelas**.
5. **Deploy**. A partir daí:
   - cada push na `main` publica em produção (*Branch deploys: production branch* ativado por padrão);
   - cada PR ganha um *Deploy Preview* em `https://deploy-preview-<N>--<site>.netlify.app`.

Se o site já tiver sido criado pela CLI, sem repositório, vincule em
**Project configuration → Build & deploy → Continuous deployment → Link repository**.

> **Importante:** o `VITE_API_URL` é embutido **no build**. Depois de criar ou alterar a variável, faça
> **Deploys → Trigger deploy → Deploy project** (ou um novo push) para que ela entre em vigor.

### Alternativa: Netlify CLI

```bash
npm install -g netlify-cli
netlify login
netlify link            # ou: netlify sites:create --name <nome>
netlify deploy --build          # deploy de rascunho (URL única), para testar
netlify deploy --build --prod   # produção
```

O arquivo `frontend/vercel.json` foi mantido apenas como referência. Ele **não é usado** pelo Netlify.

---

## 5. Fechar o ciclo

1. No Render, atualize `CORS_ORIGINS` com a URL de produção do Netlify, por exemplo
   `https://ipaj-gaming.netlify.app`. A barra final é removida automaticamente.
   Para aceitar também os Deploy Previews e branch deploys, defina a variável opcional
   `CORS_ORIGIN_REGEX = https://([a-z0-9-]+--)?ipaj-gaming\.netlify\.app` (troque `ipaj-gaming` pelo nome real do site).
2. O Render redeploya sozinho. Teste no site publicado:
   - [ ] catálogo carrega (API + banco);
   - [ ] adicionar PS5 ao carrinho mostra recomendações do IPAJ CORE;
   - [ ] Laboratório mostra 394 regras e as métricas;
   - [ ] cadastro, login e checkout criam o pedido. Confira em Supabase → Table Editor → `orders`.
3. Atualize no README a seção *Demonstração* com as URLs reais.

## Variáveis de ambiente (resumo)

| Variável | Onde | Obrigatória | Exemplo |
|---|---|---|---|
| `VITE_API_URL` | Netlify | sim | `https://<servico>.onrender.com` |
| `DATABASE_URL` | Render | sim (produção) | `postgresql://postgres.<ref>:<SENHA>@...pooler.supabase.com:5432/postgres?sslmode=require` |
| `JWT_SECRET` | Render | sim (produção) | valor aleatório de 48+ caracteres |
| `CORS_ORIGINS` | Render | sim | `https://<site>.netlify.app` |
| `CORS_ORIGIN_REGEX` | Render | não | `https://([a-z0-9-]+--)?<site>\.netlify\.app` (Deploy Previews) |
| `ENVIRONMENT` | Render | sim | `production` |
| `SEED_ON_STARTUP` | Render | não (padrão `true`) | `true` |
| `DATABASE_SSLMODE` | Render | não (padrão `require`) | `require` |
| `JWT_EXPIRES_MINUTES` | Render | não (padrão `120`) | `120` |
| `PYTHON_VERSION` | Render | recomendado | `3.12.8` |
