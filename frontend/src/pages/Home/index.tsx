import { Link } from "react-router-dom";
import { ProductCard } from "../../components/products/ProductCard";
import { HeroScene } from "../../components/ui/HeroScene";
import { ErrorMessage, Loading, Stat } from "../../components/ui/Status";
import { useAsync } from "../../hooks/useAsync";
import { api } from "../../services/api";

const FEATURED = ["P001", "P003", "P021", "P029", "P041", "P046", "P002", "P032"];

export default function Home() {
  const products = useAsync(() => api.products(), []);
  const metrics = useAsync(() => api.metrics(), []);
  const featured = products.data?.filter((p) => FEATURED.includes(p.id)) ?? [];
  const ev = metrics.data?.evaluation;

  return (
    <>
      <section className="hero">
        <div>
          <p className="category">Carrinho Inteligente · Algoritmo Apriori</p>
          <h1>Seu setup gamer, montado com mineração de dados.</h1>
          <p className="lead">
            O <strong>IPAJ CORE</strong> analisa milhares de compras e descobre quais produtos costumam ser
            comprados juntos. Cada recomendação mostra a regra, a confiança e o lift que a justificam.
          </p>
          <div style={{ display: "flex", gap: ".75rem", flexWrap: "wrap" }}>
            <Link to="/catalogo" className="btn btn--primary">Explorar catálogo</Link>
            <Link to="/laboratorio" className="btn btn--ghost">Abrir Laboratório IA</Link>
          </div>
        </div>
        <HeroScene />
      </section>

      <section className="section" aria-labelledby="numeros">
        <h2 id="numeros">IPAJ CORE em números</h2>
        {metrics.loading && <Loading />}
        {metrics.error && <ErrorMessage message={metrics.error} />}
        {metrics.data && (
          <div className="grid grid--stats">
            <Stat value={metrics.data.training.n_train_transactions.toLocaleString("pt-BR")} label="transações de treino" />
            <Stat value={metrics.data.training.n_rules} label="regras de associação" />
            {ev && <Stat value={`${ev.hit_rate_at_k_all_carts_pct.toLocaleString("pt-BR")}%`} label={`acerto no Top-${ev.top_k} (teste)`} />}
            {ev && <Stat value={`${ev.cart_coverage_pct.toLocaleString("pt-BR")}%`} label="carrinhos de teste com recomendação" />}
          </div>
        )}
      </section>

      <section className="section" aria-labelledby="destaques">
        <h2 id="destaques">Destaques</h2>
        {products.loading && <Loading />}
        {products.error && <ErrorMessage message={products.error} />}
        <div className="grid">{featured.map((p) => <ProductCard key={p.id} product={p} />)}</div>
      </section>
    </>
  );
}
