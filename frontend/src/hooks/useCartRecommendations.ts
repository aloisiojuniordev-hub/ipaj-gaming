import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { RecommendationResponse } from "../types";

/** Consulta o IPAJ CORE sempre que a composição do carrinho muda (debounce de 250 ms). */
export function useCartRecommendations(productIds: string[], limit = 4) {
  const key = [...productIds].sort().join(",");
  const [state, setState] = useState<{ data: RecommendationResponse | null; loading: boolean; error: string | null }>({
    data: null, loading: false, error: null,
  });

  useEffect(() => {
    const ids = key ? key.split(",") : [];
    if (ids.length === 0) {
      setState({ data: { cart: [], recommendations: [], message: "Adicione produtos para ativar o IPAJ CORE." }, loading: false, error: null });
      return;
    }
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    const t = setTimeout(() => {
      api.recommend(ids, limit)
        .then((data) => active && setState({ data, loading: false, error: null }))
        .catch((e: Error) => active && setState({ data: null, loading: false, error: e.message }));
    }, 250);
    return () => { active = false; clearTimeout(t); };
  }, [key, limit]);

  return state;
}
