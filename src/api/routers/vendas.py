"""
Vendas (Sales) API Router.
Handles all sale-related endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.api.schemas.common import DataResponse, PaginatedResponse
from src.api.schemas.venda import (
    VendaCreate,
    VendaResponse,
    VendaStatus,
    VendaUpdate,
    VendaListResponse,
)
from src.db.connection import get_db
from src.services.vendas import VendaService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendas", tags=["Vendas"])


def get_venda_service(db=Depends(get_db)) -> VendaService:
    """Dependency injection for VendaService."""
    return VendaService(db)


@router.post(
    "",
    response_model=DataResponse[VendaResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sale",
    description="Create a new sale from a converted lead.",
)
async def create_venda(
    data: VendaCreate,
    service: VendaService = Depends(get_venda_service),
):
    """
    Create a new sale.

    - **lead_id**: Lead ID associated with this sale
    - **valor_venda**: Sale value
    - **descricao**: Optional sale description
    - **status**: Sale status (default: pendente)

    The commission is automatically calculated based on the partner's commission rate.
    The lead status is automatically updated to 'convertido'.
    """
    venda = await service.create(data)
    return DataResponse(
        success=True,
        message="Sale created successfully",
        data=venda,
    )


@router.get(
    "",
    response_model=PaginatedResponse[VendaListResponse],
    summary="List sales",
    description="List sales with optional filtering and pagination.",
)
async def list_vendas(
    parceiro_id: Optional[str] = Query(None, description="Filter by partner ID"),
    lead_id: Optional[str] = Query(None, description="Filter by lead ID"),
    status: Optional[VendaStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: VendaService = Depends(get_venda_service),
):
    """
    List sales with filtering options.

    - **parceiro_id**: Filter by partner ID
    - **lead_id**: Filter by lead ID
    - **status**: Filter by sale status
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    """
    offset = (page - 1) * page_size

    vendas = await service.list(
        parceiro_id=parceiro_id,
        lead_id=lead_id,
        status=status,
        limit=page_size + 1,
        offset=offset,
    )

    has_more = len(vendas) > page_size
    if has_more:
        vendas = vendas[:page_size]

    total = await service.count(parceiro_id=parceiro_id, status=status)

    return PaginatedResponse(
        success=True,
        data=vendas,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/{venda_id}",
    response_model=DataResponse[VendaResponse],
    summary="Get sale by ID",
    description="Get a specific sale by its ID.",
)
async def get_venda(
    venda_id: str,
    service: VendaService = Depends(get_venda_service),
):
    """
    Get a sale by ID.

    - **venda_id**: The sale's unique identifier
    """
    venda = await service.get_by_id_or_raise(venda_id)
    return DataResponse(
        success=True,
        data=venda,
    )


@router.patch(
    "/{venda_id}",
    response_model=DataResponse[VendaResponse],
    summary="Update sale",
    description="Update a sale's information.",
)
async def update_venda(
    venda_id: str,
    data: VendaUpdate,
    service: VendaService = Depends(get_venda_service),
):
    """
    Update a sale.

    - **venda_id**: The sale's unique identifier
    - **valor_venda**: Sale value (optional)
    - **descricao**: Sale description (optional)
    - **status**: Sale status (optional)

    If status is changed to 'pago', the pago_em timestamp is automatically set.
    If valor_venda is changed, the commission is recalculated.
    """
    venda = await service.update(venda_id, data)
    return DataResponse(
        success=True,
        message="Sale updated successfully",
        data=venda,
    )


@router.delete(
    "/{venda_id}",
    response_model=DataResponse,
    summary="Delete sale",
    description="Delete a sale.",
)
async def delete_venda(
    venda_id: str,
    service: VendaService = Depends(get_venda_service),
):
    """
    Delete a sale.

    - **venda_id**: The sale's unique identifier
    """
    await service.delete(venda_id)
    return DataResponse(
        success=True,
        message="Sale deleted successfully",
    )


@router.post(
    "/{venda_id}/pagar",
    response_model=DataResponse[VendaResponse],
    summary="Mark sale as paid",
    description="Mark a sale as paid and set the payment timestamp.",
)
async def mark_venda_as_paid(
    venda_id: str,
    service: VendaService = Depends(get_venda_service),
):
    """
    Mark a sale as paid.

    This sets the status to 'pago' and records the payment timestamp.

    - **venda_id**: The sale's unique identifier
    """
    venda = await service.mark_as_paid(venda_id)
    return DataResponse(
        success=True,
        message="Sale marked as paid",
        data=venda,
    )


@router.get(
    "/parceiro/{parceiro_id}",
    response_model=PaginatedResponse[VendaListResponse],
    summary="Get sales by partner",
    description="Get all sales for a specific partner.",
)
async def get_vendas_by_parceiro(
    parceiro_id: str,
    status: Optional[VendaStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: VendaService = Depends(get_venda_service),
):
    """
    Get all sales for a partner.

    - **parceiro_id**: The partner's unique identifier
    - **status**: Optional status filter
    """
    offset = (page - 1) * page_size

    vendas = await service.list(
        parceiro_id=parceiro_id,
        status=status,
        limit=page_size + 1,
        offset=offset,
    )

    has_more = len(vendas) > page_size
    if has_more:
        vendas = vendas[:page_size]

    total = await service.count(parceiro_id=parceiro_id, status=status)

    return PaginatedResponse(
        success=True,
        data=vendas,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/lead/{lead_id}",
    response_model=PaginatedResponse[VendaListResponse],
    summary="Get sales by lead",
    description="Get all sales for a specific lead.",
)
async def get_vendas_by_lead(
    lead_id: str,
    service: VendaService = Depends(get_venda_service),
):
    """
    Get all sales for a lead.

    - **lead_id**: The lead's unique identifier
    """
    vendas = await service.get_by_lead(lead_id)

    return PaginatedResponse(
        success=True,
        data=vendas,
        page=1,
        page_size=len(vendas),
        total=len(vendas),
        has_more=False,
    )
