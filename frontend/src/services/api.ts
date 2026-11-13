import type {
  Itemset, Metrics, Order, Product, RecommendationResponse, Rule, User,
} from "../types";

const BASE = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const TOKEN_KEY = "ipaj.token";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body) headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Não foi possível conectar à API. Verifique se o backend está no ar.");
  }
  if (!res.ok) {
    let detail = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch { /* corpo não-JSON */ }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const qs = (params: Record<string, string | number | undefined>) => {
  const s = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && s.set(k, String(v)));
  const str = s.toString();
  return str ? `?${str}` : "";
};

type AuthResponse = { access_token: string; user: User };

export const api = {
  health: () => request<{ status: string }>("/health"),
  products: (p: { category?: string; q?: string; sort?: string } = {}) =>
    request<Product[]>(`/api/products${qs(p)}`),
  categories: () => request<string[]>("/api/products/categories"),
  product: (id: string) => request<Product>(`/api/products/${encodeURIComponent(id)}`),
  recommend: (cart: string[], limit = 4) =>
    request<RecommendationResponse>("/api/recommendations", {
      method: "POST", body: JSON.stringify({ cart, limit }),
    }),
  boughtTogether: (id: string, limit = 4) =>
    request<RecommendationResponse>(`/api/recommendations/product/${encodeURIComponent(id)}${qs({ limit })}`),
  metrics: () => request<Metrics>("/api/laboratory/metrics"),
  rules: (p: { sort_by?: string; limit?: number; min_confidence?: number; min_lift?: number; product_id?: string }) =>
    request<Rule[]>(`/api/laboratory/rules${qs(p)}`),
  itemsets: (p: { min_size?: number; limit?: number }) => request<Itemset[]>(`/api/laboratory/itemsets${qs(p)}`),
  register: (name: string, email: string, password: string) =>
    request<AuthResponse>("/api/users/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  login: (email: string, password: string) =>
    request<AuthResponse>("/api/users/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request<User>("/api/users/me"),
  createOrder: (items: { product_id: string; quantity: number; from_recommendation: boolean }[], guest_label?: string) =>
    request<Order>("/api/orders", { method: "POST", body: JSON.stringify({ items, guest_label }) }),
  myOrders: () => request<Order[]>("/api/orders/me"),
};
