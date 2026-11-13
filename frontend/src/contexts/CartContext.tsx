import { createContext, useCallback, useEffect, useMemo, useReducer, type ReactNode } from "react";
import type { CartItem, Product } from "../types";

const STORAGE_KEY = "ipaj.cart";

type Action =
  | { type: "add"; product: Product; fromRecommendation?: boolean }
  | { type: "setQty"; id: string; quantity: number }
  | { type: "remove"; id: string }
  | { type: "clear" };

export function cartReducer(state: CartItem[], action: Action): CartItem[] {
  switch (action.type) {
    case "add": {
      const existing = state.find((i) => i.product.id === action.product.id);
      if (existing) {
        return state.map((i) => (i.product.id === action.product.id
          ? { ...i, quantity: Math.min(i.quantity + 1, 20) } : i));
      }
      return [...state, { product: action.product, quantity: 1, fromRecommendation: !!action.fromRecommendation }];
    }
    case "setQty":
      if (action.quantity <= 0) return state.filter((i) => i.product.id !== action.id);
      return state.map((i) => (i.product.id === action.id ? { ...i, quantity: Math.min(action.quantity, 20) } : i));
    case "remove":
      return state.filter((i) => i.product.id !== action.id);
    case "clear":
      return [];
  }
}

function load(): CartItem[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as CartItem[]) : [];
  } catch {
    return [];
  }
}

export interface CartContextValue {
  items: CartItem[];
  count: number;
  total: number;
  productIds: string[];
  add: (p: Product, fromRecommendation?: boolean) => void;
  setQty: (id: string, quantity: number) => void;
  remove: (id: string) => void;
  clear: () => void;
}

export const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, dispatch] = useReducer(cartReducer, undefined, load);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const add = useCallback((product: Product, fromRecommendation?: boolean) =>
    dispatch({ type: "add", product, fromRecommendation }), []);
  const setQty = useCallback((id: string, quantity: number) => dispatch({ type: "setQty", id, quantity }), []);
  const remove = useCallback((id: string) => dispatch({ type: "remove", id }), []);
  const clear = useCallback(() => dispatch({ type: "clear" }), []);

  const value = useMemo<CartContextValue>(() => ({
    items,
    count: items.reduce((s, i) => s + i.quantity, 0),
    total: items.reduce((s, i) => s + Number(i.product.price) * i.quantity, 0),
    productIds: items.map((i) => i.product.id),
    add, setQty, remove, clear,
  }), [items, add, setQty, remove, clear]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}
