-- Migração 002 — retirar privilégios das roles públicas do Supabase (anon, authenticated).
-- Não destrutiva e idempotente: não altera dados nem estrutura, só permissões.
-- Defesa em profundidade sobre o RLS da 001: mesmo que alguém crie uma política por engano,
-- a Data API pública (chave anon) continua sem acesso às tabelas do app.
-- O backend aplica o mesmo bloco em toda inicialização (connection.REVOKE_PUBLIC_ROLES_SQL).

DO $$
DECLARE r text;
BEGIN
  FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      EXECUTE 'REVOKE ALL ON TABLE products, users, orders, order_items FROM ' || quote_ident(r);
    END IF;
  END LOOP;
END $$;
