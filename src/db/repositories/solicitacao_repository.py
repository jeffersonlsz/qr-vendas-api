# src/db/repositories/solicitacao_repository.py
"""
Repository for handling database operations for Solicitações.
"""
import logging
import asyncio
from typing import List, Dict, Any

from google.cloud.firestore_v1.base_client import BaseClient

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SolicitacaoRepository(BaseRepository):
    """
    Manages database interactions for the 'solicitacoes' collection.
    """

    def __init__(self, db: BaseClient):
        """
        Initializes the repository for the 'solicitacoes' collection.
        """
        super().__init__(db, "solicitacoes")

    async def get_all_resumo(self) -> List[Dict[str, Any]]:
        """
        Retrieves a summary list of all solicitations, including essential fields
        for the list view like 'vidas' and 'cobertura'.
        """
        logger.info("Fetching summary for all solicitations from Firestore.")
        query = self.collection.select([
            "protocolo", "status", "cidade", "uf", "parceiro_id",
            "created_at", "vidas", "cobertura"
        ]).order_by("created_at", direction="DESCENDING")

        docs = await asyncio.to_thread(lambda: list(query.stream()))

        solicitacoes = [
            {"id": doc.id, **doc.to_dict()} for doc in docs
        ]
        logger.info(f"Found {len(solicitacoes)} solicitations.")
        return solicitacoes

    async def find_by_parceiro_id(self, parceiro_id: str) -> List[Dict[str, Any]]:
        """
        Finds solicitations by a 'parceiro_id'.
        """
        self.logger.info(f"Finding solicitations for parceiro_id: {parceiro_id}")
        return await self.list(filters=[("parceiro_id", "==", parceiro_id)])