# Migrações

Migrações SQL sequenciais e imutáveis. Aplique em ordem.

| Arquivo | Descrição |
|---|---|
| `001_initial_schema.sql` | Tabelas `products`, `users`, `orders`, `order_items`, índices, restrições e RLS. |

Aplicar com psql (o `\ir` resolve o caminho relativo ao arquivo):

```bash
psql "$DATABASE_URL" -f database/migrations/001_initial_schema.sql
```

No SQL Editor do Supabase, `\ir` não é suportado: cole o conteúdo de `database/schema.sql`.
