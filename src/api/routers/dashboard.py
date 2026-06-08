"""
Dashboard API Router.
Handles dashboard and metrics endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query

from src.api.schemas.common import DataResponse
from src.api.schemas.dashboard import (
    DashboardGeral,
    DashboardResumo,
    PeriodoMetricas,
)
from src.db.connection import get_db
from src.services.dashboard import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service(db=Depends(get_db)) -> DashboardService:
    """Dependency injection for DashboardService."""
    return DashboardService(db)


@router.get(
    "/parceiro/{parceiro_id}",
    response_model=DataResponse[DashboardResumo],
    summary="Get partner dashboard",
    description="Get complete dashboard for a specific partner.",
)
async def get_parceiro_dashboard(
    parceiro_id: str,
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Get dashboard for a specific partner.

    Returns comprehensive metrics including:
    - Lead counts by status
    - Sales counts and values
    - Commission totals
    - Recent leads and sales

    - **parceiro_id**: The partner's unique identifier
    """
    dashboard = await service.get_parceiro_dashboard(parceiro_id)
    return DataResponse(
        success=True,
        data=dashboard,
    )


@router.get(
    "/geral",
    response_model=DataResponse[DashboardGeral],
    summary="Get general dashboard",
    description="Get general admin dashboard with aggregated metrics.",
)
async def get_geral_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Get general dashboard for admin view.

    Returns aggregated metrics including:
    - Total partners (active/total)
    - Total leads and conversion rate
    - Total sales and revenue
    - Total commissions
    - Top performing partners
    """
    dashboard = await service.get_geral_dashboard()
    return DataResponse(
        success=True,
        data=dashboard,
    )


@router.get(
    "/periodo",
    response_model=DataResponse[PeriodoMetricas],
    summary="Get metrics for a period",
    description="Get metrics for a specific date range.",
)
async def get_periodo_metricas(
    data_inicio: datetime = Query(
        ...,
        description="Start date (ISO format)",
    ),
    data_fim: datetime = Query(
        ...,
        description="End date (ISO format)",
    ),
    parceiro_id: Optional[str] = Query(
        None,
        description="Filter by partner ID",
    ),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Get metrics for a specific period.

    - **data_inicio**: Start date (ISO format: 2024-01-01T00:00:00)
    - **data_fim**: End date (ISO format: 2024-12-31T23:59:59)
    - **parceiro_id**: Optional partner ID filter
    """
    metricas = await service.get_periodo_metricas(
        data_inicio=data_inicio,
        data_fim=data_fim,
        parceiro_id=parceiro_id,
    )
    return DataResponse(
        success=True,
        data=metricas,
    )


@router.get(
    "/periodo/ultimos-30-dias",
    response_model=DataResponse[PeriodoMetricas],
    summary="Get metrics for last 30 days",
    description="Get metrics for the last 30 days.",
)
async def get_ultimos_30_dias_metricas(
    parceiro_id: Optional[str] = Query(
        None,
        description="Filter by partner ID",
    ),
    service: DashboardService = Depends(get_dashboard_service),
):
    """
    Get metrics for the last 30 days.

    - **parceiro_id**: Optional partner ID filter
    """
    data_fim = datetime.utcnow()
    data_inicio = data_fim - timedelta(days=30)

    metricas = await service.get_periodo_metricas(
        data_inicio=data_inicio,
        data_fim=data_fim,
        parceiro_id=parceiro_id,
    )
    return DataResponse(
        success=True,
        data=metricas,
    )
