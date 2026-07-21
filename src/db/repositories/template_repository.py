# src/db/repositories/template_repository.py
"""
Repository for accessing the 'templates' collection in Firestore.
"""
import logging
import asyncio
from typing import Dict, Any
from google.cloud.firestore_v1.base_client import BaseClient
from google.cloud.firestore import SERVER_TIMESTAMP
from src.core.exceptions import NotFoundException
from src.db.repositories.base_repository import BaseRepository
logger = logging.getLogger(__name__)


class TemplateRepository(BaseRepository):
    """Handles database operations for templates."""

    def __init__(self, db: BaseClient):
        super().__init__(db, "templates")

    async def upsert_layout(self, template_id: str, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates or updates a template's layout using set with merge.
        This ensures an "upsert" behavior.

        - If the document doesn't exist, it's created with created_at.
        - If it exists, it's merged, updating only the specified fields.
        """
        doc_ref = self.collection.document(template_id)
        doc = await asyncio.to_thread(doc_ref.get)

        update_data = {
            "id": template_id,
            "layout": layout_data,
            "updated_at": SERVER_TIMESTAMP,
        }

        if not doc.exists:
            self.logger.info(f"Template '{template_id}' not found. Creating new document.")
            update_data["created_at"] = SERVER_TIMESTAMP

        # Use set with merge=True to create or update
        await asyncio.to_thread(doc_ref.set, update_data, merge=True)
        self.logger.info(f"Upserted layout for template '{template_id}'.")

        # Re-fetch to get the materialized data
        return await self.get_or_raise(template_id)