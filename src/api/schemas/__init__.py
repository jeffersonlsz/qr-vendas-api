"""Pydantic Schemas"""

from .parceiro import (
    ParceiroCreate,
    ParceiroUpdate,
    ParceiroResponse,
    ParceiroResumo,
)
from .venda import (
    VendaCreate,
    VendaUpdate,
    VendaResponse,
    VendaStatus,
)
from .dashboard import (
    DashboardResumo,
    MetricasParceiro,
)

__all__ = [
    "ParceiroCreate",
    "ParceiroUpdate",
    "ParceiroResponse",
    "ParceiroResumo",
    "VendaCreate",
    "VendaUpdate",
    "VendaResponse",
    "VendaStatus",
    "DashboardResumo",
    "MetricasParceiro",
]
