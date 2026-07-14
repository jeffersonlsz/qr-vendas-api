# src/db/repositories/parceiro_repository.py
"""
Repository for handling database operations for Parceiros.
"""
import logging
import asyncio
from typing import List, Dict, Any

from google.cloud.firestore_v1.base_client import BaseClient

from .base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ParceiroRepository(BaseRepository):
    """
    Manages database interactions for the 'parceiros' collection.
    """

    def __init__(self, db: BaseClient):
        """
        Initializes the repository for the 'parceiros' collection.
        """
        super().__init__(db, "parceiros")

    async def get_many(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieves multiple documents by their IDs in a single batch.
        """
        logger.info(f"Fetching {len(ids)} partners from Firestore.")
        doc_refs = [self.collection.document(id) for id in ids]
        docs = await asyncio.to_thread(self.db.get_all, doc_refs)
        return [self._serialize_doc(doc) for doc in docs if doc.exists]