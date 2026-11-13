import { useState } from "react";
import { BarChart } from "../../components/charts/BarChart";
import { RecommendationPanel } from "../../components/recommendations/RecommendationPanel";
import { ErrorMessage, Loading, Stat } from "../../components/ui/Status";
import { useAsync } from "../../hooks/useAsync";
import { useCartRecommendations } from "../../hooks/useCartRecommendations";
import { api } from "../../services/api";
import { formatNum, formatPct } from "../../utils/format";

const names = (ps: { name: string }[]) => ps.map((p) => p.name).join(" + ");

export default function Laboratory() {
  const [sortBy, setSortBy] = useState("lift");
  const [minConf, setMinConf] = useState(0.3);
  const [sim, setSim] = useState<string[]>(["P001"]);

  const metrics = useAsync(() => api.metrics(), []);
  const rules = useAsync(() => api.rules({ sort_by: sortBy, limit: 15, min_confidence: minConf }), [sortBy, minConf]);
  const itemsets = useAsync(() => api.itemsets({ min_size: 2, limit: 10 }), []);
  const products = useAsync(() => api.products(), []);
  const simRecs = useCartRecommendations(sim, 5);

  const m = metrics.data;
  const ev = m?.evaluation;

  return (
    <>
      <h1>Laboratório IA</h1>
      <p className="lead">Resultados reais do treinamento do Apriori (mlxtend) e da avaliação no conjunto de teste (20%).</p>

      {metrics.loading && <Loading />}
      {metrics.error && <ErrorMessage message={metrics.error} />}
      {m && (
        <section aria-labelledby="treino">
          <h2 id="treino">Treinamento</h2>
          <div className="grid grid--stats">
            <Stat value={m.training.n_train_transactions} label="transações de treino" />
            <Stat value={m.training.n_test_transactions} label="transações de teste" />
            <Stat value={m.training.n_itemsets} label="itemsets frequentes" />
            <Stat value={m.training.n_rules} label="regras geradas" />
          </div>
          <p className="muted" style={{ marginTop: ".8rem" }}>
            Parâmetros: suporte mínimo {formatPct(m.training.parameters.min_support)}, confiança mínima{" "}
            {formatPct(m.training.parameters.min_confidence)}, lift mínimo {formatNum(m.training.parameters.min_lift, 1)},
            tamanho máximo do itemset {m.training.parameters.max_len}. Semente {m.training.seed}.
          </p>
        </section>
      )}

      {ev && (
        <section className="section" aria-labelledby="avaliacao">
          <h2 id="avaliacao">Avaliação (teste)</h2>
          <div className="grid grid--stats">
            <Stat value={`${formatNum(ev.hit_rate_at_k_all_carts_pct)}%`} label={`Hit rate @${ev.top_k} (Apriori)`} />
            <Stat value={`${formatNum(ev.baseline_popularity_hit_rate_at_k_pct)}%`} label={`Hit rate @${ev.top_k} (popularidade)`} />
            <Stat value={`${formatNum(ev.cart_coverage_pct)}%`} label="cobertura de carrinhos" />
            <Stat value={`${formatNum(ev.item_coverage_pct)}%`} label="cobertura de itens" />
          </div>
          <div className="table-wrap card" style={{ marginTop: "1rem" }}>
            <table>
              <caption className="sr-only">Comparação treino e teste das regras</caption>
              <thead><tr><th>Métrica média das regras</th><th className="num">Treino</th><th className="num">Teste</th></tr></thead>
              <tbody>
                {(["support", "confidence", "lift"] as const).map((k) => (
                  <tr key={k}>
                    <td>{{ support: "Suporte", confidence: "Confiança", lift: "Lift" }[k]}</td>
                    <td className="num">{formatNum(ev.rule_quality.train[k], 4)}</td>
                    <td className="num">{formatNum(ev.rule_quality.test[k], 4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="section" aria-labelledby="simulador">
        <h2 id="simulador">Simulador de carrinho</h2>
        <div className="two-col">
          <div className="card">
            <p className="muted">Marque produtos e veja quais regras o IPAJ CORE ativa.</p>
            {products.data && (
              <fieldset style={{ border: 0, padding: 0, margin: 0, maxHeight: 360, overflowY: "auto" }}>
                <legend className="sr-only">Produtos do carrinho simulado</legend>
                {products.data.map((p) => (
                  <label key={p.id} style={{ display: "flex", gap: ".5rem", fontWeight: 400 }}>
                    <input type="checkbox" style={{ width: "auto" }} checked={sim.includes(p.id)}
                      onChange={(e) => setSim((s) => (e.target.checked ? [...s, p.id] : s.filter((x) => x !== p.id)))} />
                    {p.name}
                  </label>
                ))}
              </fieldset>
            )}
          </div>
          <RecommendationPanel title="Recomendações do simulador" data={simRecs.data} loading={simRecs.loading} error={simRecs.error} />
        </div>
      </section>

      <section className="section" aria-labelledby="regras">
        <h2 id="regras">Regras de associação</h2>
        <div className="toolbar">
          <div>
            <label htmlFor="sort">Ordenar por</label>
            <select id="sort" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="lift">Lift</option><option value="confidence">Confiança</option><option value="support">Suporte</option>
            </select>
          </div>
          <div>
            <label htmlFor="minconf">Confiança mínima: {formatPct(minConf)}</label>
            <input id="minconf" type="range" min={0.3} max={0.9} step={0.05} value={minConf}
              onChange={(e) => setMinConf(Number(e.target.value))} />
          </div>
        </div>
        {rules.loading && <Loading />}
        {rules.error && <ErrorMessage message={rules.error} />}
        {rules.data && (
          <div className="card table-wrap">
            <table>
              <thead><tr><th>Se o carrinho tem</th><th>Então recomenda</th><th className="num">Suporte</th><th className="num">Confiança</th><th className="num">Lift</th></tr></thead>
              <tbody>
                {rules.data.map((r, i) => (
                  <tr key={i}>
                    <td>{names(r.antecedents)}</td><td>{names(r.consequents)}</td>
                    <td className="num">{formatPct(r.support, 1)}</td>
                    <td className="num">{formatPct(r.confidence, 1)}</td>
                    <td className="num">{formatNum(r.lift)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {rules.data.length === 0 && <p className="muted">Nenhuma regra com esses filtros.</p>}
          </div>
        )}
      </section>

      <section className="section card" aria-labelledby="itemsets">
        <h2 id="itemsets" className="sr-only">Itemsets frequentes</h2>
        {itemsets.data && (
          <BarChart title="Top 10 itemsets frequentes (2+ itens), por suporte"
            bars={itemsets.data.map((s) => ({ label: names(s.items), value: s.support, display: formatPct(s.support, 1) }))} />
        )}
        {itemsets.error && <ErrorMessage message={itemsets.error} />}
      </section>
    </>
  );
}
