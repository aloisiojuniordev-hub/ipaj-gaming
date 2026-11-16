# Implantação — GitHub, Supabase e Netlify

| Camada | Serviço | Configuração no repositório |
|---|---|---|
| Site (React/Vite) + IPAJ CORE | **Netlify** | `netlify.toml` (raiz) |
| Banco (PostgreSQL) + login | **Supabase** | `database/schema.sql` e `database/migrations/` |
| Mineração Apriori | **Python, offline** | `ml/` → `scripts/export_static.py` |

Não há servidor Python em produção. O Apriori é executado em Python (mlxtend) e as 394 regras reais são
exportadas para o site. O navegador só **consulta** essas regras, e um teste garante que ele responde igual
ao motor Python. Login e pedidos usam o Supabase com a chave **pública**, protegida por RLS e por uma
função SQL que calcula os preços no banco.

---

## 1. Supabase

**Projeto:** `https://lvukeuyexxewmnslucwj.supabase.co` (ref `lvukeuyexxewmnslucwj`).

### 1.1 SQL (SQL Editor → New query, um arquivo por vez, nesta ordem)

| Ordem | Arquivo | O que faz | Destrutivo? |
|---|---|---|---|
| 1 | `database/schema.sql` | cria as 4 tabelas e ativa RLS | Não |
| 2 | `database/migrations/002_revoke_public_roles.sql` | fecha as tabelas para as roles públicas | Não |
| 3 | `database/migrations/003_frontend_supabase_access.sql` | coluna `auth_user_id`, leitura pública do catálogo, RLS "só os meus pedidos", função `create_order` | Não |
| 4 | `database/migrations/004_seed_products.sql` | carrega os 50 produtos (insere ou atualiza) | Não |

Todos são idempotentes: podem ser executados de novo sem problema.

Depois do passo 4, `SELECT count(*) FROM products;` deve retornar **50**.

### 1.2 Chave pública

**Connect → Framework**. Copie o valor `sb_publishable_...`, que é a *publishable key*. Ela é pública por
definição e vai para o Netlify. **Nunca** use `sb_secret_...` nem a `service_role` no site.

### 1.3 Auth (Authentication no menu)

- **URL Configuration → Site URL:** a URL do Netlify, por exemplo `https://<site>.netlify.app`.
  Ela é usada nos links de confirmação de e-mail.
- **Sign In / Providers → Email:**
  - *Confirm email* **ligado** (padrão): o usuário confirma pelo e-mail antes do primeiro login.
    O plano gratuito limita o envio de e-mails por hora.
  - *Confirm email* **desligado**: o cadastro entra direto, o que é mais prático para a demonstração.

### 1.4 Segurança (o que o navegador pode e não pode)

| Ação com a chave pública | Visitante | Logado |
|---|---|---|
| Ler o catálogo | ✅ | ✅ |
| Criar pedido via `create_order` (preço do banco) | ✅ | ✅ (vinculado à conta) |
| Ler pedidos | ❌ | ✅ só os próprios (RLS) |
| Gravar, alterar ou apagar direto em qualquer tabela | ❌ | ❌ |
| Ler a tabela `users` (do backend local) | ❌ | ❌ |

Esse comportamento é testado num PostgreSQL real na CI (`backend/tests/test_supabase_sql.py`).

---

## 2. Netlify

A configuração de build está em `netlify.toml`: base `frontend`, `npm run build`, publish `dist`,
Node 22, fallback de SPA e headers de segurança. `VITE_SUPABASE_URL` já está definida lá.

1. Acesse <https://app.netlify.com> e entre com **GitHub**.
2. **Add new project → Import an existing project → GitHub → `aloisiojuniordev-hub/ipaj-gaming`**, branch **`main`**.
   Os campos de build vêm do `netlify.toml`. Não altere.
3. **Environment variables → Add a variable:** `VITE_SUPABASE_PUBLISHABLE_KEY` = a chave do passo 1.2.
4. **Deploy.** Cada push na `main` publica sozinho, e cada PR ganha um *Deploy Preview*.

Variáveis `VITE_` são embutidas no build. Depois de criar ou alterar uma delas, rode
**Deploys → Trigger deploy → Deploy project**.

Sem a chave, o site funciona: catálogo, recomendações e Laboratório. Login e pedidos mostram um aviso
de configuração.

---

## 3. Conferência no site publicado

- [ ] `/catalogo`, `/carrinho` e `/laboratorio` abrem e funcionam ao recarregar (F5);
- [ ] PS5 no carrinho → DualSense Extra (72%), EA FC 25 (62%) e Headset Pulse 3D (56%);
- [ ] Laboratório mostra 394 regras e Hit rate@3 de 58,72%;
- [ ] cadastro e login funcionam;
- [ ] checkout cria o pedido. Confira em Supabase → Table Editor → `orders`;
- [ ] o pedido aparece em **Perfil**, e em outra conta não aparece.

Depois, registre a URL na seção *Demonstração* do README.

## Variáveis de ambiente

| Variável | Onde | Obrigatória | Valor |
|---|---|---|---|
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Netlify | para login e pedidos | `sb_publishable_...` (pública) |
| `VITE_SUPABASE_URL` | `netlify.toml` | já definida | `https://lvukeuyexxewmnslucwj.supabase.co` |

A API FastAPI em `backend/` é só para uso local e tem as suas variáveis em `backend/.env.example`.
Não a aponte para o banco do Supabase: ela revoga os privilégios públicos na inicialização.
