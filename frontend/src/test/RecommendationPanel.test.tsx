import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { RecommendationPanel } from "../components/recommendations/RecommendationPanel";
import { CartProvider } from "../contexts/CartContext";
import type { RecommendationResponse } from "../types";

const data: RecommendationResponse = {
  cart: ["P001"],
  message: null,
  recommendations: [{
    product: { id: "P014", name: "Controle DualSense Extra", category: "Controles", price: "449.00", description: "" },
    confidence: 0.62, lift: 3.1, support: 0.08,
    because: [{ id: "P001", name: "PlayStation 5 Slim", category: "Consoles", price: "4499.00", description: "" }],
    explanation: "62% de quem levou PlayStation 5 Slim também levou Controle DualSense Extra",
  }],
};

const wrap = (ui: React.ReactNode) => render(<MemoryRouter><CartProvider>{ui}</CartProvider></MemoryRouter>);

describe("RecommendationPanel", () => {
  it("mostra recomendação com métricas da regra", () => {
    wrap(<RecommendationPanel data={data} loading={false} error={null} />);
    expect(screen.getByText("Controle DualSense Extra")).toBeInTheDocument();
    expect(screen.getByText(/confiança 62%/)).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Confiança de 62%" })).toBeInTheDocument();
  });

  it("mostra mensagem quando não há regra aplicável", () => {
    wrap(<RecommendationPanel data={{ cart: ["X"], recommendations: [], message: "Nenhuma regra" }} loading={false} error={null} />);
    expect(screen.getByText("Nenhuma regra")).toBeInTheDocument();
  });

  it("adiciona ao carrinho marcando origem IPAJ CORE", () => {
    wrap(<RecommendationPanel data={data} loading={false} error={null} />);
    fireEvent.click(screen.getByRole("button", { name: "Adicionar ao carrinho" }));
    const saved = JSON.parse(localStorage.getItem("ipaj.cart") ?? "[]");
    expect(saved[0].product.id).toBe("P014");
    expect(saved[0].fromRecommendation).toBe(true);
  });

  it("exibe erro de API", () => {
    wrap(<RecommendationPanel data={null} loading={false} error="API fora do ar" />);
    expect(screen.getByRole("alert")).toHaveTextContent("API fora do ar");
  });
});
