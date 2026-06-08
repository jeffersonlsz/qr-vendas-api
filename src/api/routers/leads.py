"""
Leads API Router.
Handles all lead-related endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.api.schemas.common import DataResponse, PaginatedResponse
from src.api.schemas.lead import (
    LeadCreate,
    LeadListResponse,
    LeadResponse,
    LeadStatus,
    LeadUpdate,
)
from src.db.connection import get_db
from src.services.leads import LeadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/leads", tags=["Leads"])


def get_lead_service(db=Depends(get_db)) -> LeadService:
    """Dependency injection for LeadService."""
    return LeadService(db)


@router.post(
    "",
    response_model=DataResponse[LeadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead",
    description="Create a new lead associated with a partner.",
)
async def create_lead(
    data: LeadCreate,
    service: LeadService = Depends(get_lead_service),
):
    """
    Create a new lead.

    - **nome**: Lead's name
    - **telefone**: Lead's phone number
    - **parceiro_id**: Partner ID who referred this lead
    - **origem**: Lead origin (default: qr_code)
    - **observacoes**: Optional observations
    """
    lead = await service.create(data)
    return DataResponse(
        success=True,
        message="Lead created successfully",
        data=lead,
    )


@router.get(
    "",
    response_model=PaginatedResponse[LeadListResponse],
    summary="List leads",
    description="List leads with optional filtering and pagination.",
)
async def list_leads(
    parceiro_id: Optional[str] = Query(None, description="Filter by partner ID"),
    status: Optional[LeadStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: LeadService = Depends(get_lead_service),
):
    """
    List leads with filtering options.

    - **parceiro_id**: Filter by partner ID
    - **status**: Filter by lead status
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    """
    offset = (page - 1) * page_size

    leads = await service.list(
        parceiro_id=parceiro_id,
        status=status,
        limit=page_size + 1,  # Get one extra to check if there's more
        offset=offset,
    )

    has_more = len(leads) > page_size
    if has_more:
        leads = leads[:page_size]

    total = await service.count(parceiro_id=parceiro_id, status=status)

    return PaginatedResponse(
        success=True,
        data=leads,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/{lead_id}",
    response_model=DataResponse[LeadResponse],
    summary="Get lead by ID",
    description="Get a specific lead by its ID.",
)
async def get_lead(
    lead_id: str,
    service: LeadService = Depends(get_lead_service),
):
    """
    Get a lead by ID.

    - **lead_id**: The lead's unique identifier
    """
    lead = await service.get_by_id_or_raise(lead_id)
    return DataResponse(
        success=True,
        data=lead,
    )


@router.patch(
    "/{lead_id}",
    response_model=DataResponse[LeadResponse],
    summary="Update lead",
    description="Update a lead's information.",
)
async def update_lead(
    lead_id: str,
    data: LeadUpdate,
    service: LeadService = Depends(get_lead_service),
):
    """
    Update a lead.

    - **lead_id**: The lead's unique identifier
    - **nome**: Lead's name (optional)
    - **telefone**: Lead's phone number (optional)
    - **status**: Lead status (optional)
    - **observacoes**: Observations (optional)
    """
    lead = await service.update(lead_id, data)
    return DataResponse(
        success=True,
        message="Lead updated successfully",
        data=lead,
    )


@router.delete(
    "/{lead_id}",
    response_model=DataResponse,
    summary="Delete lead",
    description="Delete a lead.",
)
async def delete_lead(
    lead_id: str,
    service: LeadService = Depends(get_lead_service),
):
    """
    Delete a lead.

    - **lead_id**: The lead's unique identifier
    """
    await service.delete(lead_id)
    return DataResponse(
        success=True,
        message="Lead deleted successfully",
    )


@router.get(
    "/parceiro/{parceiro_id}",
    response_model=PaginatedResponse[LeadListResponse],
    summary="Get leads by partner",
    description="Get all leads for a specific partner.",
)
async def get_leads_by_parceiro(
    parceiro_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: LeadService = Depends(get_lead_service),
):
    """
    Get all leads for a partner.

    - **parceiro_id**: The partner's unique identifier
    """
    offset = (page - 1) * page_size

    leads = await service.list(
        parceiro_id=parceiro_id,
        limit=page_size + 1,
        offset=offset,
    )

    has_more = len(leads) > page_size
    if has_more:
        leads = leads[:page_size]

    total = await service.count(parceiro_id=parceiro_id)

    return PaginatedResponse(
        success=True,
        data=leads,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )
