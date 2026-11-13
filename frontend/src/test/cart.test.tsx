import { describe, expect, it } from "vitest";
import { cartReducer } from "../contexts/CartContext";
import type { Product } from "../types";
import { formatPct, formatPrice } from "../utils/format";

const ps5: Product = { id: "P001", name: "PS5", category: "Consoles", price: "4499.00", description: "" };
const ctrl: Product = { id: "P014", name: "DualSense", category: "Controles", price: "449.00", description: "" };

describe("cartReducer", () => {
  it("adiciona, incrementa e marca origem da recomendação", () => {
    let s = cartReducer([], { type: "add", product: ps5 });
    s = cartReducer(s, { type: "add", product: ps5 });
    s = cartReducer(s, { type: "add", product: ctrl, fromRecommendation: true });
    expect(s).toHaveLength(2);
    expect(s[0].quantity).toBe(2);
    expect(s[1].fromRecommendation).toBe(true);
  });

  it("limita quantidade a 20 e remove com quantidade 0", () => {
    let s = cartReducer([], { type: "add", product: ps5 });
    s = cartReducer(s, { type: "setQty", id: "P001", quantity: 99 });
    expect(s[0].quantity).toBe(20);
    s = cartReducer(s, { type: "setQty", id: "P001", quantity: 0 });
    expect(s).toHaveLength(0);
  });

  it("remove e limpa", () => {
    let s = cartReducer([], { type: "add", product: ps5 });
    s = cartReducer(s, { type: "add", product: ctrl });
    expect(cartReducer(s, { type: "remove", id: "P001" }).map((i) => i.product.id)).toEqual(["P014"]);
    expect(cartReducer(s, { type: "clear" })).toEqual([]);
  });
});

describe("format", () => {
  it("formata preço em BRL e percentuais", () => {
    expect(formatPrice("4499.00").replace(/\s/g, " ")).toBe("R$ 4.499,00");
    expect(formatPct(0.6383, 1)).toBe("63,8%");
  });
});
