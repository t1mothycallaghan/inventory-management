"""
Tests for restocking API endpoints (budget-based recommendations and restock orders).
"""
from datetime import datetime, timedelta

import pytest

import main


@pytest.fixture(autouse=True)
def clear_restock_orders():
    """Restock orders live in a module-level list; reset it so tests don't share state."""
    main.restock_orders.clear()
    yield
    main.restock_orders.clear()


def get_recommendations(client, budget, **filters):
    params = {"budget": budget, **filters}
    response = client.get("/api/restocking/recommendations", params=params)
    assert response.status_code == 200
    return response.json()


class TestRestockRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_recommendations_structure(self, client):
        """Test response shape and per-item fields."""
        data = get_recommendations(client, 10000)

        for key in ["budget", "full_restock_cost", "recommended_total", "remaining_budget", "items"]:
            assert key in data
        assert len(data["items"]) > 0

        for item in data["items"]:
            for key in ["sku", "name", "category", "warehouse", "quantity_on_hand", "reorder_point",
                        "forecasted_demand", "trend", "unit_cost", "lead_time_days",
                        "suggested_quantity", "recommended_quantity", "line_total"]:
                assert key in item
            assert 0 <= item["recommended_quantity"] <= item["suggested_quantity"]
            assert abs(item["line_total"] - item["recommended_quantity"] * item["unit_cost"]) < 0.01

    @pytest.mark.parametrize("budget", [0, 100, 1500, 7777.77, 25000])
    def test_recommended_total_never_exceeds_budget(self, client, budget):
        """Test the greedy fill never spends more than the budget."""
        data = get_recommendations(client, budget)

        assert data["recommended_total"] <= budget + 0.01
        assert abs(data["remaining_budget"] - (budget - data["recommended_total"])) < 0.01
        assert abs(sum(i["line_total"] for i in data["items"]) - data["recommended_total"]) < 0.01

    def test_zero_budget_recommends_nothing(self, client):
        """Test that budget=0 recommends zero units for every item."""
        data = get_recommendations(client, 0)

        assert data["recommended_total"] == 0
        assert all(item["recommended_quantity"] == 0 for item in data["items"])
        # Items are still listed so the user can add them manually
        assert len(data["items"]) > 0

    def test_large_budget_fills_everything(self, client):
        """Test that a budget above the full restock cost fills every suggestion."""
        data = get_recommendations(client, 10_000_000)

        for item in data["items"]:
            assert item["recommended_quantity"] == item["suggested_quantity"]
        assert abs(data["recommended_total"] - data["full_restock_cost"]) < 0.01

    def test_suggested_quantity_calculation(self, client):
        """Test suggested = max(0, forecast + reorder_point - on_hand)."""
        data = get_recommendations(client, 0)

        for item in data["items"]:
            expected = max(0, item["forecasted_demand"] + item["reorder_point"] - item["quantity_on_hand"])
            assert item["suggested_quantity"] == expected
        assert any(item["suggested_quantity"] > 0 for item in data["items"])

    def test_increasing_trend_filled_first(self, client):
        """Test that increasing-trend items rank first and are funded before others."""
        full = get_recommendations(client, 10_000_000)
        trends = [item["trend"] for item in full["items"]]
        order = {"increasing": 0, "stable": 1, "decreasing": 2}
        assert [order[t] for t in trends] == sorted(order[t] for t in trends)

        # Budget for exactly the increasing items' needs: nothing else should be funded
        increasing_cost = sum(
            i["suggested_quantity"] * i["unit_cost"] for i in full["items"] if i["trend"] == "increasing"
        )
        assert increasing_cost > 0
        data = get_recommendations(client, round(increasing_cost, 2))
        for item in data["items"]:
            if item["trend"] == "increasing":
                assert item["recommended_quantity"] == item["suggested_quantity"]

    def test_recommendations_by_warehouse(self, client):
        """Test filtering recommendations by warehouse."""
        data = get_recommendations(client, 5000, warehouse="Tokyo")
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["warehouse"] == "Tokyo"

    def test_recommendations_by_category(self, client):
        """Test filtering recommendations by category (case-insensitive)."""
        data = get_recommendations(client, 5000, category="power supplies")
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["category"].lower() == "power supplies"

    def test_negative_budget_returns_400(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations", params={"budget": -1})
        assert response.status_code == 400
        assert "detail" in response.json()


class TestRestockOrders:
    """Test suite for POST/GET /api/restocking/orders."""

    def test_create_order_success(self, client):
        """Test a successful order uses server prices and the max lead time."""
        inventory = {i["sku"]: i for i in client.get("/api/inventory").json()}
        leads = {f["item_sku"]: f["lead_time_days"] for f in client.get("/api/demand").json()}
        items = [{"sku": "PSU-501", "quantity": 10}, {"sku": "SRV-301", "quantity": 2}]

        response = client.post("/api/restocking/orders", json={"budget": 100000, "items": items})
        assert response.status_code == 201

        order = response.json()
        expected_total = sum(inventory[i["sku"]]["unit_cost"] * i["quantity"] for i in items)
        assert abs(order["total_cost"] - expected_total) < 0.01
        assert order["status"] == "Submitted"
        assert order["order_number"].startswith("RST-")
        assert order["lead_time_days"] == max(leads[i["sku"]] for i in items)

        submitted = datetime.fromisoformat(order["submitted_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        assert expected_delivery - submitted == timedelta(days=order["lead_time_days"])

    def test_create_order_ignores_client_prices(self, client):
        """Test that extra client-supplied price fields don't affect the total."""
        unit_cost = next(i for i in client.get("/api/inventory").json() if i["sku"] == "PSU-501")["unit_cost"]
        response = client.post("/api/restocking/orders", json={
            "budget": 100000,
            "items": [{"sku": "PSU-501", "quantity": 5, "unit_cost": 0.01}],
        })
        assert response.status_code == 201
        assert abs(response.json()["total_cost"] - unit_cost * 5) < 0.01

    def test_create_order_unknown_sku_returns_404(self, client):
        """Test that an unknown SKU returns 404."""
        response = client.post("/api/restocking/orders", json={
            "budget": 1000, "items": [{"sku": "NOPE-999", "quantity": 1}],
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_order_over_budget_returns_400(self, client):
        """Test that an order costing more than the budget is rejected and not stored."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100, "items": [{"sku": "SRV-302", "quantity": 1}],
        })
        assert response.status_code == 400
        assert client.get("/api/restocking/orders").json() == []

    @pytest.mark.parametrize("payload", [
        {"budget": 1000, "items": [{"sku": "PSU-501", "quantity": 0}]},
        {"budget": 1000, "items": []},
    ])
    def test_create_order_invalid_payload_returns_422(self, client, payload):
        """Test that zero quantity or an empty items list fails validation."""
        response = client.post("/api/restocking/orders", json=payload)
        assert response.status_code == 422

    def test_list_orders_newest_first(self, client):
        """Test that GET lists created orders, newest first."""
        assert client.get("/api/restocking/orders").json() == []

        numbers = []
        for qty in (1, 2):
            response = client.post("/api/restocking/orders", json={
                "budget": 100000, "items": [{"sku": "PSU-501", "quantity": qty}],
            })
            assert response.status_code == 201
            numbers.append(response.json()["order_number"])

        listed = client.get("/api/restocking/orders").json()
        assert [o["order_number"] for o in listed] == list(reversed(numbers))
