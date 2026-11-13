import { useParams } from "react-router-dom";
import { ProductImage } from "../../components/products/ProductImage";
import { RecommendationPanel } from "../../components/recommendations/RecommendationPanel";
import { ErrorMessage, Loading } from "../../components/ui/Status";
import { useAsync } from "../../hooks/useAsync";
import { useCart } from "../../hooks/useCart";
import { api } from "../../services/api";
import { formatPrice } from "../../utils/format";

export default function ProductDetails() {
  const { id = "" } = useParams();
  const { add } = useCart();
  const product = useAsync(() => api.product(id), [id]);
  const recs = useAsync(() => api.boughtTogether(id, 4), [id]);

  if (product.loading) return <Loading />;
  if (product.error || !product.data) return <ErrorMessage message={product.error ?? "Produto não encontrado."} />;
  const p = product.data;

  return (
    <div className="two-col">
      <article>
        <ProductImage name={p.name} category={p.category} />
        <p className="category" style={{ marginTop: "1rem" }}>{p.category}</p>
        <h1>{p.name}</h1>
        <p className="lead">{p.description}</p>
        <p className="price" style={{ fontSize: "1.6rem" }}>{formatPrice(p.price)}</p>
        <button type="button" className="btn btn--primary" onClick={() => add(p)}>Adicionar ao carrinho</button>
      </article>
      <RecommendationPanel title="Frequentemente comprados juntos" data={recs.data} loading={recs.loading} error={recs.error} />
    </div>
  );
}
