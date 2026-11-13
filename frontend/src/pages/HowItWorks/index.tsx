import { Link } from "react-router-dom";

export default function HowItWorks() {
  return (
    <article style={{ maxWidth: "75ch" }}>
      <h1>Como funciona o IPAJ CORE</h1>
      <p className="lead">
        O IPAJ CORE é o motor de recomendação da loja. Ele usa o algoritmo <strong>Apriori</strong> para
        descobrir regras do tipo “quem compra A também compra B” a partir do histórico de compras.
      </p>
      <ol className="steps">
        <li>
          <h2>Dados de compras</h2>
          <p>Geramos 5.000 transações simuladas com padrões realistas (por exemplo, quem compra um console
            costuma levar controle extra e jogos), além de ruído aleatório controlado.</p>
        </li>
        <li>
          <h2>Divisão treino/teste</h2>
          <p>80% das transações treinam o modelo e 20% ficam reservadas para medir se as regras generalizam.</p>
        </li>
        <li>
          <h2>Itemsets frequentes</h2>
          <p>O Apriori encontra combinações de produtos que aparecem em pelo menos 1% das compras
            (<em>suporte</em>), descartando cedo combinações cujos subconjuntos já são raros.</p>
        </li>
        <li>
          <h2>Regras de associação</h2>
          <p>Para cada combinação frequente geramos regras A → B e mantemos as que têm
            <em> confiança</em> ≥ 30% (P(B | A)) e <em>lift</em> ≥ 1,2 (B é pelo menos 20% mais provável com A do que ao acaso).</p>
        </li>
        <li>
          <h2>Recomendação no carrinho</h2>
          <p>Quando você monta o carrinho, o motor procura as regras cujo lado “se” está contido nele e
            sugere os itens do lado “então”, ordenados por confiança e lift. Se nenhuma regra se aplica,
            nada é recomendado: não inventamos sugestões.</p>
        </li>
      </ol>
      <p>Veja os números reais no <Link to="/laboratorio">Laboratório IA</Link>.</p>
    </article>
  );
}
