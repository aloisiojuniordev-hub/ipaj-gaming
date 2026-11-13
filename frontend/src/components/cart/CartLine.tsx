import { Link } from "react-router-dom";
import { useCart } from "../../hooks/useCart";
import type { CartItem } from "../../types";
import { formatPrice } from "../../utils/format";
import { ProductImage } from "../products/ProductImage";

export function CartLine({ item }: { item: CartItem }) {
  const { setQty, remove } = useCart();
  const { product, quantity } = item;
  const inputId = `qty-${product.id}`;
  return (
    <div className="rec-item" style={{ gridTemplateColumns: "72px 1fr auto" }}>
      <ProductImage name={product.name} category={product.category} size="sm" />
      <div>
        <Link to={`/produto/${product.id}`}><strong>{product.name}</strong></Link>
        <div className="rec-item__meta">
          {formatPrice(product.price)} cada
          {item.fromRecommendation && <span className="chip" style={{ marginLeft: ".5rem" }}>via IPAJ CORE</span>}
        </div>
        <div className="qty">
          <label htmlFor={inputId} className="sr-only">Quantidade de {product.name}</label>
          <button type="button" className="btn btn--ghost btn--sm" aria-label={`Diminuir ${product.name}`}
            onClick={() => setQty(product.id, quantity - 1)}>−</button>
          <input id={inputId} type="number" min={1} max={20} value={quantity}
            onChange={(e) => setQty(product.id, Number(e.target.value) || 1)} />
          <button type="button" className="btn btn--ghost btn--sm" aria-label={`Aumentar ${product.name}`}
            onClick={() => setQty(product.id, quantity + 1)}>+</button>
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => remove(product.id)}>Remover</button>
        </div>
      </div>
      <strong className="price">{formatPrice(Number(product.price) * quantity)}</strong>
    </div>
  );
}
