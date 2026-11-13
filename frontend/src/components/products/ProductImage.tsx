/** Ilustração SVG gerada por categoria (sem imagens de terceiros). */
const PALETTE: Record<string, [string, string]> = {
  Consoles: ["#7c3aed", "#22d3ee"],
  Jogos: ["#db2777", "#f59e0b"],
  Controles: ["#2563eb", "#22d3ee"],
  Headsets: ["#9333ea", "#ec4899"],
  Teclados: ["#0891b2", "#34d399"],
  Mouses: ["#4f46e5", "#a78bfa"],
  Mousepads: ["#0f766e", "#22d3ee"],
  Monitores: ["#1d4ed8", "#60a5fa"],
  Cadeiras: ["#b91c1c", "#f97316"],
  Acessórios: ["#4b5563", "#a3a8cc"],
  Streaming: ["#be123c", "#fb7185"],
  Hardware: ["#15803d", "#a3e635"],
};

const GLYPH: Record<string, string> = {
  Consoles: "M30 52h60a12 12 0 0 1 12 12v6a20 20 0 0 1-34 14h-16A20 20 0 0 1 18 70v-6a12 12 0 0 1 12-12z",
  Controles: "M30 52h60a12 12 0 0 1 12 12v6a20 20 0 0 1-34 14h-16A20 20 0 0 1 18 70v-6a12 12 0 0 1 12-12z",
  Jogos: "M38 30h44v60H38z M46 40h28v24H46z",
  Headsets: "M30 70a30 30 0 0 1 60 0v14h-12V70h6a24 24 0 0 0-48 0h6v14H30z",
  Teclados: "M18 48h84v34H18z M26 56h8v6h-8z M40 56h8v6h-8z M54 56h8v6h-8z M68 56h8v6h-8z M84 56h10v6H84z M30 70h60v6H30z",
  Mouses: "M60 28a18 18 0 0 1 18 18v28a18 18 0 0 1-36 0V46a18 18 0 0 1 18-18z M59 34h2v14h-2z",
  Mousepads: "M18 44h84v40H18z",
  Monitores: "M18 32h84v48H18z M54 80h12v8H54z M42 88h36v4H42z",
  Cadeiras: "M44 24h32v44H44z M38 68h44v8H38z M58 76h4v14h-4z M44 90h32v4H44z",
  Acessórios: "M60 30l26 15v30L60 90 34 75V45z",
  Streaming: "M52 30h16v36a8 8 0 0 1-16 0z M44 58a16 16 0 0 0 32 0 M60 74v12 M48 88h24",
  Hardware: "M28 40h64v40H28z M36 48h20v24H36z M64 48h20v10H64z M64 62h20v10H64z",
};

export function ProductImage({ name, category, size = "md" }: { name: string; category: string; size?: "sm" | "md" }) {
  const [a, b] = PALETTE[category] ?? ["#7c3aed", "#22d3ee"];
  const id = `g-${category}-${size}`.replace(/\W/g, "");
  return (
    <svg className="product-image" viewBox="0 0 120 90" role="img" aria-label={`Ilustração de ${name}`}
      style={size === "sm" ? { width: 72, height: 54 } : undefined}>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={a} /><stop offset="1" stopColor={b} />
        </linearGradient>
      </defs>
      <rect width="120" height="90" rx="10" fill={`url(#${id})`} opacity=".25" />
      <path d={GLYPH[category] ?? GLYPH["Acessórios"]} transform="translate(0,-8)" fill="none"
        stroke={`url(#${id})`} strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}
