import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ErrorMessage } from "../../components/ui/Status";
import { useAuth } from "../../hooks/useAuth";
import { useCart } from "../../hooks/useCart";
import { api } from "../../services/api";
import type { Order } from "../../types";
import { formatPrice } from "../../utils/format";

export default function Checkout() {
  const { items, total, clear } = useCart();
  const { user } = useAuth();
  const [nickname, setNickname] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [order, setOrder] = useState<Order | null>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const created = await api.createOrder(
        items.map((i) => ({ product_id: i.product.id, quantity: i.quantity, from_recommendation: i.fromRecommendation })),
        user ? undefined : nickname.trim() || undefined,
      );
      setOrder(created);
      clear();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  if (order) {
    return (
      <section className="card form-card" aria-live="polite">
        <h1>Pedido demonstrativo #{order.id} confirmado</h1>
        <div className="alert alert--success">Total registrado: {formatPrice(order.total)}</div>
        <p className="muted">Nenhum pagamento foi processado: esta é uma loja acadêmica de demonstração.</p>
        {user ? <Link to="/perfil">Ver meus pedidos</Link> : <Link to="/catalogo">Voltar ao catálogo</Link>}
      </section>
    );
  }

  if (items.length === 0) {
    return <p className="muted">Carrinho vazio. <Link to="/catalogo">Escolha seus produtos</Link>.</p>;
  }

  return (
    <form className="card form-card" onSubmit={submit} noValidate>
      <h1>Checkout demonstrativo</h1>
      <div className="alert alert--info">Não há cobrança nem pagamento real. O pedido é salvo apenas para demonstração.</div>
      <ul>
        {items.map((i) => <li key={i.product.id}>{i.quantity}× {i.product.name} — {formatPrice(Number(i.product.price) * i.quantity)}</li>)}
      </ul>
      <p><strong>Total: {formatPrice(total)}</strong></p>
      {user ? (
        <p className="muted">O pedido será vinculado à sua conta ({user.email}).</p>
      ) : (
        <div className="field">
          <label htmlFor="apelido">Apelido (opcional, visitante)</label>
          <input id="apelido" maxLength={60} value={nickname} onChange={(e) => setNickname(e.target.value)}
            aria-describedby="apelido-ajuda" />
          <small id="apelido-ajuda" className="muted">
            Não pedimos e-mail nem endereço de visitantes. <Link to="/entrar">Entre</Link> para salvar o histórico.
          </small>
        </div>
      )}
      {error && <ErrorMessage message={error} />}
      <button type="submit" className="btn btn--primary" disabled={submitting}>
        {submitting ? "Registrando..." : "Confirmar pedido demonstrativo"}
      </button>
    </form>
  );
}
