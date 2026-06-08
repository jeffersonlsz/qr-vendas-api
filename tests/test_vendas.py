"""
Tests for Vendas API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestVendasEndpoints:
    """Test sale-related endpoints."""

    def test_create_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
        sample_venda_data: dict,
    ):
        """Test creating a new sale."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        lead_response = client.post("/api/v1/leads", json=sample_lead_data)
        lead_id = lead_response.json()["data"]["id"]
        
        # Create sale
        sample_venda_data["lead_id"] = lead_id
        response = client.post("/api/v1/vendas", json=sample_venda_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["lead_id"] == lead_id
        assert data["data"]["parceiro_id"] == sample_parceiro_data["id"]
        assert data["data"]["comissao"] > 0

    def test_get_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
        sample_venda_data: dict,
    ):
        """Test getting a sale by ID."""
        # Create partner, lead, and sale
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        lead_response = client.post("/api/v1/leads", json=sample_lead_data)
        sample_venda_data["lead_id"] = lead_response.json()["data"]["id"]
        
        create_response = client.post("/api/v1/vendas", json=sample_venda_data)
        venda_id = create_response.json()["data"]["id"]
        
        # Get the sale
        response = client.get(f"/api/v1/vendas/{venda_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == venda_id

    def test_list_vendas(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
        sample_venda_data: dict,
    ):
        """Test listing sales."""
        # Create partner, lead, and sale
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        lead_response = client.post("/api/v1/leads", json=sample_lead_data)
        sample_venda_data["lead_id"] = lead_response.json()["data"]["id"]
        client.post("/api/v1/vendas", json=sample_venda_data)
        
        response = client.get("/api/v1/vendas")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "vendas" in data

    def test_mark_venda_as_paid(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
        sample_venda_data: dict,
    ):
        """Test marking a sale as paid."""
        # Create partner, lead, and sale
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        lead_response = client.post("/api/v1/leads", json=sample_lead_data)
        sample_venda_data["lead_id"] = lead_response.json()["data"]["id"]
        
        create_response = client.post("/api/v1/vendas", json=sample_venda_data)
        venda_id = create_response.json()["data"]["id"]
        
        # Mark as paid
        response = client.post(f"/api/v1/vendas/{venda_id}/pagar")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["status"] == "pago"
        assert data["data"]["pago_em"] is not None

    def test_update_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
        sample_venda_data: dict,
    ):
        """Test updating a sale."""
        # Create partner, lead, and sale
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        lead_response = client.post("/api/v1/leads", json=sample_lead_data)
        sample_venda_data["lead_id"] = lead_response.json()["data"]["id"]
        
        create_response = client.post("/api/v1/vendas", json=sample_venda_data)
        venda_id = create_response.json()["data"]["id"]
        
        # Update the sale
        response = client.patch(
            f"/api/v1/vendas/{venda_id}",
            json={"valor_venda": 2000.00, "descricao": "Updated description"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["valor_venda"] == 2000.00
        # Commission should be recalculated
        assert data["data"]["comissao"] == 2000.00 * sample_parceiro_data["percentual_comissao"]
