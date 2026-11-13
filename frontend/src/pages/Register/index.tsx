import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ErrorMessage } from "../../components/ui/Status";
import { useAuth } from "../../hooks/useAuth";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("A senha precisa ter pelo menos 8 caracteres.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await register(form.name, form.email, form.password);
      navigate("/perfil");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="card form-card" onSubmit={submit}>
      <h1>Criar conta</h1>
      <div className="field">
        <label htmlFor="nome">Nome</label>
        <input id="nome" autoComplete="name" required minLength={2} value={form.name} onChange={set("name")} />
      </div>
      <div className="field">
        <label htmlFor="email">E-mail</label>
        <input id="email" type="email" autoComplete="email" required value={form.email} onChange={set("email")} />
      </div>
      <div className="field">
        <label htmlFor="senha">Senha (mínimo 8 caracteres)</label>
        <input id="senha" type="password" autoComplete="new-password" required minLength={8} maxLength={72}
          value={form.password} onChange={set("password")} />
      </div>
      {error && <ErrorMessage message={error} />}
      <button type="submit" className="btn btn--primary" disabled={busy}>{busy ? "Criando..." : "Criar conta"}</button>
      <p className="muted" style={{ marginTop: "1rem" }}>Já tem conta? <Link to="/entrar">Entrar</Link>.</p>
    </form>
  );
}
