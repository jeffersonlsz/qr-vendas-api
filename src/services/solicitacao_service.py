# src/services/solicitacao_service.py
"""
Service layer for Solicitação de Cotação feature.
"""
import logging
from datetime import datetime

from typing import Any, Dict, List
from google.cloud import firestore
from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.solicitacao import (DadosComerciaisSchema,
                                         SolicitacaoCreate,
                                         StatusSolicitacao)
from src.db.repositories import (ParceiroRepository,
                                 SolicitacaoRepository)
from src.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class SolicitacaoService:
    """
    Orchestrates the business logic for creating and managing solicitações.
    """

    def __init__(self, db: BaseClient):
        """
        Initialize the service.

        Args:
            db: Firestore client.
        """
        self.db = db
        self.solicitacao_repo = SolicitacaoRepository(db)
        self.parceiro_repo = ParceiroRepository(db)

    async def get_all_solicitacoes(self) -> List[Dict[str, Any]]:
        """
        Retrieves all solicitations.

        Returns:
            A list of all solicitations as dictionaries.
        """
        logger.info("Retrieving all solicitations.")
        solicitacoes_data = await self.solicitacao_repo.list()
        return solicitacoes_data

    async def create_solicitacao(self, solicitacao_data: SolicitacaoCreate) -> str:
        """
        Creates a new solicitation, including protocol generation and lead creation.

        Args:
            solicitacao_data: The data for the new solicitation.

        Returns:
            The protocol of the newly created solicitation.
            
        Raises:
            NotFoundException: If the parceiro_id does not exist.
        """
        logger.info("Starting new solicitation creation process.")

        # 1. Validate partner
        parceiro = await self.parceiro_repo.get(solicitacao_data.parceiro_id)
        if not parceiro:
            raise NotFoundException("Parceiro", solicitacao_data.parceiro_id)

        # 2. Prepare data for storage
        now = datetime.utcnow()
        data_to_save = solicitacao_data.model_dump()
        data_to_save.update({
            "protocolo": "placeholder", # Será gerado pelo BaseRepository
            "status": StatusSolicitacao.NOVA.value,
            "tipo_contratacao": solicitacao_data.tipo_contratacao.value if solicitacao_data.tipo_contratacao else None,
            "created_at": now,
            "updated_at": now,
        })
        
        # Convert enums and other complex types to strings/dicts
        data_to_save['cobertura'] = data_to_save['cobertura'].value
        if data_to_save.get('operadoras_preferidas'):
            data_to_save['operadoras_preferidas'] = [op.value for op in data_to_save['operadoras_preferidas']]
        data_to_save['vidas'] = [vida.model_dump() for vida in solicitacao_data.vidas]

        # 3. Create solicitation document
        solicitacao_id = await self.solicitacao_repo.create(data_to_save, id_prefix="SOL")
        logger.info(f"Successfully created solicitation document with ID: {solicitacao_id}")

        # 4. Update protocol with the final generated ID
        protocolo = f"SOL-{solicitacao_id.split('_')[-1].upper()}"
        await self.solicitacao_repo.update(solicitacao_id, {"protocolo": protocolo})

        return protocolo

    async def update_dados_comerciais(
        self, solicitacao_id: str, dados_update: DadosComerciaisSchema
    ) -> Dict[str, Any]:
        """
        Partially updates the commercial data of a solicitation.

        Args:
            solicitacao_id: The ID of the solicitation to update.
            dados_update: The commercial data fields to update.

        Returns:
            The full updated solicitation document.

        Raises:
            NotFoundException: If the solicitation is not found.
        """
        logger.info(f"Updating commercial data for solicitation {solicitacao_id}")

        # Ensure solicitation exists
        solicitacao = await self.solicitacao_repo.get_or_raise(solicitacao_id)

        # Get current data and merge with the update
        current_dados = solicitacao.get("dados_comerciais") or {}
        update_payload = dados_update.model_dump(exclude_unset=True)
        current_dados.update(update_payload)

        # Prepare data for Firestore update
        update_data = {
            "dados_comerciais": current_dados,
            "updated_at": datetime.utcnow(),
        }

        await self.solicitacao_repo.update(solicitacao_id, update_data)
        logger.info(f"Successfully updated commercial data for solicitation {solicitacao_id}")

        # Return the updated document
        return await self.solicitacao_repo.get_or_raise(solicitacao_id)

    async def get_solicitacao_historico(self, solicitacao_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the status history of a solicitation.

        Args:
            solicitacao_id: The ID of the solicitation.

        Returns:
            A list of status history events.

        Raises:
            NotFoundException: If the solicitation is not found.
        """
        logger.info(f"Retrieving history for solicitation {solicitacao_id}")
        solicitacao = await self.solicitacao_repo.get_or_raise(solicitacao_id)
        return solicitacao.get("historico_status") or []
