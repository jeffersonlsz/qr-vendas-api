# tests/test_solicitacoes.py
"""
Tests for the /solicitacoes endpoint (Solicitação de Cotação feature).
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from pytest_mock import MockerFixture
from datetime import datetime

VALID_PAYLOAD = {
    "parceiro_id": "VALID_PARCEIRO_ID",
    "vidas": [{"idade": 30}, {"idade": 45}],
    "cobertura": "regional",
    "cidade": "Brasília",
    "uf": "DF",
    "operadoras_preferidas": ["Amil", "Bradesco Saúde"]
}


def test_get_all_solicitacoes_success(client: TestClient, mocker: MockerFixture):
    """
    Test successful retrieval of all solicitations.
    """
    mock_solicitacoes = [
        {
            "id": "SOL_1",
            "protocolo": "SOL-2026-000001",
            "parceiro_id": "PARC_1",
            "vidas": [{"idade": 30}],
            "cobertura": "nacional",
            "status": "nova",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
        {
            "id": "SOL_2",
            "protocolo": "SOL-2026-000002",
            "parceiro_id": "PARC_2",
            "vidas": [{"idade": 45}, {"idade": 50}],
            "cobertura": "regional",
            "cidade": "Goiânia",
            "uf": "GO",
            "status": "em_atendimento",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        },
    ]

    mock_service_instance = MagicMock()
    mock_service_instance.get_all_solicitacoes = AsyncMock(return_value=mock_solicitacoes)

    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service_instance
    )

    response = client.get("/api/v1/solicitacoes")

    assert response.status_code == 200
    response_data = response.json()
    assert "solicitacoes" in response_data
    assert len(response_data["solicitacoes"]) == 2
    assert response_data["solicitacoes"][0]["protocolo"] == "SOL-2026-000001"
    mock_service_instance.get_all_solicitacoes.assert_called_once()


def test_create_solicitacao_success(client: TestClient, mocker: MockerFixture):
    """
    Test successful creation of a new solicitation.
    """
    # Mock the service layer to isolate the endpoint
    mock_service_instance = MagicMock()
    mock_service_instance.create_solicitacao = AsyncMock(return_value="SOL-2026-000001")
    
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service_instance
    )

    response = client.post("/api/v1/solicitacoes", json=VALID_PAYLOAD)

    assert response.status_code == 201
    assert response.json() == {"protocolo": "SOL-2026-000001"}
    
    # Verify that the service was called correctly
    mock_service_instance.create_solicitacao.assert_called_once()


def test_create_solicitacao_parceiro_not_found(client: TestClient, mocker: MockerFixture):
    """
    Test solicitation creation fails when parceiro_id is not found.
    """
    from src.core.exceptions import NotFoundException

    mock_service_instance = MagicMock()
    mock_service_instance.create_solicitacao = AsyncMock(
        side_effect=NotFoundException("Parceiro", "INVALID_PARCEIRO_ID")
    )
    
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service_instance
    )

    payload = VALID_PAYLOAD.copy()
    payload["parceiro_id"] = "INVALID_PARCEIRO_ID"
    
    response = client.post("/api/v1/solicitacoes", json=payload)

    assert response.status_code == 404
    assert "Parceiro with ID INVALID_PARCEIRO_ID not found" in response.json()["detail"]


def test_create_solicitacao_invalid_data(client: TestClient):
    """
    Test solicitation creation fails with invalid data (422).
    """
    payload = VALID_PAYLOAD.copy()
    payload["cobertura"] = "INVALID_COBERTURA"  # Invalid enum value

    response = client.post("/api/v1/solicitacoes", json=payload)

    assert response.status_code == 422


def test_create_solicitacao_internal_server_error(client: TestClient, mocker: MockerFixture):
    """
    Test that a generic exception in the service layer returns a 500 error.
    """
    mock_service_instance = MagicMock()
    mock_service_instance.create_solicitacao = AsyncMock(
        side_effect=Exception("A generic, unexpected error occurred")
    )

    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service_instance
    )

    response = client.post("/api/v1/solicitacoes", json=VALID_PAYLOAD)

    assert response.status_code == 500
    assert "internal error" in response.json()["detail"].lower()


def test_alterar_status_success(client: TestClient, mocker: MockerFixture):
    """
    Test successful status change of a solicitation.
    """
    solicitacao_id = "SOL_123"
    updated_solicitacao = {
        "id": solicitacao_id,
        "status": "em_atendimento",
        "protocolo": "SOL-PROTO-1",
        "parceiro_id": "PARC_1",
        "vidas": [{"idade": 30}],
        "cobertura": "nacional",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    mock_workflow_service = MagicMock()
    mock_workflow_service.alterar_status = AsyncMock()
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoWorkflowService",
        return_value=mock_workflow_service
    )

    mock_repo = MagicMock()
    mock_repo.get_or_raise = AsyncMock(return_value=updated_solicitacao)
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoRepository",
        return_value=mock_repo
    )

    response = client.patch(
        f"/api/v1/solicitacoes/{solicitacao_id}/status",
        json={"status": "em_atendimento"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "em_atendimento"
    mock_repo.get_or_raise.assert_called_once_with(solicitacao_id)


def test_alterar_status_conflict(client: TestClient, mocker: MockerFixture):
    """
    Test that a 409 Conflict error is returned for an invalid status transition.
    """
    from src.core.exceptions import ConflictException
    solicitacao_id = "SOL_123"

    mock_workflow_service = MagicMock()
    mock_workflow_service.alterar_status = AsyncMock(
        side_effect=ConflictException("Invalid transition from 'nova' to 'em_atendimento'")
    )
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoWorkflowService",
        return_value=mock_workflow_service
    )

    response = client.patch(
        f"/api/v1/solicitacoes/{solicitacao_id}/status",
        json={"status": "em_atendimento"}  # Valid status, but invalid transition
    )

    assert response.status_code == 409
    assert "Invalid transition" in response.json()["detail"]


def test_update_dados_comerciais_success(client: TestClient, mocker: MockerFixture):
    """
    Test successful partial update of commercial data.
    """
    solicitacao_id = "SOL_123"
    update_payload = {"vendedor": "Novo Vendedor", "valor_mensal": 123.45}
    
    # Mock a full solicitation object for the response model
    updated_solicitacao = {
        "id": solicitacao_id,
        "protocolo": "SOL-PROTO-1",
        "parceiro_id": "PARC_1",
        "vidas": [{"idade": 30}],
        "cobertura": "nacional",
        "status": "nova",
        "dados_comerciais": {
            "vendedor": "Novo Vendedor",
            "valor_mensal": 123.45,
            "operadora": None,
            "plano": None,
            "valor_adesao": None,
            "observacoes": None
        },
        "historico_status": None,
        "motivo_perda": None,
        "cidade": None,
        "uf": None,
        "cpf": None,
        "cnpj": None,
        "tipo_contratacao": None,
        "operadoras_preferidas": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    mock_service = MagicMock()
    mock_service.update_dados_comerciais = AsyncMock(return_value=updated_solicitacao)
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service
    )

    response = client.patch(
        f"/api/v1/solicitacoes/{solicitacao_id}/dados-comerciais",
        json=update_payload
    )

    assert response.status_code == 200
    assert response.json()["dados_comerciais"]["vendedor"] == "Novo Vendedor"
    mock_service.update_dados_comerciais.assert_called_once()


def test_update_dados_comerciais_not_found(client: TestClient, mocker: MockerFixture):
    """
    Test that updating commercial data for a non-existent solicitation returns 404.
    """
    from src.core.exceptions import NotFoundException
    solicitacao_id = "SOL_404"

    mock_service = MagicMock()
    mock_service.update_dados_comerciais = AsyncMock(
        side_effect=NotFoundException("Solicitacao", solicitacao_id)
    )
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service
    )

    response = client.patch(
        f"/api/v1/solicitacoes/{solicitacao_id}/dados-comerciais",
        json={"vendedor": "Test"}
    )

    assert response.status_code == 404


def test_get_historico_success(client: TestClient, mocker: MockerFixture):
    """
    Test successful retrieval of status history.
    """
    solicitacao_id = "SOL_123"
    mock_history = [
        {"status": "nova", "data": datetime.utcnow().isoformat(), "usuario": None},
        {"status": "em_atendimento", "data": datetime.utcnow().isoformat(), "usuario": "api_user"},
    ]
    mock_service = MagicMock()
    mock_service.get_solicitacao_historico = AsyncMock(return_value=mock_history)
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service
    )

    response = client.get(f"/api/v1/solicitacoes/{solicitacao_id}/historico")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["status"] == "nova"
    assert response.json()[1]["status"] == "em_atendimento"
    mock_service.get_solicitacao_historico.assert_called_once_with(solicitacao_id)


def test_get_historico_not_found(client: TestClient, mocker: MockerFixture):
    """
    Test that retrieving history for a non-existent solicitation returns 404.
    """
    from src.core.exceptions import NotFoundException
    solicitacao_id = "SOL_404"

    mock_service = MagicMock()
    mock_service.get_solicitacao_historico = AsyncMock(
        side_effect=NotFoundException("Solicitacao", solicitacao_id)
    )
    mocker.patch(
        "src.api.routers.solicitacoes.SolicitacaoService",
        return_value=mock_service
    )

    response = client.get(f"/api/v1/solicitacoes/{solicitacao_id}/historico")

    assert response.status_code == 404
