# src/services/solicitacao_service.py
"""
Business logic for managing Solicitações de Cotação.
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.parceiro import ParceiroResumoSolicitacao
from src.api.schemas.solicitacao import (
    SolicitacaoCreate,
    SolicitacaoInDB,
    SolicitacaoListItem,
    DadosComerciaisSchema,
    HistoricoStatusSchema,
)
from src.core.exceptions import NotFoundException
# The following import is incorrect because 'src.db.repositories' is not a package
# due to a file conflict or incorrect structure.
# We will correct this by importing from the new __init__.py
from src.db.repositories.solicitacao_repository import SolicitacaoRepository
from src.db.repositories.parceiro_repository import ParceiroRepository

logger = logging.getLogger(__name__)


class SolicitacaoService:
    """
    Service layer for handling business logic related to solicitations.
    """

    def __init__(self, db: BaseClient):
        self.db = db
        self.solicitacao_repo = SolicitacaoRepository(db)
        self.parceiro_repo = ParceiroRepository(db)
        
    async def get_solicitacao(self, solicitacao_id: str) -> Dict[str, Any]:
        """Retrieves a single solicitation by its ID."""
        return await self.solicitacao_repo.get_or_raise(solicitacao_id)

    async def get_all_solicitacoes_resumo(self) -> List[Dict[str, Any]]:
        """
        Retrieves a summary list of all solicitations, enriching them with
        partner information.
        """
        solicitacoes_data = await self.solicitacao_repo.get_all_resumo()

        # Fetch all required partners in a single batch to optimize
        parceiro_ids = {
            s["parceiro_id"] for s in solicitacoes_data if "parceiro_id" in s
        }
        parceiros_map = {}
        if parceiro_ids:
            parceiros_docs = await self.parceiro_repo.get_many(list(parceiro_ids))
            parceiros_map = {doc["id"]: doc for doc in parceiros_docs}

        # Build the final list
        result_list = []
        for solicitacao_dict in solicitacoes_data:
            parceiro_id = solicitacao_dict.get("parceiro_id")
            parceiro_info = None
            if parceiro_id and parceiro_id in parceiros_map:
                parceiro_data = parceiros_map[parceiro_id]
                parceiro_info = ParceiroResumoSolicitacao(
                    id=parceiro_data.get("id"),
                    nome=parceiro_data.get("nome"),
                    codigo_cartao=parceiro_data.get("codigo_cartao"),
                )

            # Ensure 'vidas' and 'cobertura' have default values if missing in DB
            # This is a safeguard, but the repo query should fetch them.
            solicitacao_dict.setdefault("vidas", [])
            solicitacao_dict.setdefault("cobertura", "nacional") # Or some other sensible default

            list_item = SolicitacaoListItem(
                **solicitacao_dict,
                parceiro=parceiro_info,
            )
            result_list.append(list_item.model_dump())

        return result_list

    async def create_solicitacao(self, data: SolicitacaoCreate) -> str:
        """Creates a new solicitation and returns its protocol."""
        logger.info(f"Attempting to create solicitation for partner {data.parceiro_id}")

        # 1. Validate partner existence
        await self.parceiro_repo.get_or_raise(data.parceiro_id)

        # 2. Generate protocol
        # This is a simplified version. A robust implementation might use a counter.
        timestamp = datetime.now(timezone.utc)
        protocolo = f"SOL-{timestamp.strftime('%Y%m%d%H%M%S')}"

        # 3. Prepare data for DB
        solicitacao_db_data = SolicitacaoInDB(
            **data.model_dump(),
            id="",  # Firestore will generate it
            protocolo=protocolo,
            tipo_contratacao=data.tipo_contratacao,
            created_at=timestamp,
            updated_at=timestamp,
        )

        # 4. Create document in Firestore
        doc_ref = await self.solicitacao_repo.create(solicitacao_db_data.model_dump(exclude={"id"}))
        logger.info(f"Successfully created solicitation with ID {doc_ref.id} and protocol {protocolo}")

        return protocolo

    async def update_dados_comerciais(self, solicitacao_id: str, dados_update: DadosComerciaisSchema) -> Dict[str, Any]:
        """
        Updates the commercial data for a given solicitation.
        """
        logger.info(f"Updating commercial data for solicitation ID: {solicitacao_id}")

        # Get existing solicitation data to ensure it exists
        await self.solicitacao_repo.get_or_raise(solicitacao_id)

        # Prepare update data for the repository
        # Use model_dump to convert Pydantic model to dictionary
        update_data = {
            "dados_comerciais": dados_update.model_dump()
        }

        # Update the solicitation in the database
        updated_solicitacao = await self.solicitacao_repo.update(solicitacao_id, update_data)
        
        return updated_solicitacao

    async def get_solicitacao_historico(self, solicitacao_id: str) -> List[HistoricoStatusSchema]:
        """
        Retrieves the historical status changes for a given solicitation.
        """
        logger.info(f"Fetching history for solicitation ID: {solicitacao_id}")
        
        # Get the full solicitation data
        solicitacao_data = await self.solicitacao_repo.get_or_raise(solicitacao_id)
        
        # Extract historico_status, default to an empty list if not present
        historico_raw = solicitacao_data.get("historico_status", [])
        
        # Convert raw history dictionaries to HistoricoStatusSchema objects
        historico = [HistoricoStatusSchema(**item) for item in historico_raw]
        
        return historico