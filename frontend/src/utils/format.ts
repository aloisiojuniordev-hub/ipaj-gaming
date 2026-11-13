const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export const formatPrice = (value: string | number) => brl.format(Number(value));
export const formatPct = (ratio: number, digits = 0) =>
  `${(ratio * 100).toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits })}%`;
export const formatNum = (n: number, digits = 2) =>
  n.toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits });
