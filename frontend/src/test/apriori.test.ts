import { describe, expect, it } from "vitest";
import { recommend, RULES, topRules, type AprioriRule } from "../core/apriori";
import { api } from "../services/api";
import expected from "./fixtures/expected_recommendations.json";

type Case = { cart: string[]; recs: { product_id: string; confidence: number; lift: number; because: string[] }[] };

describe("IPAJ CORE no navegador = motor Python", () => {
  it("usa as 394 regras reais do Apriori", () => {
    expect(RULES).toHaveLength(394);
  });

  it.each((expected as Case[]).map((c) => [c.cart.join("+"), c] as const))(
    "carrinho %s produz as mesmas recomendações do Python", (_name, c) => {
      const got = recommend(c.cart, 5).map(({ product_id, confidence, lift, because }) => ({ product_id, confidence, lift, because }));
      expect(got).toEqual(c.recs);
    });

  it("nunca recomenda o que já está no carrinho e não inventa sem regra", () => {
    const rules: AprioriRule[] = [
      { antecedents: ["A"], consequents: ["B"], support: 0.2, antecedent_support: 0.25, consequent_support: 0.3, confidence: 0.8, lift: 2, leverage: 0.1 },
    ];
    expect(recommend(["A", "B"], 5, rules)).toEqual([]);
    expect(recommend(["Z"], 5, rules)).toEqual([]);
  });

  it("ordena regras por lift decrescente", () => {
    const lifts = topRules("lift").slice(0, 20).map((r) => r.lift);
    expect(lifts).toEqual([...lifts].sort((a, b) => b - a));
  });
});

describe("api estática", () => {
  it("monta recomendações com produtos e explicação", async () => {
    const r = await api.recommend(["P001"], 3);
    expect(r.recommendations.map((x) => x.product.id)).toEqual(["P014", "P004", "P018"]);
    expect(r.recommendations[0].explanation).toMatch(/^72% de quem levou PlayStation 5 Slim/);
  });

  it("explica quando nenhuma regra se aplica", async () => {
    const r = await api.recommend(["P012"]);
    expect(r.recommendations).toEqual([]);
    expect(r.message).toMatch(/Nenhuma regra/);
  });

  it("rejeita produto inexistente e filtra o catálogo", async () => {
    await expect(api.recommend(["NOPE"])).rejects.toThrow(/inexistentes/);
    expect((await api.products({ category: "Consoles" })).map((p) => p.id).sort()).toEqual(["P001", "P002", "P003"]);
    expect(await api.products()).toHaveLength(50);
  });

  it("filtra regras do Laboratório", async () => {
    const rules = await api.rules({ sort_by: "confidence", limit: 5, min_confidence: 0.9 });
    expect(rules).toHaveLength(5);
    expect(rules.every((r) => r.confidence >= 0.9)).toBe(true);
  });

  it("sem chave do Supabase, pedidos dão erro claro (não fingem sucesso)", async () => {
    await expect(api.createOrder([{ product_id: "P001", quantity: 1, from_recommendation: false }]))
      .rejects.toThrow(/VITE_SUPABASE_PUBLISHABLE_KEY/);
  });
});
