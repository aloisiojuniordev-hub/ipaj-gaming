-- Migração 003 — acesso do frontend (Netlify) direto ao Supabase, sem servidor Python.
-- Não destrutiva e idempotente: só ADICIONA coluna, índice, permissões, políticas e uma função.
-- Não apaga dados, tabelas nem políticas.
--
-- Modelo de segurança:
--   products     -> leitura pública (catálogo).
--   orders/items -> usuário autenticado (Supabase Auth) LÊ apenas os próprios pedidos (RLS).
--   escrita      -> NINGUÉM grava direto nas tabelas. Pedidos só via create_order(), que
--                   calcula os preços no banco (o navegador não define preço nem dono).
--   users        -> continua fechada (tabela do backend local; o login agora é o Supabase Auth).

BEGIN;

-- Dono do pedido no Supabase Auth (NULL = visitante). user_id (INTEGER) segue para o backend local.
ALTER TABLE orders ADD COLUMN IF NOT EXISTS auth_user_id uuid NULL REFERENCES auth.users (id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_orders_auth_user_id ON orders (auth_user_id);

-- Catálogo: leitura pública.
GRANT SELECT ON products TO anon, authenticated;

-- Pedidos: somente leitura, e só para usuários logados (filtrada pelas políticas abaixo).
GRANT SELECT ON orders, order_items TO authenticated;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'products'
                 AND policyname = 'products_read_all') THEN
    CREATE POLICY products_read_all ON products FOR SELECT TO anon, authenticated USING (true);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'orders'
                 AND policyname = 'orders_read_own') THEN
    CREATE POLICY orders_read_own ON orders FOR SELECT TO authenticated
      USING (auth_user_id = (SELECT auth.uid()));
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'order_items'
                 AND policyname = 'order_items_read_own') THEN
    CREATE POLICY order_items_read_own ON order_items FOR SELECT TO authenticated
      USING (EXISTS (SELECT 1 FROM orders o
                     WHERE o.id = order_items.order_id AND o.auth_user_id = (SELECT auth.uid())));
  END IF;
END $$;

-- Cria um pedido demonstrativo. Roda com os privilégios do dono (SECURITY DEFINER), com
-- search_path vazio (evita sequestro de nomes). Valida a entrada, usa SEMPRE o preço do banco
-- e vincula o pedido ao usuário do token (auth.uid()), ou NULL para visitante.
CREATE OR REPLACE FUNCTION public.create_order(p_items jsonb, p_guest_label text DEFAULT NULL)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
  v_uid uuid := auth.uid();
  v_item jsonb;
  v_qty numeric;
  v_missing text;
  v_order_id integer;
BEGIN
  IF p_items IS NULL OR jsonb_typeof(p_items) IS DISTINCT FROM 'array'
     OR jsonb_array_length(p_items) NOT BETWEEN 1 AND 50 THEN
    RAISE EXCEPTION 'O pedido precisa ter de 1 a 50 itens.' USING ERRCODE = '22023';
  END IF;

  FOR v_item IN SELECT value FROM jsonb_array_elements(p_items) LOOP
    IF jsonb_typeof(v_item) IS DISTINCT FROM 'object'
       OR jsonb_typeof(v_item -> 'product_id') IS DISTINCT FROM 'string'
       OR jsonb_typeof(v_item -> 'quantity') IS DISTINCT FROM 'number'
       OR (v_item ? 'from_recommendation'
           AND jsonb_typeof(v_item -> 'from_recommendation') IS DISTINCT FROM 'boolean') THEN
      RAISE EXCEPTION 'Item de pedido inválido.' USING ERRCODE = '22023';
    END IF;
    v_qty := (v_item ->> 'quantity')::numeric;
    IF v_qty <> trunc(v_qty) OR v_qty NOT BETWEEN 1 AND 20 THEN
      RAISE EXCEPTION 'Quantidade deve ser um inteiro de 1 a 20.' USING ERRCODE = '22023';
    END IF;
  END LOOP;

  IF p_guest_label IS NOT NULL AND char_length(p_guest_label) > 60 THEN
    RAISE EXCEPTION 'Apelido deve ter no máximo 60 caracteres.' USING ERRCODE = '22023';
  END IF;

  SELECT string_agg(DISTINCT e.value ->> 'product_id', ', ') INTO v_missing
  FROM jsonb_array_elements(p_items) e
  WHERE NOT EXISTS (SELECT 1 FROM public.products p WHERE p.id = e.value ->> 'product_id');
  IF v_missing IS NOT NULL THEN
    RAISE EXCEPTION 'Produtos inexistentes: %', v_missing USING ERRCODE = '22023';
  END IF;

  INSERT INTO public.orders (user_id, auth_user_id, guest_label, status, total)
  VALUES (NULL, v_uid,
          CASE WHEN v_uid IS NULL THEN nullif(btrim(p_guest_label), '') END,
          'demo_confirmed', 0)
  RETURNING id INTO v_order_id;

  -- Itens repetidos são somados; o preço vem da tabela products.
  INSERT INTO public.order_items (order_id, product_id, quantity, unit_price, from_recommendation)
  SELECT v_order_id, a.product_id, a.quantity, p.price, a.from_rec
  FROM (SELECT e.value ->> 'product_id' AS product_id,
               sum((e.value ->> 'quantity')::int)::int AS quantity,
               bool_or(coalesce((e.value -> 'from_recommendation') = 'true'::jsonb, false)) AS from_rec
        FROM jsonb_array_elements(p_items) e
        GROUP BY 1) a
  JOIN public.products p ON p.id = a.product_id;

  UPDATE public.orders o
  SET total = (SELECT coalesce(sum(i.unit_price * i.quantity), 0)
               FROM public.order_items i WHERE i.order_id = v_order_id)
  WHERE o.id = v_order_id;

  RETURN (
    SELECT jsonb_build_object(
      'id', o.id, 'status', o.status, 'total', o.total, 'created_at', o.created_at,
      'is_guest', o.auth_user_id IS NULL,
      'items', (SELECT jsonb_agg(jsonb_build_object(
                         'product_id', i.product_id, 'quantity', i.quantity,
                         'unit_price', i.unit_price, 'from_recommendation', i.from_recommendation)
                       ORDER BY i.product_id)
                FROM public.order_items i WHERE i.order_id = o.id))
    FROM public.orders o WHERE o.id = v_order_id);
END $$;

REVOKE ALL ON FUNCTION public.create_order(jsonb, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.create_order(jsonb, text) TO anon, authenticated;

COMMIT;
