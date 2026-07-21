# src/api/routers/templates.py
"""
API endpoints for managing template layouts.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.template import TemplateLayoutSchema
from src.core.exceptions import NotFoundException
from src.db.connection import get_db
from src.services.template_layout_service import TemplateLayoutService

router = APIRouter(prefix="/templates", tags=["Templates"])
logger = logging.getLogger(__name__)


@router.get(
    "/{template_id}/layout",
    response_model=TemplateLayoutSchema,
    status_code=status.HTTP_200_OK,
    summary="Get Template Layout",
    description="Retrieves the layout definition for a given template.",
)
async def get_template_layout_endpoint(template_id: str, db: BaseClient = Depends(get_db)):
    """
    Endpoint to fetch the layout of a template.
    Returns 404 if no layout is saved for the given template ID.
    """
    try:
        service = TemplateLayoutService(db)
        layout = await service.get_layout(template_id)
        if layout is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Layout not found for template '{template_id}'.")
        return layout
    except HTTPException as http_exc:
        # Re-raise HTTPException to prevent it from being caught by the generic Exception handler
        raise http_exc
    except Exception as e:
        logger.error(f"Error fetching layout for template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")


@router.put(
    "/{template_id}/layout",
    response_model=TemplateLayoutSchema,
    status_code=status.HTTP_200_OK,
    summary="Save or Replace Template Layout",
    description="Saves or fully replaces the layout definition for a given template.",
)
async def save_template_layout_endpoint(
    template_id: str,
    layout_data: TemplateLayoutSchema,
    db: BaseClient = Depends(get_db),
):
    """
    Endpoint to save a template's layout.
    This is an "upsert" operation: it creates the template document if it
    doesn't exist, or updates it if it does.
    """
    try:
        service = TemplateLayoutService(db)
        updated_template = await service.save_layout(template_id, layout_data)
        if updated_template and "layout" in updated_template:
            return updated_template["layout"]
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save or retrieve layout.")
    except Exception as e:
        logger.error(f"Error saving layout for template {template_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error.")