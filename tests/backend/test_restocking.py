"""
Tests for restocking order endpoints.
"""
import pytest


class TestRestockOrdersEndpoints:
    """Test suite for restock order endpoints."""

    def test_get_restock_orders_returns_list(self, client):
        """Test getting restock orders returns a list."""
        response = client.get("/api/restock-orders")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_create_restock_order_success(self, client):
        """Test creating a restock order with valid items."""
        payload = {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 10, "unit_cost": 24.99}
            ],
            "budget": 5000
        }
        response = client.post("/api/restock-orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["status"] == "Submitted"
        assert data["lead_time_days"] == 14
        assert "expected_delivery_date" in data
        assert "created_date" in data
        assert "order_number" in data
        assert data["total_cost"] == pytest.approx(249.9)
        assert data["budget"] == 5000
        assert len(data["items"]) == 1

    def test_create_restock_order_appears_in_list(self, client):
        """Test that a created restock order shows up in a subsequent GET."""
        payload = {
            "items": [
                {"sku": "SPR-602", "name": "Compression Spring", "quantity": 5, "unit_cost": 89.5}
            ],
            "budget": 1000
        }
        create_response = client.post("/api/restock-orders", json=payload)
        assert create_response.status_code == 201
        created_order = create_response.json()

        list_response = client.get("/api/restock-orders")
        assert list_response.status_code == 200
        data = list_response.json()

        order_ids = [order["id"] for order in data]
        assert created_order["id"] in order_ids

    def test_create_restock_order_empty_items_rejected(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restock-orders", json={"items": [], "budget": 1000})
        assert response.status_code == 400
