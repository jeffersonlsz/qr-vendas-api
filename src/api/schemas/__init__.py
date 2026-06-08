"""Pydantic Schemas"""

from .parceiro import (
    ParceiroCreate,
    ParceiroUpdate,
    ParceiroResponse,
    ParceiroResumo,
)
from .lead import (
    LeadCreate,
    LeadUpdate,
    LeadResponse,
    LeadStatus,
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
    "LeadCreate",
    "LeadUpdate",
    "LeadResponse",
    "LeadStatus",
    "VendaCreate",
    "VendaUpdate",
    "VendaResponse",
    "VendaStatus",
    "DashboardResumo",
    "MetricasParceiro",
]
