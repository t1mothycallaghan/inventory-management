"""
Tests for task and purchase order API endpoints.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def reset_state():
    """Tasks and purchase orders live in module-level lists; snapshot and restore them
    so tests don't share state (purchase_orders is seeded from JSON, so restore rather than clear)."""
    saved_pos = list(main.purchase_orders)
    main.tasks.clear()
    main.next_task_id = 1
    yield
    main.tasks.clear()
    main.next_task_id = 1
    main.purchase_orders[:] = saved_pos


def make_task(client, **overrides):
    body = {"title": "Check stock", "priority": "high", "dueDate": "2025-12-01", **overrides}
    response = client.post("/api/tasks", json=body)
    assert response.status_code == 201
    return response.json()


def first_backlog_id(client):
    backlog = client.get("/api/backlog").json()
    assert len(backlog) > 0
    return backlog[0]["id"]


def make_po(client, backlog_item_id, **overrides):
    body = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 50,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-12-15",
        "notes": "Rush",
        **overrides,
    }
    return client.post("/api/purchase-orders", json=body)


class TestTasksEndpoints:
    """Test suite for task endpoints."""

    def test_get_tasks_empty(self, client):
        """Test that the task list starts empty."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_task(self, client):
        """Test creating a task returns it as pending with a string id."""
        task = make_task(client)
        assert task["title"] == "Check stock"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2025-12-01"
        assert task["status"] == "pending"
        assert isinstance(task["id"], str)

    def test_created_tasks_listed_newest_first(self, client):
        """Test that new tasks appear at the front of the list."""
        first = make_task(client, title="First")
        second = make_task(client, title="Second")
        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert ids == [second["id"], first["id"]]

    def test_create_task_validation(self, client):
        """Test that empty titles, bad priorities and missing due dates are rejected."""
        assert client.post("/api/tasks", json={"title": "", "dueDate": "2025-12-01"}).status_code == 422
        assert client.post("/api/tasks", json={"title": "x", "priority": "urgent", "dueDate": "2025-12-01"}).status_code == 422
        assert client.post("/api/tasks", json={"title": "x"}).status_code == 422

    def test_toggle_task(self, client):
        """Test that PATCH flips status pending -> completed -> pending."""
        task = make_task(client)
        response = client.patch(f"/api/tasks/{task['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert client.patch(f"/api/tasks/{task['id']}").json()["status"] == "pending"

    def test_delete_task(self, client):
        """Test deleting a task removes it from the list."""
        task = make_task(client)
        assert client.delete(f"/api/tasks/{task['id']}").status_code == 200
        assert client.get("/api/tasks").json() == []

    def test_nonexistent_task(self, client):
        """Test toggling or deleting an unknown task returns 404."""
        for response in (client.patch("/api/tasks/task-999"), client.delete("/api/tasks/task-999")):
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()


class TestPurchaseOrderEndpoints:
    """Test suite for purchase order endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a PO returns the full record as pending."""
        backlog_id = first_backlog_id(client)
        response = make_po(client, backlog_id)
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["supplier_name"] == "Acme Supply"
        assert po["quantity"] == 50
        assert abs(po["unit_cost"] - 12.5) < 0.01
        assert po["status"] == "pending"
        assert "T" in po["created_date"]

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the PO created for a backlog item."""
        backlog_id = first_backlog_id(client)
        created = make_po(client, backlog_id).json()
        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json() == created

    def test_backlog_reports_has_purchase_order(self, client):
        """Test that /api/backlog flags the item once a PO exists."""
        backlog_id = first_backlog_id(client)
        make_po(client, backlog_id)
        item = next(b for b in client.get("/api/backlog").json() if b["id"] == backlog_id)
        assert item["has_purchase_order"] is True

    def test_duplicate_purchase_order_rejected(self, client):
        """Test that a second PO for the same backlog item returns 409."""
        backlog_id = first_backlog_id(client)
        assert make_po(client, backlog_id).status_code == 201
        assert make_po(client, backlog_id).status_code == 409

    def test_purchase_order_unknown_backlog_item(self, client):
        """Test creating a PO for a nonexistent backlog item returns 404."""
        response = make_po(client, "nonexistent-999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_purchase_order_validation(self, client):
        """Test that non-positive quantity/cost and empty supplier are rejected."""
        backlog_id = first_backlog_id(client)
        assert make_po(client, backlog_id, quantity=0).status_code == 422
        assert make_po(client, backlog_id, unit_cost=-1).status_code == 422
        assert make_po(client, backlog_id, supplier_name="").status_code == 422

    def test_get_nonexistent_purchase_order(self, client):
        """Test fetching a PO for a backlog item without one returns 404."""
        response = client.get("/api/purchase-orders/nonexistent-999")
        assert response.status_code == 404
        assert "detail" in response.json()
