import { Link, NavLink } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { useCart } from "../../hooks/useCart";

const links = [
  { to: "/", label: "Início", end: true },
  { to: "/catalogo", label: "Catálogo" },
  { to: "/laboratorio", label: "Laboratório IA" },
  { to: "/como-funciona", label: "Como funciona" },
];

export function Header() {
  const { count } = useCart();
  const { user } = useAuth();
  return (
    <header className="header">
      <div className="container header__inner">
        <Link to="/" className="brand" aria-label="IPAJ Gaming, página inicial">IPAJ<span>Gaming</span></Link>
        <nav className="nav" aria-label="Navegação principal">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end}>{l.label}</NavLink>
          ))}
        </nav>
        <div className="header__actions">
          {user
            ? <NavLink to="/perfil">Olá, {user.name.split(" ")[0]}</NavLink>
            : <NavLink to="/entrar">Entrar</NavLink>}
          <Link to="/carrinho" className="cart-link" aria-label={`Carrinho com ${count} ${count === 1 ? "item" : "itens"}`}>
            Carrinho <span className="badge" aria-hidden="true">{count}</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
