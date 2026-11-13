-- Migração 001 — schema inicial da IPAJ Gaming.
-- Autocontida (sem \ir): roda no SQL Editor do Supabase, no psql e em ferramentas de migração.
-- O corpo abaixo é idêntico a database/schema.sql (verificado por backend/tests/test_database.py).
-- Novas alterações devem ser criadas como 002_<descricao>.sql, 003_..., sem editar esta.

BEGIN;

CREATE TABLE IF NOT EXISTS products (
    id          VARCHAR(10)    PRIMARY KEY,
    name        VARCHAR(150)   NOT NULL,
    category    VARCHAR(50)    NOT NULL,
    price       NUMERIC(10, 2) NOT NULL CONSTRAINT ck_products_price CHECK (price >= 0),
    description TEXT           NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_products_category ON products (category);

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL       PRIMARY KEY,
    name          VARCHAR(120) NOT NULL,
    email         VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS orders (
    id          SERIAL         PRIMARY KEY,
    user_id     INTEGER        NULL REFERENCES users (id) ON DELETE SET NULL,
    guest_label VARCHAR(60)    NULL,
    status      VARCHAR(20)    NOT NULL DEFAULT 'demo_confirmed'
                CONSTRAINT ck_orders_status CHECK (status IN ('demo_confirmed', 'demo_cancelled')),
    total       NUMERIC(12, 2) NOT NULL CONSTRAINT ck_orders_total CHECK (total >= 0),
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_orders_user_id ON orders (user_id);

CREATE TABLE IF NOT EXISTS order_items (
    id                  SERIAL         PRIMARY KEY,
    order_id            INTEGER        NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_id          VARCHAR(10)    NOT NULL REFERENCES products (id),
    quantity            INTEGER        NOT NULL CONSTRAINT ck_order_items_qty CHECK (quantity > 0),
    unit_price          NUMERIC(10, 2) NOT NULL CONSTRAINT ck_order_items_price CHECK (unit_price >= 0),
    from_recommendation BOOLEAN        NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items (order_id);
CREATE INDEX IF NOT EXISTS ix_order_items_product_id ON order_items (product_id);

-- Segurança Supabase: o frontend NUNCA acessa o banco diretamente; somente o backend
-- (conexão com o usuário postgres via DATABASE_URL). Habilitar RLS sem políticas bloqueia
-- as roles públicas (anon/authenticated) da API REST automática do Supabase.
ALTER TABLE products    ENABLE ROW LEVEL SECURITY;
ALTER TABLE users       ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders      ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

COMMIT;
