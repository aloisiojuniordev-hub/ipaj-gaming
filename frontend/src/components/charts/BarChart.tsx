/** Gráfico de barras horizontal em SVG puro, acessível (tabela equivalente para leitores de tela). */
export interface Bar { label: string; value: number; display?: string }

export function BarChart({ title, bars, max }: { title: string; bars: Bar[]; max?: number }) {
  const top = max ?? Math.max(...bars.map((b) => b.value), 1);
  const rowH = 30;
  const labelW = 210;
  const width = 640;
  return (
    <figure style={{ margin: 0 }}>
      <figcaption><strong>{title}</strong></figcaption>
      <svg viewBox={`0 0 ${width} ${bars.length * rowH + 10}`} width="100%" aria-hidden="true">
        {bars.map((b, i) => {
          const w = ((width - labelW - 70) * b.value) / top;
          return (
            <g key={b.label} transform={`translate(0, ${i * rowH + 5})`}>
              <text x={labelW - 8} y={18} textAnchor="end" fill="#a3a8cc" fontSize="12">
                {b.label.length > 32 ? `${b.label.slice(0, 31)}…` : b.label}
              </text>
              <rect x={labelW} y={4} width={Math.max(w, 2)} height={20} rx={5} fill="url(#barGrad)" />
              <text x={labelW + w + 6} y={18} fill="#e8eaf6" fontSize="12">{b.display ?? b.value}</text>
            </g>
          );
        })}
        <defs>
          <linearGradient id="barGrad" x1="0" x2="1"><stop offset="0" stopColor="#7c3aed" /><stop offset="1" stopColor="#22d3ee" /></linearGradient>
        </defs>
      </svg>
      <table className="sr-only">
        <caption>{title}</caption>
        <tbody>{bars.map((b) => <tr key={b.label}><th>{b.label}</th><td>{b.display ?? b.value}</td></tr>)}</tbody>
      </table>
    </figure>
  );
}
