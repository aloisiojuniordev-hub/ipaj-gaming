import { useSearchParams } from "react-router-dom";
import { ProductCard } from "../../components/products/ProductCard";
import { ErrorMessage, Loading } from "../../components/ui/Status";
import { useAsync } from "../../hooks/useAsync";
import { api } from "../../services/api";

export default function Catalog() {
  const [params, setParams] = useSearchParams();
  const category = params.get("categoria") ?? "";
  const q = params.get("q") ?? "";
  const sort = params.get("ordem") ?? "name";

  const categories = useAsync(() => api.categories(), []);
  const products = useAsync(() => api.products({ category, q, sort }), [category, q, sort]);

  const update = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };

  return (
    <>
      <h1>Catálogo</h1>
      <div className="toolbar" role="search">
        <div>
          <label htmlFor="busca">Buscar</label>
          <input id="busca" type="search" value={q} placeholder="Ex.: mouse, PS5..."
            onChange={(e) => update("q", e.target.value)} />
        </div>
        <div>
          <label htmlFor="categoria">Categoria</label>
          <select id="categoria" value={category} onChange={(e) => update("categoria", e.target.value)}>
            <option value="">Todas</option>
            {categories.data?.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="ordem">Ordenar por</label>
          <select id="ordem" value={sort} onChange={(e) => update("ordem", e.target.value)}>
            <option value="name">Nome</option>
            <option value="price_asc">Menor preço</option>
            <option value="price_desc">Maior preço</option>
          </select>
        </div>
      </div>
      {products.loading && <Loading />}
      {products.error && <ErrorMessage message={products.error} />}
      {products.data && (
        <>
          <p className="muted" role="status">{products.data.length} produto(s)</p>
          <div className="grid">{products.data.map((p) => <ProductCard key={p.id} product={p} />)}</div>
        </>
      )}
    </>
  );
}
