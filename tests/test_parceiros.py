"""
Tests for Parceiros API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestParceirosEndpoints:
    """Test partner-related endpoints."""

    def test_create_parceiro(self, client: TestClient, sample_parceiro_data: dict):
        """Test creating a new partner."""
        response = client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == sample_parceiro_data["id"]
        assert data["data"]["nome"] == sample_parceiro_data["nome"]
        assert data["data"]["ativo"] is True

    def test_get_parceiro(self, client: TestClient, sample_parceiro_data: dict):
        """Test getting a partner by ID."""
        # First create the partner
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Then retrieve it
        response = client.get(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == sample_parceiro_data["id"]

    def test_get_parceiro_not_found(self, client: TestClient):
        """Test getting a non-existent partner."""
        response = client.get("/api/v1/parceiros/UBER_NONEXISTENT")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_list_parceiros(self, client: TestClient, sample_parceiro_data: dict):
        """Test listing partners."""
        # Create a partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        response = client.get("/api/v1/parceiros")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_update_parceiro(self, client: TestClient, sample_parceiro_data: dict):
        """Test updating a partner."""
        # Create partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Update it
        update_data = {"nome": "Updated Name", "percentual_comissao": 0.20}
        response = client.patch(
            f"/api/v1/parceiros/{sample_parceiro_data['id']}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["nome"] == "Updated Name"
        assert data["data"]["percentual_comissao"] == 0.20

    def test_delete_parceiro(self, client: TestClient, sample_parceiro_data: dict):
        """Test soft deleting a partner."""
        # Create partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Delete it
        response = client.delete(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_parceiro_resumo(self, client: TestClient, sample_parceiro_data: dict):
        """Test getting partner summary."""
        # Create partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        response = client.get(f"/api/v1/parceiros/{sample_parceiro_data['id']}/resumo")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "total_leads" in data["data"]
        assert "total_vendas" in data["data"]
        assert "total_comissao" in data["data"]
