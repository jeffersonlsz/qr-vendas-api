# src/services/template_layout_service.py
"""
Business logic for managing template layouts.
"""
import logging
from typing import Dict, Any, Optional
from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.template import TemplateLayoutSchema
from src.core.exceptions import NotFoundException
from src.db.repositories.template_repository import TemplateRepository

logger = logging.getLogger(__name__)


class TemplateLayoutService:
    """Service for handling template layout operations."""

    def __init__(self, db: BaseClient):
        self.db = db
        self.template_repo = TemplateRepository(db)

    async def get_layout(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the layout for a specific template.
        Returns None if the template or its layout does not exist.
        """
        logger.info(f"Fetching layout for template ID: {template_id}")
        try:
            template_doc = await self.template_repo.get_or_raise(template_id)
            layout = template_doc.get("layout")
            if not layout:
                logger.warning(f"Template '{template_id}' exists but has no layout field.")
                return None
            return layout
        except NotFoundException:
            logger.info(f"Template '{template_id}' not found. No layout to return.")
            return None

    async def save_layout(
        self,
        template_id: str,
        layout_data: TemplateLayoutSchema
    ) -> Dict[str, Any]:
        """
        Saves or replaces the layout for a specific template (upsert).
        """
        logger.info(f"Saving layout for template ID: {template_id}")
        layout_dict = layout_data.model_dump()
        updated_template = await self.template_repo.upsert_layout(template_id, layout_dict)
        return updated_template