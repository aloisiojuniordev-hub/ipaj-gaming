# Migrações

Migrações SQL sequenciais e imutáveis. Aplique em ordem.

| Arquivo | Descrição |
|---|---|
| `001_initial_schema.sql` | Tabelas `products`, `users`, `orders`, `order_items`, índices, restrições e RLS. |
| `002_revoke_public_roles.sql` | Retira das roles `anon`/`authenticated` qualquer privilégio nas tabelas (não destrutiva, idempotente). |

Cada arquivo é autocontido (não usa `\ir`) e roda tanto no SQL Editor do Supabase
(colar e executar) quanto no psql:

```bash
psql "$DATABASE_URL" -f database/migrations/001_initial_schema.sql
```

O corpo da `001` é idêntico a `database/schema.sql`. O teste `backend/tests/test_database.py`
falha se os dois divergirem.

## Relação com o backend

Na inicialização, o backend executa `ensure_schema()`, que cria as tabelas que faltarem e
ativa RLS **na mesma transação**. Por isso as tabelas nunca ficam expostas à Data API
pública do Supabase, mesmo se o backend subir antes desta migração.

O `ensure_schema()` **não altera** tabelas existentes. Mudanças de schema (colunas novas etc.)
devem virar uma nova migração `002_...sql` e ser espelhadas em `backend/app/database/models.py`.

## Integração GitHub do Supabase

Esta pasta **não** é lida pela integração GitHub/Branching do Supabase, que procura
`supabase/migrations/<timestamp>_nome.sql`. Neste projeto o schema é aplicado manualmente
(SQL Editor) ou pelo backend. Mantenha o Branching desativado, ou crie a pasta `supabase/`
via `supabase init` se quiserem adotá-lo.
