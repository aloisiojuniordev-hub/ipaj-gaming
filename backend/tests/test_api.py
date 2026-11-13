from decimal import Decimal


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["rules_loaded"] > 0


def test_catalog_seeded(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    assert len(r.json()) == 50
    assert "Consoles" in client.get("/api/products/categories").json()


def test_product_filters_and_404(client):
    consoles = client.get("/api/products", params={"category": "Consoles"}).json()
    assert {p["id"] for p in consoles} == {"P001", "P002", "P003"}
    prices = [Decimal(p["price"]) for p in client.get("/api/products", params={"sort": "price_asc"}).json()]
    assert prices == sorted(prices)
    assert client.get("/api/products/XXXX").status_code == 404


def test_recommendations_for_cart(client):
    r = client.post("/api/recommendations", json={"cart": ["P001"], "limit": 3})
    assert r.status_code == 200
    recs = r.json()["recommendations"]
    assert 0 < len(recs) <= 3
    ids = [x["product"]["id"] for x in recs]
    assert "P001" not in ids
    confs = [x["confidence"] for x in recs]
    assert confs == sorted(confs, reverse=True)
    assert all(x["lift"] > 1 for x in recs)
    assert recs[0]["because"][0]["id"] == "P001"


def test_recommendations_empty_and_invalid(client):
    empty = client.post("/api/recommendations", json={"cart": []}).json()
    assert empty["recommendations"] == [] and empty["message"]
    assert client.post("/api/recommendations", json={"cart": ["NOPE"]}).status_code == 422


def test_recommendations_by_product(client):
    r = client.get("/api/recommendations/product/P003")
    assert r.status_code == 200
    assert r.json()["recommendations"]


def test_laboratory(client):
    m = client.get("/api/laboratory/metrics").json()
    assert m["training"]["n_rules"] > 0 and "evaluation" in m
    rules = client.get("/api/laboratory/rules", params={"limit": 5, "sort_by": "lift"}).json()
    lifts = [r["lift"] for r in rules]
    assert len(rules) == 5 and lifts == sorted(lifts, reverse=True)
    sets = client.get("/api/laboratory/itemsets", params={"min_size": 2, "limit": 5}).json()
    assert all(len(s["items"]) >= 2 for s in sets)


def test_auth_flow(client):
    payload = {"name": "Iran", "email": "Fluxo@Example.com", "password": "senha-forte-123"}
    assert client.post("/api/users/register", json=payload).status_code == 201
    assert client.post("/api/users/register", json=payload).status_code == 409
    assert client.post("/api/users/login", json={"email": payload["email"], "password": "errada"}).status_code == 401
    token = client.post("/api/users/login", json={"email": "fluxo@example.com",
                                                  "password": payload["password"]}).json()["access_token"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["email"] == "fluxo@example.com"
    assert client.get("/api/users/me").status_code == 401
    assert client.get("/api/users/me", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_guest_order_uses_server_prices(client):
    r = client.post("/api/orders", json={"items": [{"product_id": "P024", "quantity": 2},
                                                   {"product_id": "P024", "quantity": 1}]})
    assert r.status_code == 201
    body = r.json()
    assert body["is_guest"] is True
    assert Decimal(body["total"]) == Decimal("357.00")  # 3 x 119,00
    assert len(body["items"]) == 1


def test_order_linked_to_user_and_isolated(client, auth_headers):
    r = client.post("/api/orders", headers=auth_headers,
                    json={"items": [{"product_id": "P001", "quantity": 1},
                                    {"product_id": "P014", "quantity": 1, "from_recommendation": True}]})
    assert r.status_code == 201
    order = r.json()
    assert order["is_guest"] is False
    mine = client.get("/api/orders/me", headers=auth_headers).json()
    assert [o["id"] for o in mine] == [order["id"]]
    assert client.get(f"/api/orders/{order['id']}", headers=auth_headers).status_code == 200

    other = client.post("/api/users/register", json={"name": "Outro", "email": "outro@example.com",
                                                     "password": "senha-outro-1"}).json()["access_token"]
    assert client.get(f"/api/orders/{order['id']}",
                      headers={"Authorization": f"Bearer {other}"}).status_code == 404


def test_order_validation(client):
    assert client.post("/api/orders", json={"items": []}).status_code == 422
    assert client.post("/api/orders", json={"items": [{"product_id": "XX", "quantity": 1}]}).status_code == 422
    assert client.post("/api/orders", json={"items": [{"product_id": "P001", "quantity": 0}]}).status_code == 422
