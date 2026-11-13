import { Link } from "react-router-dom";
import { useCart } from "../../hooks/useCart";
import type { RecommendationResponse } from "../../types";
import { formatNum, formatPct, formatPrice } from "../../utils/format";
import { ProductImage } from "../products/ProductImage";
import { ErrorMessage, Loading } from "../ui/Status";

interface Props {
  title?: string;
  data: RecommendationResponse | null;
  loading: boolean;
  error: string | null;
}

/** Painel do IPAJ CORE: mostra recomendações e a regra Apriori que as justifica. */
export function RecommendationPanel({ title = "IPAJ CORE recomenda", data, loading, error }: Props) {
  const { add } = useCart();
  return (
    <section className="card core-panel" aria-labelledby="core-title" aria-live="polite">
      <h2 id="core-title" className="core-title"><span className="core-dot" aria-hidden="true" />{title}</h2>
      {loading && <Loading label="Analisando regras de associação..." />}
      {error && <ErrorMessage message={error} />}
      {!loading && !error && data && data.recommendations.length === 0 && (
        <p className="muted">{data.message ?? "Sem recomendações para esta combinação."}</p>
      )}
      {!loading && !error && data?.recommendations.map((r) => (
        <div key={r.product.id} className="rec-item">
          <ProductImage name={r.product.name} category={r.product.category} size="sm" />
          <div>
            <Link to={`/produto/${r.product.id}`}><strong>{r.product.name}</strong></Link>
            <div className="rec-item__meta">
              {formatPrice(r.product.price)} · confiança {formatPct(r.confidence)} · lift {formatNum(r.lift)}
            </div>
            <div className="meter" role="img" aria-label={`Confiança de ${formatPct(r.confidence)}`}>
              <span style={{ width: `${Math.round(r.confidence * 100)}%` }} />
            </div>
            <p className="muted" style={{ fontSize: ".85rem" }}>{r.explanation}</p>
            <button type="button" className="btn btn--ghost btn--sm" onClick={() => add(r.product, true)}>
              Adicionar ao carrinho
            </button>
          </div>
        </div>
      ))}
    </section>
  );
}
