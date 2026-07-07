# src\api\routers\parceiros.py
"""
Parceiros (Partners) API Router.
Handles all partner-related endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from src.api.schemas.common import DataResponse, PaginatedResponse
from src.api.schemas.parceiro import (
    ParceiroCreate,
    ParceiroListResponse,
    ParceiroLoteCreateRequest,
    ParceiroLoteCreateResponse,
    ParceiroResponse,
    ParceiroResumo,
    ParceiroUpdate,
    ParceiroAssociacaoUpdate,
)
from src.api.schemas.solicitacao import SolicitacaoListResponse
from src.db.connection import get_db
from src.services.parceiros import ParceiroService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parceiros", tags=["Parceiros"])


def get_parceiro_service(db=Depends(get_db)) -> ParceiroService:
    """Dependency injection for ParceiroService."""
    return ParceiroService(db)


@router.post(
    "/{parceiro_id}/associar",
    response_model=DataResponse[ParceiroResponse],
    summary="Associate card with a partner",
    description="Associates a pre-generated card with a real partner's details.",
)
async def associar_cartao_parceiro(
    parceiro_id: str,
    data: ParceiroAssociacaoUpdate,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Associate a card with a partner.

    This endpoint is used to update the details of a pre-generated partner
    (card) when it's physically delivered to someone. It can only be used
    if the card status is 'DISPONIVEL'.

    - **parceiro_id**: The ID of the partner/card to associate.
    - **nome**: Partner's full name.
    - **telefone**: Partner's phone number.
    - **percentual_comissao**: Commission percentage (optional).
    - **ativo**: Active status (optional).
    """
    parceiro = await service.associar_cartao(parceiro_id, data)
    return DataResponse(
        success=True,
        message="Cartão associado ao parceiro com sucesso.",
        data=parceiro,
    )


@router.get(
    "/{parceiro_id}/solicitacoes",
    response_model=SolicitacaoListResponse,
    summary="Get solicitations by partner",
    description="Get all solicitations for a specific partner.",
)
async def get_solicitacoes_by_parceiro(
    parceiro_id: str,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Get all solicitations for a specific partner.

    - **parceiro_id**: The partner's unique identifier
    """
    solicitacoes = await service.get_solicitacoes_by_parceiro(parceiro_id)
    return SolicitacaoListResponse(solicitacoes=solicitacoes)


@router.post(
    "",
    response_model=DataResponse[ParceiroResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new partner",
    description="Create a new partner (motorista) in the system.",
)
async def create_parceiro(
    data: ParceiroCreate,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Create a new partner.

    - **nome**: Partner's name
    - **telefone**: Partner's phone number
    - **percentual_comissao**: Commission percentage (0-1, default: 0.1)
    - **id**: Optional partner ID (e.g., UBER_123). Auto-generated if not provided.
    """
    parceiro = await service.create(data)
    return DataResponse(
        success=True,
        message="Partner created successfully",
        data=parceiro,
    )


@router.post(
    "/lote",
    response_model=DataResponse[ParceiroLoteCreateResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a batch of new partners",
    description="Create a batch of new partners (cards) in the system.",
)
async def create_parceiros_lote(
    data: ParceiroLoteCreateRequest,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Create a batch of new partners.

    - **quantidade**: Number of partners to create (1-1000)
    - **prefixo_nome**: Prefix for the partner name (default: "Parceiro")
    """
    resultado = await service.create_lote(data)
    return DataResponse(
        success=True,
        message=f"{resultado.quantidade_criada} partners created successfully in batch.",
        data=resultado,
    )


@router.get(
    "",
    response_model=PaginatedResponse[ParceiroListResponse],
    summary="List partners",
    description="List all partners with optional filtering.",
)
async def list_parceiros(
    ativo: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    List partners with filtering options.

    - **ativo**: Filter by active status (true/false)
    - **page**: Page number (starts at 1)
    - **page_size**: Number of items per page (max 100)
    """
    offset = (page - 1) * page_size

    parceiros = await service.list(
        ativo=ativo,
        limit=page_size + 1,
        offset=offset,
    )

    has_more = len(parceiros) > page_size
    if has_more:
        parceiros = parceiros[:page_size]

    total = await service.count(ativo=ativo)

    return PaginatedResponse(
        success=True,
        data=parceiros,
        page=page,
        page_size=page_size,
        total=total,
        has_more=has_more,
    )


@router.get(
    "/{parceiro_id}",
    response_model=DataResponse[ParceiroResponse],
    summary="Get partner by ID",
    description="Get a specific partner by their ID.",
)
async def get_parceiro(
    parceiro_id: str,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Get a partner by ID.

    - **parceiro_id**: The partner's unique identifier (e.g., UBER_123)
    """
    parceiro = await service.get_by_id_or_raise(parceiro_id)
    return DataResponse(
        success=True,
        data=parceiro,
    )


@router.patch(
    "/{parceiro_id}",
    response_model=DataResponse[ParceiroResponse],
    summary="Update partner",
    description="Update a partner's information.",
)
async def update_parceiro(
    parceiro_id: str,
    data: ParceiroUpdate,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Update a partner.

    - **parceiro_id**: The partner's unique identifier
    - **nome**: Partner's name (optional)
    - **telefone**: Partner's phone number (optional)
    - **percentual_comissao**: Commission percentage (optional)
    - **ativo**: Active status (optional)
    """
    parceiro = await service.update(parceiro_id, data)
    return DataResponse(
        success=True,
        message="Partner updated successfully",
        data=parceiro,
    )


@router.delete(
    "/{parceiro_id}",
    response_model=DataResponse,
    summary="Deactivate partner",
    description="Soft delete a partner (sets ativo=false).",
)
async def delete_parceiro(
    parceiro_id: str,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Deactivate a partner (soft delete).

    This sets the partner's active status to false.
    The partner will not be able to generate new solicitations.

    - **parceiro_id**: The partner's unique identifier
    """
    await service.delete(parceiro_id)
    return DataResponse(
        success=True,
        message="Partner deactivated successfully",
    )


@router.get(
    "/{parceiro_id}/resumo",
    response_model=DataResponse[ParceiroResumo],
    summary="Get partner summary",
    description="Get summary metrics for a partner.",
)
async def get_parceiro_resumo(
    parceiro_id: str,
    service: ParceiroService = Depends(get_parceiro_service),
):
    """
    Get partner summary with metrics.

    Returns total solicitations, sales, and commission for the partner.

    - **parceiro_id**: The partner's unique identifier
    """
    resumo = await service.get_resumo(parceiro_id)
    return DataResponse(
        success=True,
        data=resumo,
    )
