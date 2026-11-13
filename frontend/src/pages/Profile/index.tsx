import { Navigate } from "react-router-dom";
import { ErrorMessage, Loading } from "../../components/ui/Status";
import { useAsync } from "../../hooks/useAsync";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import { formatPrice } from "../../utils/format";

export default function Profile() {
  const { user, loading, logout } = useAuth();
  const orders = useAsync(() => (user ? api.myOrders() : Promise.resolve([])), [user?.id]);

  if (loading) return <Loading />;
  if (!user) return <Navigate to="/entrar" replace />;

  return (
    <>
      <h1>Olá, {user.name}</h1>
      <p className="muted">{user.email}</p>
      <button type="button" className="btn btn--ghost btn--sm" onClick={logout}>Sair</button>
      <section className="section card" aria-labelledby="pedidos">
        <h2 id="pedidos">Meus pedidos demonstrativos</h2>
        {orders.loading && <Loading />}
        {orders.error && <ErrorMessage message={orders.error} />}
        {orders.data?.length === 0 && <p className="muted">Nenhum pedido ainda.</p>}
        {orders.data && orders.data.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Pedido</th><th>Data</th><th className="num">Itens</th><th className="num">Via IPAJ CORE</th><th className="num">Total</th></tr></thead>
              <tbody>
                {orders.data.map((o) => (
                  <tr key={o.id}>
                    <td>#{o.id}</td>
                    <td>{new Date(o.created_at).toLocaleString("pt-BR")}</td>
                    <td className="num">{o.items.reduce((s, i) => s + i.quantity, 0)}</td>
                    <td className="num">{o.items.filter((i) => i.from_recommendation).length}</td>
                    <td className="num">{formatPrice(o.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
