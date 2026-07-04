# tests/test_solicitacao_workflow_service.py
"""
Unit tests for the SolicitacaoWorkflowService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.solicitacao_workflow_service import SolicitacaoWorkflowService
from src.api.schemas.solicitacao import StatusSolicitacao
from src.core.exceptions import ConflictException, NotFoundException

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_db_client():
    """Fixture for a mocked Firestore client."""
    return MagicMock()


@pytest.fixture
def workflow_service(mock_db_client):
    """Fixture for the SolicitacaoWorkflowService with a mocked repository."""
    with patch('src.services.solicitacao_workflow_service.SolicitacaoRepository') as MockRepo:
        service = SolicitacaoWorkflowService(mock_db_client)
        service.solicitacao_repo = MockRepo.return_value
        service.solicitacao_repo.get_or_raise = AsyncMock()
        service.solicitacao_repo.update = AsyncMock()
        yield service


async def test_alterar_status_valid_transition(workflow_service: SolicitacaoWorkflowService):
    """
    Should update status and history for a valid transition.
    """
    solicitacao_id = "sol_123"
    usuario = "test_user"
    solicitacao_inicial = {
        "id": solicitacao_id,
        "status": StatusSolicitacao.NOVA.value,
        "historico_status": []
    }
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial

    await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.WHATSAPP_INICIADO, usuario)

    workflow_service.solicitacao_repo.update.assert_called_once()
    
    # Check the update payload
    update_args = workflow_service.solicitacao_repo.update.call_args[0][1]
    assert update_args["status"] == StatusSolicitacao.WHATSAPP_INICIADO.value
    assert len(update_args["historico_status"]) == 1
    
    history_entry = update_args["historico_status"][0]
    assert history_entry["status"] == StatusSolicitacao.WHATSAPP_INICIADO.value
    assert history_entry["usuario"] == usuario
    assert "updated_at" in update_args


async def test_alterar_status_invalid_transition(workflow_service: SolicitacaoWorkflowService):
    """
    Should raise ConflictException for an invalid transition.
    """
    solicitacao_id = "sol_123"
    solicitacao_inicial = {"id": solicitacao_id, "status": StatusSolicitacao.NOVA.value}
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial

    with pytest.raises(ConflictException, match="Invalid status transition from 'nova' to 'em_atendimento'"):
        await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.EM_ATENDIMENTO)
    
    workflow_service.solicitacao_repo.update.assert_not_called()


async def test_alterar_status_not_found(workflow_service: SolicitacaoWorkflowService):
    """
    Should raise NotFoundException if solicitation doesn't exist.
    """
    solicitacao_id = "sol_not_found"
    workflow_service.solicitacao_repo.get_or_raise.side_effect = NotFoundException("Solicitacao", solicitacao_id)

    with pytest.raises(NotFoundException):
        await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.PERDIDA)


@pytest.mark.parametrize("initial_status", [
    StatusSolicitacao.NOVA,
    StatusSolicitacao.WHATSAPP_INICIADO,
    StatusSolicitacao.EM_ATENDIMENTO,
    StatusSolicitacao.PROPOSTA_ENVIADA,
])
async def test_alterar_status_to_perdida_is_valid(workflow_service: SolicitacaoWorkflowService, initial_status: StatusSolicitacao):
    """
    Should allow transitioning to PERDIDA from any state except CONVERTIDA.
    """
    solicitacao_id = "sol_123"
    solicitacao_inicial = {"id": solicitacao_id, "status": initial_status.value}
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial
    
    await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.PERDIDA)

    workflow_service.solicitacao_repo.update.assert_called_once()
    update_args = workflow_service.solicitacao_repo.update.call_args[0][1]
    assert update_args["status"] == StatusSolicitacao.PERDIDA.value


async def test_alterar_status_from_convertida_is_invalid(workflow_service: SolicitacaoWorkflowService):
    """
    Should raise ConflictException when transitioning from CONVERTIDA.
    """
    solicitacao_id = "sol_123"
    solicitacao_inicial = {"id": solicitacao_id, "status": StatusSolicitacao.CONVERTIDA.value}
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial

    with pytest.raises(ConflictException):
        await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.PERDIDA)


async def test_alterar_status_from_perdida_is_invalid(workflow_service: SolicitacaoWorkflowService):
    """
    Should raise ConflictException when transitioning from PERDIDA.
    """
    solicitacao_id = "sol_123"
    solicitacao_inicial = {"id": solicitacao_id, "status": StatusSolicitacao.PERDIDA.value}
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial

    with pytest.raises(ConflictException):
        await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.NOVA)


async def test_history_is_appended(workflow_service: SolicitacaoWorkflowService):
    """
    Should append to existing history, not overwrite it.
    """
    solicitacao_id = "sol_123"
    existing_history = [{
        "status": StatusSolicitacao.NOVA.value,
        "data": datetime.utcnow(),
        "usuario": "system"
    }]
    solicitacao_inicial = {
        "id": solicitacao_id,
        "status": StatusSolicitacao.NOVA.value,
        "historico_status": existing_history
    }
    workflow_service.solicitacao_repo.get_or_raise.return_value = solicitacao_inicial

    await workflow_service.alterar_status(solicitacao_id, StatusSolicitacao.WHATSAPP_INICIADO)

    workflow_service.solicitacao_repo.update.assert_called_once()
    update_args = workflow_service.solicitacao_repo.update.call_args[0][1]
    
    assert len(update_args["historico_status"]) == 2
    assert update_args["historico_status"][0]["status"] == StatusSolicitacao.NOVA.value
    assert update_args["historico_status"][1]["status"] == StatusSolicitacao.WHATSAPP_INICIADO.value
