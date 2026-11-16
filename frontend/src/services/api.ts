/**
 * Camada de dados do frontend (sem servidor Python em produção).
 *
 * - Catálogo, métricas, regras e itemsets: dados estáticos exportados dos artefatos REAIS
 *   do Apriori (scripts/export_static.py).
 * - Recomendações: IPAJ CORE no navegador (src/core/apriori.ts), consultando essas regras.
 * - Login: Supabase Auth. Pedidos: função create_order no PostgreSQL do Supabase.
 *
 * As funções mantêm a mesma forma da antiga API FastAPI, então as páginas não mudaram.
 */
import catalogData from "../data/catalog.json";
import metricsData from "../data/metrics.json";
import { explain, ITEMSETS, recommend as coreRecommend, topRules, type RuleSort } from "../core/apriori";
import type { Itemset, Metrics, Order, Product, RecommendationResponse, Rule } from "../types";
import { getSupabase, SUPABASE_NOT_CONFIGURED } from "./supabase";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

const CATALOG = catalogData as Product[];
const BY_ID = new Map(CATALOG.map((p) => [p.id, p]));
const resolve = (ids: string[]) => ids.map((id) => BY_ID.get(id)).filter((p): p is Product => !!p);

function buildRecommendations(cart: string[], limit: number): RecommendationResponse {
  const unique = [...new Set(cart)];
  const unknown = unique.filter((id) => !BY_ID.has(id));
  if (unknown.length) throw new ApiError(422, `Produtos inexistentes no carrinho: ${unknown.join(", ")}`);
  const recommendations = coreRecommend(unique, limit).flatMap((r) => {
    const product = BY_ID.get(r.product_id);
    if (!product) return [];
    const because = resolve(r.because);
    return [{
      product, confidence: r.confidence, lift: r.lift, support: r.support, because,
      explanation: explain(because.map((p) => p.name), product.name, r.confidence, r.lift),
    }];
  });
  let message: string | null = null;
  if (!unique.length) message = "Adicione produtos ao carrinho para ativar o IPAJ CORE.";
  else if (!recommendations.length) message = "Nenhuma regra de associação cobre esta combinação de produtos.";
  return { cart: unique, recommendations, message };
}

function requireSupabase() {
  const sb = getSupabase();
  if (!sb) throw new ApiError(503, SUPABASE_NOT_CONFIGURED);
  return sb;
}

type RawOrder = Omit<Order, "is_guest" | "items"> & {
  auth_user_id?: string | null;
  is_guest?: boolean;
  items?: Order["items"];
  order_items?: Order["items"];
};

const toOrder = (o: RawOrder): Order => ({
  id: o.id, status: o.status, total: o.total, created_at: o.created_at,
  is_guest: o.is_guest ?? !o.auth_user_id,
  items: o.items ?? o.order_items ?? [],
});

export const api = {
  products: async (p: { category?: string; q?: string; sort?: string } = {}): Promise<Product[]> => {
    const q = p.q?.trim().toLowerCase();
    const list = CATALOG.filter((x) => (!p.category || x.category === p.category)
      && (!q || x.name.toLowerCase().includes(q)));
    if (p.sort === "price_asc") return list.sort((a, b) => Number(a.price) - Number(b.price));
    if (p.sort === "price_desc") return list.sort((a, b) => Number(b.price) - Number(a.price));
    return list.sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
  },

  categories: async (): Promise<string[]> =>
    [...new Set(CATALOG.map((p) => p.category))].sort((a, b) => a.localeCompare(b, "pt-BR")),

  product: async (id: string): Promise<Product> => {
    const product = BY_ID.get(id);
    if (!product) throw new ApiError(404, "Produto não encontrado.");
    return product;
  },

  recommend: async (cart: string[], limit = 4) => buildRecommendations(cart, limit),

  boughtTogether: async (id: string, limit = 4) => {
    if (!BY_ID.has(id)) throw new ApiError(404, "Produto não encontrado.");
    return buildRecommendations([id], limit);
  },

  metrics: async () => metricsData as Metrics,

  rules: async (p: { sort_by?: string; limit?: number; min_confidence?: number; min_lift?: number; product_id?: string }) => {
    const sortBy = (["lift", "confidence", "support"].includes(p.sort_by ?? "") ? p.sort_by : "lift") as RuleSort;
    const limit = Math.min(Math.max(p.limit ?? 20, 1), 500);
    const selected = topRules(sortBy).filter((r) => r.confidence >= (p.min_confidence ?? 0)
      && r.lift >= (p.min_lift ?? 0)
      && (!p.product_id || [...r.antecedents, ...r.consequents].includes(p.product_id))).slice(0, limit);
    return selected.map((r): Rule => ({
      antecedents: resolve(r.antecedents), consequents: resolve(r.consequents),
      support: r.support, confidence: r.confidence, lift: r.lift, leverage: r.leverage,
    }));
  },

  itemsets: async (p: { min_size?: number; limit?: number }) =>
    ITEMSETS.filter((i) => i.items.length >= (p.min_size ?? 1))
      .sort((a, b) => b.support - a.support || a.items.join().localeCompare(b.items.join()))
      .slice(0, p.limit ?? 30)
      .map((i): Itemset => ({ items: resolve(i.items), support: i.support })),

  createOrder: async (items: { product_id: string; quantity: number; from_recommendation: boolean }[],
                      guest_label?: string): Promise<Order> => {
    const { data, error } = await requireSupabase().rpc("create_order", {
      p_items: items, p_guest_label: guest_label ?? null,
    });
    if (error) throw new ApiError(400, error.message);
    return toOrder(data as RawOrder);
  },

  myOrders: async (): Promise<Order[]> => {
    const { data, error } = await requireSupabase().from("orders")
      .select("id, status, total, created_at, auth_user_id, order_items(product_id, quantity, unit_price, from_recommendation)")
      .order("created_at", { ascending: false });
    if (error) throw new ApiError(400, error.message);
    return (data as RawOrder[]).map(toOrder);
  },
};
