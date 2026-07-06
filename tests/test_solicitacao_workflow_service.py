# tests/test_solicitacao_workflow_service.py
"""
Unit tests for the SolicitacaoWorkflowService.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.schemas.solicitacao import StatusSolicitacao
from src.core.exceptions import ConflictException, NotFoundException
from src.services.solicitacao_workflow_service import SolicitacaoWorkflowService

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db_client():
    return MagicMock()


@pytest.fixture
def workflow_service(mock_db_client):
    with patch("src.services.solicitacao_workflow_service.SolicitacaoRepository") as MockRepo:
        service = SolicitacaoWorkflowService(mock_db_client)
        service.solicitacao_repo = MockRepo.return_value
        service.solicitacao_repo.get_or_raise = AsyncMock()
        service.solicitacao_repo.update = AsyncMock()
        yield service


async def test_alterar_status_valid_transition(workflow_service):
    solicitacao = {
        "id": "sol_123",
        "status": StatusSolicitacao.NOVA.value,
        "historico_status": [],
    }

    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao

    await workflow_service.alterar_status(
        "sol_123",
        StatusSolicitacao.EM_ATENDIMENTO,
        "usuario",
    )

    workflow_service.solicitacao_repo.update.assert_called_once()

    update = workflow_service.solicitacao_repo.update.call_args[0][1]

    assert update["status"] == StatusSolicitacao.EM_ATENDIMENTO.value
    assert len(update["historico_status"]) == 1
    assert update["historico_status"][-1]["status"] == update["status"]


async def test_alterar_status_invalid_transition(workflow_service):
    solicitacao = {
        "id": "sol_123",
        "status": StatusSolicitacao.EM_ATENDIMENTO.value,
    }

    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao

    with pytest.raises(
        ConflictException,
        match="Invalid status transition from 'em_atendimento' to 'nova'",
    ):
        await workflow_service.alterar_status(
            "sol_123",
            StatusSolicitacao.NOVA,
        )

    workflow_service.solicitacao_repo.update.assert_not_called()


async def test_alterar_status_not_found(workflow_service):
    workflow_service.solicitacao_repo.get_or_raise.side_effect = (
        NotFoundException("Solicitacao", "sol")
    )

    with pytest.raises(NotFoundException):
        await workflow_service.alterar_status(
            "sol",
            StatusSolicitacao.PERDIDA,
        )


@pytest.mark.parametrize(
    "origem,destino",
    [
        (StatusSolicitacao.NOVA, StatusSolicitacao.EM_ATENDIMENTO),
        (StatusSolicitacao.NOVA, StatusSolicitacao.PERDIDA),
        (StatusSolicitacao.EM_ATENDIMENTO, StatusSolicitacao.CONVERTIDA),
        (StatusSolicitacao.EM_ATENDIMENTO, StatusSolicitacao.PERDIDA),
        (StatusSolicitacao.PERDIDA, StatusSolicitacao.EM_ATENDIMENTO),
    ],
)
async def test_valid_transitions(workflow_service, origem, destino):
    solicitacao = {
        "id": "sol_123",
        "status": origem.value,
    }

    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao

    await workflow_service.alterar_status(
        "sol_123",
        destino,
    )

    workflow_service.solicitacao_repo.update.assert_called_once()

    update = workflow_service.solicitacao_repo.update.call_args[0][1]

    assert update["status"] == destino.value
    assert update["historico_status"][-1]["status"] == destino.value

    workflow_service.solicitacao_repo.update.reset_mock()


async def test_alterar_status_from_convertida_is_invalid(workflow_service):
    workflow_service.solicitacao_repo.get_or_raise.return_value = {
        "id": "sol_123",
        "status": StatusSolicitacao.CONVERTIDA.value,
    }

    with pytest.raises(ConflictException):
        await workflow_service.alterar_status(
            "sol_123",
            StatusSolicitacao.PERDIDA,
        )


async def test_history_is_appended(workflow_service):
    existing_history = [
        {
            "status": StatusSolicitacao.NOVA.value,
            "data": datetime.utcnow(),
            "usuario": "system",
        }
    ]

    workflow_service.solicitacao_repo.get_or_raise.return_value = {
        "id": "sol_123",
        "status": StatusSolicitacao.NOVA.value,
        "historico_status": existing_history,
    }

    await workflow_service.alterar_status(
        "sol_123",
        StatusSolicitacao.EM_ATENDIMENTO,
    )

    workflow_service.solicitacao_repo.update.assert_called_once()

    update = workflow_service.solicitacao_repo.update.call_args[0][1]

    assert len(update["historico_status"]) == 2
    assert update["historico_status"][0]["status"] == StatusSolicitacao.NOVA.value
    assert (
        update["historico_status"][1]["status"]
        == StatusSolicitacao.EM_ATENDIMENTO.value
    )
    assert update["historico_status"][-1]["status"] == update["status"]