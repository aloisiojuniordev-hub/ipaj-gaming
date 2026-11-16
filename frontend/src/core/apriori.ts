/**
 * IPAJ CORE no navegador: consulta às regras de associação geradas pelo Apriori.
 *
 * A MINERAÇÃO não acontece aqui. As regras vêm de ml/train_apriori.py (Python + mlxtend),
 * exportadas sem alteração por scripts/export_static.py para src/data/rules.json.
 * Este arquivo é a tradução fiel de ml/recommendation_engine.py; o teste
 * src/test/apriori.test.ts compara as saídas com as do motor Python.
 */
import rulesData from "../data/rules.json";
import itemsetsData from "../data/itemsets.json";

export interface AprioriRule {
  antecedents: string[];
  consequents: string[];
  support: number;
  antecedent_support: number;
  consequent_support: number;
  confidence: number;
  lift: number;
  leverage: number;
}

export interface AprioriItemset {
  items: string[];
  support: number;
}

export interface RawRecommendation {
  product_id: string;
  confidence: number;
  lift: number;
  support: number;
  because: string[];
}

export const RULES = rulesData as AprioriRule[];
export const ITEMSETS = itemsetsData as AprioriItemset[];

const cmpStr = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);

/** Comparação lexicográfica de listas, como em Python. */
export function cmpList(a: string[], b: string[]): number {
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const c = cmpStr(a[i], b[i]);
    if (c !== 0) return c;
  }
  return a.length - b.length;
}

/**
 * Recomenda itens ausentes do carrinho. Para cada candidato vale a melhor regra aplicável
 * (maior confiança, desempate por lift); ordem final: confiança, lift, id.
 * Sem regra aplicável, retorna lista vazia (sem fallback inventado).
 */
export function recommend(cart: string[], limit = 5, rules: AprioriRule[] = RULES): RawRecommendation[] {
  const cartSet = new Set(cart);
  const best = new Map<string, AprioriRule>();
  for (const rule of rules) {
    const consequent = rule.consequents[0];
    if (cartSet.has(consequent) || !rule.antecedents.every((a) => cartSet.has(a))) continue;
    const current = best.get(consequent);
    if (!current || rule.confidence > current.confidence
        || (rule.confidence === current.confidence && rule.lift > current.lift)) {
      best.set(consequent, rule);
    }
  }
  return [...best.entries()]
    .sort(([ia, a], [ib, b]) => b.confidence - a.confidence || b.lift - a.lift || cmpStr(ia, ib))
    .slice(0, limit)
    .map(([id, r]) => ({ product_id: id, confidence: r.confidence, lift: r.lift, support: r.support, because: r.antecedents }));
}

export type RuleSort = "lift" | "confidence" | "support";

export function topRules(sortBy: RuleSort = "lift", rules: AprioriRule[] = RULES): AprioriRule[] {
  return [...rules].sort((a, b) => b[sortBy] - a[sortBy]
    || cmpList(a.antecedents, b.antecedents) || cmpList(a.consequents, b.consequents));
}

const pct = (v: number) => `${Math.round(v * 100)}%`;
const dec = (v: number, places = 2) => v.toFixed(places).replace(".", ",");

export function explain(antecedentNames: string[], consequentName: string, confidence: number, lift: number): string {
  return `${pct(confidence)} de quem levou ${antecedentNames.join(" + ")} também levou ${consequentName} `
    + `(lift ${dec(lift)}: ${dec(lift, 1)}x a chance esperada ao acaso).`;
}
