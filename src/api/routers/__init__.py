"""API Routers"""

from .leads import router as leads_router
from .parceiros import router as parceiros_router
from .vendas import router as vendas_router
from .dashboard import router as dashboard_router

__all__ = [
    "leads_router",
    "parceiros_router",
    "vendas_router",
    "dashboard_router",
]
