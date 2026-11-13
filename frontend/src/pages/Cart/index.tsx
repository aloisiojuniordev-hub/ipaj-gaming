import { Link } from "react-router-dom";
import { CartLine } from "../../components/cart/CartLine";
import { RecommendationPanel } from "../../components/recommendations/RecommendationPanel";
import { useCart } from "../../hooks/useCart";
import { useCartRecommendations } from "../../hooks/useCartRecommendations";
import { formatPrice } from "../../utils/format";

export default function Cart() {
  const { items, total, productIds, clear } = useCart();
  const recs = useCartRecommendations(productIds, 4);

  return (
    <>
      <h1>Carrinho Inteligente</h1>
      <div className="two-col">
        <section className="card" aria-labelledby="itens">
          <h2 id="itens">Itens</h2>
          {items.length === 0 ? (
            <p className="muted">Seu carrinho está vazio. <Link to="/catalogo">Explore o catálogo</Link>.</p>
          ) : (
            <>
              {items.map((i) => <CartLine key={i.product.id} item={i} />)}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem", gap: "1rem", flexWrap: "wrap" }}>
                <button type="button" className="btn btn--ghost btn--sm" onClick={clear}>Esvaziar carrinho</button>
                <div>
                  <span className="muted">Total: </span>
                  <strong className="price" style={{ fontSize: "1.4rem" }}>{formatPrice(total)}</strong>
                </div>
                <Link to="/checkout" className="btn btn--primary">Finalizar compra</Link>
              </div>
            </>
          )}
        </section>
        <RecommendationPanel data={recs.data} loading={recs.loading} error={recs.error} />
      </div>
    </>
  );
}
