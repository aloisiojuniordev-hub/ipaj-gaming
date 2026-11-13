import { Link } from "react-router-dom";
import { useCart } from "../../hooks/useCart";
import type { Product } from "../../types";
import { formatPrice } from "../../utils/format";
import { ProductImage } from "./ProductImage";

export function ProductCard({ product }: { product: Product }) {
  const { add, productIds } = useCart();
  const inCart = productIds.includes(product.id);
  return (
    <article className="card product-card">
      <ProductImage name={product.name} category={product.category} />
      <span className="category">{product.category}</span>
      <h3><Link to={`/produto/${product.id}`}>{product.name}</Link></h3>
      <div className="product-card__footer">
        <span className="price">{formatPrice(product.price)}</span>
        <button type="button" className="btn btn--primary btn--sm" onClick={() => add(product)}
          aria-label={`Adicionar ${product.name} ao carrinho`}>
          {inCart ? "+1" : "Adicionar"}
        </button>
      </div>
    </article>
  );
}
