"""
Tests for Parceiros API endpoints.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


class TestParceirosEndpoints:
    """Test partner-related endpoints."""

    def test_get_solicitacoes_by_parceiro(self, client: TestClient, mocker):
        """Test getting solicitations for a specific partner."""
        parceiro_id = "UBER_123"
        mock_solicitacoes_data = [
            {
                "id": "SOL_1",
                "protocolo": "SOL-2026-000001",
                "parceiro_id": parceiro_id,
                "vidas": [{"idade": 30}],
                "cobertura": "nacional",
                "status": "nova",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "tipo_contratacao": "pf",
                "cpf": "12345678900",
            }
        ]

        # Mock the service method's dependencies instead of the method itself
        mocker.patch(
            "src.services.parceiros.ParceiroService.get_by_id_or_raise",
            new_callable=AsyncMock,
            return_value={"id": parceiro_id, "nome": "Test Partner"},
        )
        mocker.patch(
            "src.services.parceiros.SolicitacaoRepository.find_by_parceiro_id",
            new_callable=AsyncMock,
            return_value=mock_solicitacoes_data,
        )

        response = client.get(f"/api/v1/parceiros/{parceiro_id}/solicitacoes")

        assert response.status_code == 200
        data = response.json()
        assert len(data["solicitacoes"]) == 1
        assert data["solicitacoes"][0]["parceiro_id"] == parceiro_id

    def test_create_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test creating a new partner."""
        response = client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == sample_parceiro_data["id"]
        assert data["data"]["nome"] == sample_parceiro_data["nome"]
        assert data["data"]["ativo"] is True

    def test_get_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test getting a partner by ID."""
        # First create the partner
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Then retrieve it
        response = client.get(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == sample_parceiro_data["id"]

    def test_get_parceiro_not_found(self, client: TestClient, db):
        """Test getting a non-existent partner."""
        response = client.get("/api/v1/parceiros/UBER_NONEXISTENT")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_list_parceiros(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test listing partners."""
        # Create a partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        response = client.get("/api/v1/parceiros")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_update_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
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

    def test_delete_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test soft deleting a partner."""
        # Create partner first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Delete it
        response = client.delete(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_parceiro_resumo(self, client: TestClient, sample_parceiro_data: dict, db):
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
