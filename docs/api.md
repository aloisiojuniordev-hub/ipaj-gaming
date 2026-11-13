# API

Base local: `http://localhost:8000`. A documentação interativa OpenAPI é gerada pelo FastAPI:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Esquema: `/openapi.json`

Erros seguem o padrão do FastAPI: `{"detail": "mensagem"}` (ou uma lista de erros de validação no 422).

## Infra

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | `{"status":"ok","database":"ok","recommender":"ok","rules_loaded":394}`. `status` = `degraded` se o banco ou os artefatos falharem. |

## Produtos

| Método | Rota | Parâmetros | Respostas |
|---|---|---|---|
| GET | `/api/products` | `category`, `q` (busca no nome, máx. 80), `sort` = `name` \| `price_asc` \| `price_desc` | 200 lista de produtos, 422 parâmetro inválido |
| GET | `/api/products/categories` | — | 200 lista de strings |
| GET | `/api/products/{id}` | — | 200 produto, 404 |

Produto:

```json
{ "id": "P001", "name": "PlayStation 5 Slim", "category": "Consoles", "price": "4499.00", "description": "..." }
```

## IPAJ CORE (recomendações)

### `POST /api/recommendations`

```json
{ "cart": ["P001"], "limit": 3 }
```

`cart`: até 50 IDs. `limit`: 1 a 10 (padrão 4).

Resposta 200:

```json
{
  "cart": ["P001"],
  "recommendations": [
    {
      "product": { "id": "P014", "name": "Controle DualSense Extra", "...": "..." },
      "confidence": 0.7167, "lift": 7.2213, "support": 0.0633,
      "because": [{ "id": "P001", "name": "PlayStation 5 Slim", "...": "..." }],
      "explanation": "72% de quem levou PlayStation 5 Slim também levou Controle DualSense Extra (...)"
    }
  ],
  "message": null
}
```

Carrinho vazio ou sem regra aplicável: `recommendations: []` e `message` explicativa.

| Código | Quando |
|---|---|
| 422 | ID inexistente no carrinho ou corpo inválido |
| 503 | Artefatos do Apriori indisponíveis |

### `GET /api/recommendations/product/{id}?limit=4`

“Frequentemente comprados juntos” (carrinho = `[id]`). 404 se o produto não existir.

## Laboratório IA

| Método | Rota | Parâmetros |
|---|---|---|
| GET | `/api/laboratory/metrics` | — devolve `metrics.json` (treino e avaliação) |
| GET | `/api/laboratory/rules` | `sort_by` = `lift`\|`confidence`\|`support`; `limit` 1–500; `min_confidence` 0–1; `min_lift` ≥ 0; `product_id` |
| GET | `/api/laboratory/itemsets` | `min_size` 1–3; `limit` 1–300 |

## Usuários

| Método | Rota | Corpo | Respostas |
|---|---|---|---|
| POST | `/api/users/register` | `{"name","email","password"}` (senha de 8 a 72 caracteres) | 201 `{access_token, token_type, user}`, 409 e-mail já cadastrado, 422 |
| POST | `/api/users/login` | `{"email","password"}` | 200 token, 401 credenciais inválidas (mensagem única) |
| GET | `/api/users/me` | header `Authorization: Bearer <token>` | 200 usuário, 401 |

O token é um JWT HS256 com expiração configurável (`JWT_EXPIRES_MINUTES`, padrão 120).

## Pedidos (demonstrativos)

### `POST /api/orders`

Autenticação **opcional**. Com token, o pedido fica vinculado ao usuário. Sem token, é pedido de visitante.

```json
{
  "items": [
    { "product_id": "P001", "quantity": 1 },
    { "product_id": "P014", "quantity": 1, "from_recommendation": true }
  ],
  "guest_label": "opcional, até 60 caracteres (só para visitantes)"
}
```

- O total é calculado **no servidor** com os preços do banco.
- Itens repetidos são agregados. `quantity` vai de 1 a 20 e o pedido pode ter até 50 linhas.
- Visitantes não informam e-mail nem endereço.

| Código | Quando |
|---|---|
| 201 | Pedido criado (`status: "demo_confirmed"`) |
| 401 | Token enviado, mas inválido |
| 422 | Lista vazia, produto inexistente ou quantidade inválida |

### `GET /api/orders/me`

Pedidos do usuário autenticado (401 sem token).

### `GET /api/orders/{id}`

Pedido do próprio usuário. Devolve **404** também para pedidos de outros usuários, para não revelar que existem.

## Exemplo com curl

```bash
curl -s -X POST http://localhost:8000/api/recommendations \
  -H "Content-Type: application/json" -d '{"cart":["P003"],"limit":3}'
```
