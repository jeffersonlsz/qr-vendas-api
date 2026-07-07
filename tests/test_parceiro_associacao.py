# tests/test_parceiro_associacao.py
"""
Tests for the Parceiro Card Association endpoint.
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from src.services.parceiros import ParceiroService

# Helper to create a partner directly for testing
async def create_test_parceiro(
    parceiro_service: ParceiroService,
    parceiro_id: str,
    status_cartao: str,
    numero_sequencial: int,
    nome_prefix="Parceiro"
):
    """Creates a partner document directly in Firestore for testing."""
    codigo_cartao = f"PREFIXO-{numero_sequencial:06d}"
    created_at = datetime.now(timezone.utc)
    parceiro_data = {
        "id": parceiro_id,
        "nome": f"{nome_prefix} {numero_sequencial}",
        "telefone": "",
        "percentual_comissao": 0.1,
        "status_cartao": status_cartao,
        "numero_sequencial": numero_sequencial,
        "codigo_cartao": codigo_cartao,
        "data_entrega_cartao": None,
        "entregue_por": None,
        "ativo": True,
        "created_at": created_at,
        "updated_at": created_at,
    }
    parceiro_service.collection.document(parceiro_id).set(parceiro_data)
    # Return a serializable version for comparison
    parceiro_data["created_at"] = created_at.isoformat().replace("+00:00", "Z")
    parceiro_data["updated_at"] = parceiro_data["created_at"]
    return parceiro_data


class TestAssociarCartaoEndpoint:
    """Test suite for the POST /parceiros/{parceiro_id}/associar endpoint."""

    @pytest.mark.asyncio
    async def test_associar_cartao_disponivel_success(
        self, client: TestClient, parceiro_service: ParceiroService
    ):
        """Scenario 1: Test successful association of a 'DISPONIVEL' card."""
        parceiro_disponivel = await create_test_parceiro(
            parceiro_service, "PARCEIRO_DISPONIVEL_1", "DISPONIVEL", 9001
        )
        parceiro_id = parceiro_disponivel["id"]
        
        associacao_data = {
            "nome": "João Carlos da Silva",
            "telefone": "61988887777",
            "percentual_comissao": 0.15,
            "ativo": True,
        }

        response = client.post(
            f"/api/v1/parceiros/{parceiro_id}/associar", json=associacao_data
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert data["nome"] == associacao_data["nome"]
        assert data["status_cartao"] == "EM_USO"
        assert data["data_entrega_cartao"] is not None

    @pytest.mark.asyncio
    async def test_associar_cartao_em_uso_conflict(
        self, client: TestClient, parceiro_service: ParceiroService
    ):
        """Scenario 2: Test associating a card that is already 'EM_USO'."""
        parceiro_em_uso = await create_test_parceiro(
            parceiro_service, "PARCEIRO_EM_USO_1", "EM_USO", 9002
        )
        parceiro_id = parceiro_em_uso["id"]
        
        associacao_data = {"nome": "Maria Joana", "telefone": "61955554444"}

        response = client.post(
            f"/api/v1/parceiros/{parceiro_id}/associar", json=associacao_data
        )

        assert response.status_code == 409
        data = response.json()
        assert data["message"] == "Este cartão já foi associado a um parceiro."

    @pytest.mark.asyncio
    async def test_immutable_fields_remain_unchanged(
        self, client: TestClient, parceiro_service: ParceiroService
    ):
        """Scenarios 3, 4, 5: Verify key fields remain unchanged."""
        parceiro_disponivel = await create_test_parceiro(
            parceiro_service, "PARCEIRO_DISPONIVEL_2", "DISPONIVEL", 9003
        )
        parceiro_id = parceiro_disponivel["id"]

        associacao_data = {"nome": "Final Name", "telefone": "61911112222"}

        response = client.post(
            f"/api/v1/parceiros/{parceiro_id}/associar", json=associacao_data
        )

        assert response.status_code == 200
        data = response.json()["data"]

        assert data["codigo_cartao"] == parceiro_disponivel["codigo_cartao"]
        assert data["numero_sequencial"] == parceiro_disponivel["numero_sequencial"]
        assert data["created_at"] == parceiro_disponivel["created_at"]
        assert data["id"] == parceiro_disponivel["id"]

    @pytest.mark.asyncio
    async def test_associated_partner_appears_in_list(
        self, client: TestClient, parceiro_service: ParceiroService
    ):
        """Scenario 6: Verify the associated partner appears correctly in lists."""
        parceiro_disponivel = await create_test_parceiro(
            parceiro_service, "PARCEIRO_DISPONIVEL_3", "DISPONIVEL", 9004
        )
        parceiro_id = parceiro_disponivel["id"]

        associacao_data = {"nome": "Listed Partner", "telefone": "61933334444"}
        client.post(f"/api/v1/parceiros/{parceiro_id}/associar", json=associacao_data)

        response = client.get("/api/v1/parceiros")
        assert response.status_code == 200
        
        listed_partners = response.json()["data"]
        found = any(
            p["id"] == parceiro_id and p["status_cartao"] == "EM_USO"
            for p in listed_partners
        )
        assert found, f"Partner {parceiro_id} not found in list after association."
