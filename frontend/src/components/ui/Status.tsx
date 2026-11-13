export function Loading({ label = "Carregando..." }: { label?: string }) {
  return <p role="status" className="muted">{label}</p>;
}

export function ErrorMessage({ message }: { message: string }) {
  return <div role="alert" className="alert alert--error">{message}</div>;
}

export function Stat({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="card stat">
      <div className="stat__value">{value}</div>
      <div className="stat__label">{label}</div>
    </div>
  );
}
