"""
Tests for Parceiros API endpoints.
"""

from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock


@pytest.fixture(scope="function")
def operador_valido(db):
    """Creates a valid, active operator for testing."""
    operador_ref = db.collection("operadores")
    operador_id = "OPERADOR_VALIDO_123"
    operador_data = {"id": operador_id, "nome": "Operador Valido", "telefone": "61999998888", "ativo": True}
    doc_ref = operador_ref.document(operador_id)
    doc_ref.set(operador_data)
    yield operador_data
    doc_ref.delete()

@pytest.fixture(scope="function")
def operador_inativo(db):
    """Creates an inactive operator for testing."""
    operador_ref = db.collection("operadores")
    operador_id = "OPERADOR_INATIVO_456"
    operador_data = {"id": operador_id, "nome": "Operador Inativo", "telefone": "61977776666", "ativo": False}
    doc_ref = operador_ref.document(operador_id)
    doc_ref.set(operador_data)
    yield operador_data
    doc_ref.delete()

@pytest.fixture
def sample_parceiro_data():
    return {
        "id": "UBER_123",
        "nome": "Test Partner",
        "telefone": "+5561999999999",
        "percentual_comissao": 0.1,
    }


class TestCreateParceirosLote:
    """Tests for the POST /parceiros/lote endpoint."""

    API_URL = "/api/v1/parceiros/lote"

    def test_create_lote_success(self, client: TestClient, operador_valido, db):
        """Test creating a batch of partners successfully with a valid operator."""
        payload = {"quantidade": 3, "prefixo_nome": "LoteSucesso", "operador_id": operador_valido["id"]}
        
        response = client.post(self.API_URL, json=payload)
        
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["quantidade_criada"] == 3

        # Verify one of the created partners
        parceiros = db.collection("parceiros").where("operador_id", "==", operador_valido["id"]).stream()
        created_partner = next(p for p in parceiros if p.to_dict()["nome"].startswith("LoteSucesso"))
        
        assert created_partner is not None
        partner_dict = created_partner.to_dict()
        assert partner_dict["operador_id"] == operador_valido["id"]
        assert partner_dict["operador_nome"] == operador_valido["nome"]
        assert partner_dict["operador_telefone"] == operador_valido["telefone"]

    def test_create_lote_fails_without_operador_id(self, client: TestClient):
        """Test that request fails if operador_id is missing."""
        payload = {"quantidade": 5, "prefixo_nome": "LoteFalha"}
        response = client.post(self.API_URL, json=payload)
        
        assert response.status_code == 422  # ValidationException
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "ValidationException"
        assert "obrigatório" in data["message"]

    def test_create_lote_fails_with_nonexistent_operador_id(self, client: TestClient):
        """Test that request fails if operador_id does not exist."""
        payload = {"quantidade": 5, "prefixo_nome": "LoteFalha", "operador_id": "OP_NAOEXISTE"}
        response = client.post(self.API_URL, json=payload)
        
        assert response.status_code == 404  # NotFoundException
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "NotFoundException"

    def test_create_lote_fails_with_inactive_operador_id(self, client: TestClient, operador_inativo):
        """Test that request fails if the operator is inactive."""
        payload = {"quantidade": 5, "prefixo_nome": "LoteFalha", "operador_id": operador_inativo["id"]}
        response = client.post(self.API_URL, json=payload)
        
        assert response.status_code == 422  # ValidationException
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == "ValidationException"
        assert "is not active" in data["message"]


class TestParceirosEndpoints:
    """Test partner-related endpoints."""

    def test_list_parceiros_with_operator_fields(self, client: TestClient, operador_valido):
        """Test that listing partners includes new operator fields."""
        # Create a batch with an operator
        client.post("/api/v1/parceiros/lote", json={"quantidade": 1, "operador_id": operador_valido["id"]})
        
        response = client.get("/api/v1/parceiros")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert len(data["data"]) > 0
        
        partner_with_op = data["data"][0]
        assert "operador_id" in partner_with_op
        assert "operador_nome" in partner_with_op
        assert "operador_telefone" in partner_with_op
        assert partner_with_op["operador_id"] == operador_valido["id"]

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

        mocker.patch("src.services.parceiros.ParceiroService.get_by_id_or_raise", new_callable=AsyncMock, return_value={"id": parceiro_id, "nome": "Test Partner"})
        mocker.patch("src.db.repositories.SolicitacaoRepository.find_by_parceiro_id", new_callable=AsyncMock, return_value=mock_solicitacoes_data)

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
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        response = client.get(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_parceiro_data["id"]

    def test_get_parceiro_not_found(self, client: TestClient):
        """Test getting a non-existent partner."""
        response = client.get("/api/v1/parceiros/UBER_NONEXISTENT")
        assert response.status_code == 404

    def test_update_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test updating a partner."""
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        update_data = {"nome": "Updated Name", "percentual_comissao": 0.20}
        response = client.patch(f"/api/v1/parceiros/{sample_parceiro_data['id']}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["nome"] == "Updated Name"

    def test_delete_parceiro(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test soft deleting a partner."""
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        response = client.delete(f"/api/v1/parceiros/{sample_parceiro_data['id']}")
        assert response.status_code == 200

    def test_get_parceiro_resumo(self, client: TestClient, sample_parceiro_data: dict, db):
        """Test getting partner summary."""
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        response = client.get(f"/api/v1/parceiros/{sample_parceiro_data['id']}/resumo")
        assert response.status_code == 200
