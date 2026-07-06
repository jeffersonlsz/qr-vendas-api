# src/services/solicitacao_workflow_service.py
"""
Service layer for managing the status workflow of a Solicitação de Cotação.
"""
import logging
from datetime import datetime
from typing import Optional

from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.solicitacao import HistoricoStatusSchema, StatusSolicitacao
from src.core.exceptions import ConflictException
from src.db.repositories import SolicitacaoRepository

logger = logging.getLogger(__name__)


class SolicitacaoWorkflowService:
    """
    Orchestrates the business logic for status changes in a Solicitação.
    """
    VALID_TRANSITIONS = {
        StatusSolicitacao.NOVA: [
            StatusSolicitacao.EM_ATENDIMENTO,
            StatusSolicitacao.PERDIDA,
        ],

        StatusSolicitacao.EM_ATENDIMENTO: [
            StatusSolicitacao.CONVERTIDA,
            StatusSolicitacao.PERDIDA,
        ],

        StatusSolicitacao.PERDIDA: [
            StatusSolicitacao.EM_ATENDIMENTO,
        ],

        StatusSolicitacao.CONVERTIDA: [],
    }

    def __init__(self, db: BaseClient):
        """
        Initialize the service.

        Args:
            db: Firestore client.
        """
        self.db = db
        self.solicitacao_repo = SolicitacaoRepository(db)

    async def alterar_status(
        self,
        solicitacao_id: str,
        novo_status: StatusSolicitacao,
        usuario: Optional[str] = None,
    ):
        """
        Changes the status of a solicitation, validating the transition and recording the history.

        Args:
            solicitacao_id: The ID of the solicitation to update.
            novo_status: The new status to apply.
            usuario: The user performing the action.

        Raises:
            NotFoundException: If the solicitation is not found.
            ConflictException: If the status transition is invalid.
        """
        logger.info(f"Attempting to change status of solicitation {solicitacao_id} to {novo_status.value}")

        solicitacao = await self.solicitacao_repo.get_or_raise(solicitacao_id)
        status_atual = StatusSolicitacao(solicitacao["status"])

        if novo_status not in self.VALID_TRANSITIONS.get(status_atual, []):
            raise ConflictException(
                f"Invalid status transition from '{status_atual.value}' to '{novo_status.value}'"
            )

        now = datetime.utcnow()

        # Create history entry
        historico_entry = HistoricoStatusSchema(
            status=novo_status,
            data=now,
            usuario=usuario,
        )

        # Get current history or initialize it
        historico_atual = solicitacao.get("historico_status") or []
        
        # Append new entry (as dict for Firestore)
        historico_atual.append(historico_entry.model_dump())

        # Prepare data for update
        update_data = {
            "status": novo_status.value,
            "historico_status": historico_atual,
            "updated_at": now,
        }

        await self.solicitacao_repo.update(solicitacao_id, update_data)
        logger.info(f"Successfully changed status of solicitation {solicitacao_id} to {novo_status.value}")

