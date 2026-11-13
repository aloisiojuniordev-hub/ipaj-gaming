export interface Product {
  id: string;
  name: string;
  category: string;
  price: string; // Decimal serializado pela API (ex.: "4499.00")
  description: string;
}

export interface Recommendation {
  product: Product;
  confidence: number;
  lift: number;
  support: number;
  because: Product[];
  explanation: string;
}

export interface RecommendationResponse {
  cart: string[];
  recommendations: Recommendation[];
  message: string | null;
}

export interface Rule {
  antecedents: Product[];
  consequents: Product[];
  support: number;
  confidence: number;
  lift: number;
  leverage: number;
}

export interface Itemset {
  items: Product[];
  support: number;
}

export interface Metrics {
  training: {
    trained_at_utc: string;
    seed: number;
    n_train_transactions: number;
    n_test_transactions: number;
    parameters: { min_support: number; min_confidence: number; min_lift: number; max_len: number };
    n_itemsets: number;
    n_rules: number;
  };
  evaluation?: {
    top_k: number;
    n_test_carts_evaluated: number;
    cart_coverage_pct: number;
    hit_rate_at_k_all_carts_pct: number;
    hit_rate_at_k_covered_carts_pct: number;
    precision_at_k_covered_pct: number;
    baseline_popularity_hit_rate_at_k_pct: number;
    item_coverage_pct: number;
    rule_quality: {
      n_rules: number;
      train: { support: number; confidence: number; lift: number };
      test: { support: number; confidence: number; lift: number };
      pct_rules_lift_gt_1_in_test: number;
    };
  };
}

export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

export interface CartItem {
  product: Product;
  quantity: number;
  fromRecommendation: boolean;
}

export interface Order {
  id: number;
  status: string;
  total: string;
  created_at: string;
  is_guest: boolean;
  items: { product_id: string; quantity: number; unit_price: string; from_recommendation: boolean }[];
}
