"""
Tests for Vendas API endpoints.
"""
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient


class TestVendasEndpoints:
    """Test sale-related endpoints."""
    
    def test_create_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_solicitacao_data: dict,
        sample_venda_data: dict,
    ):
        """Test creating a new sale."""
        # Arrange: Create partner and mock solicitation/partner services for sale creation
        client.post("/api/v1/parceiros", json=sample_parceiro_data)

        solicitacao_id = sample_venda_data["solicitacao_id"]
        mock_solicitacao = {**sample_solicitacao_data, "id": solicitacao_id}

        with patch("src.services.vendas.VendaService._validate_solicitacao", new_callable=AsyncMock) as mock_validate_sol, \
             patch("src.services.vendas.VendaService._get_parceiro", new_callable=AsyncMock) as mock_get_parceiro, \
             patch("src.services.vendas.VendaService._update_solicitacao_status", new_callable=AsyncMock):

            mock_validate_sol.return_value = mock_solicitacao
            mock_get_parceiro.return_value = sample_parceiro_data

            # Act: Create sale
            response = client.post("/api/v1/vendas", json=sample_venda_data)

        # Assert
        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["data"]["solicitacao_id"] == solicitacao_id
        assert data["data"]["parceiro_id"] == sample_parceiro_data["id"]
        assert data["data"]["comissao"] > 0

    def test_get_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_solicitacao_data: dict,
        sample_venda_data: dict,
    ):
        """Test getting a sale by ID."""
        # Arrange
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        with patch("src.services.vendas.VendaService._validate_solicitacao", new_callable=AsyncMock) as mock_validate_sol, \
             patch("src.services.vendas.VendaService._get_parceiro", new_callable=AsyncMock) as mock_get_parceiro, \
             patch("src.services.vendas.VendaService._update_solicitacao_status", new_callable=AsyncMock):
            
            mock_validate_sol.return_value = {**sample_solicitacao_data, "id": sample_venda_data["solicitacao_id"]}
            mock_get_parceiro.return_value = sample_parceiro_data
            
            create_response = client.post("/api/v1/vendas", json=sample_venda_data)
            venda_id = create_response.json()["data"]["id"]

        # Act
        response = client.get(f"/api/v1/vendas/{venda_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"]["id"] == venda_id

    def test_mark_venda_as_paid(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_solicitacao_data: dict,
        sample_venda_data: dict,
    ):
        """Test marking a sale as paid."""
        # Arrange
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        with patch("src.services.vendas.VendaService._validate_solicitacao", new_callable=AsyncMock) as mock_validate_sol, \
             patch("src.services.vendas.VendaService._get_parceiro", new_callable=AsyncMock) as mock_get_parceiro, \
             patch("src.services.vendas.VendaService._update_solicitacao_status", new_callable=AsyncMock):
            
            mock_validate_sol.return_value = {**sample_solicitacao_data, "id": sample_venda_data["solicitacao_id"]}
            mock_get_parceiro.return_value = sample_parceiro_data
            
            create_response = client.post("/api/v1/vendas", json=sample_venda_data)
            venda_id = create_response.json()["data"]["id"]

        # Act
        response = client.post(f"/api/v1/vendas/{venda_id}/pagar")

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["data"]["status"] == "pago"
        assert data["data"]["pago_em"] is not None

    def test_update_venda(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_solicitacao_data: dict,
        sample_venda_data: dict,
    ):
        """Test updating a sale."""
        # Arrange
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        with patch("src.services.vendas.VendaService._validate_solicitacao", new_callable=AsyncMock) as mock_validate_sol, \
             patch("src.services.vendas.VendaService._get_parceiro", new_callable=AsyncMock) as mock_get_parceiro, \
             patch("src.services.vendas.VendaService._update_solicitacao_status", new_callable=AsyncMock):
            
            mock_validate_sol.return_value = {**sample_solicitacao_data, "id": sample_venda_data["solicitacao_id"]}
            mock_get_parceiro.return_value = sample_parceiro_data
            
            create_response = client.post("/api/v1/vendas", json=sample_venda_data)
            venda_id = create_response.json()["data"]["id"]

        # Act
        response = client.patch(
            f"/api/v1/vendas/{venda_id}",
            json={"valor_venda": 2000.00, "descricao": "Updated description"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()

        assert data["data"]["valor_venda"] == 2000.00
        # Commission should be recalculated
        assert data["data"]["comissao"] == 2000.00 * sample_parceiro_data["percentual_comissao"]
