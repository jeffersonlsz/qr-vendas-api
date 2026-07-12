"""API Routers"""

from .parceiros import router as parceiros_router
from .vendas import router as vendas_router
from .dashboard import router as dashboard_router
from .solicitacoes import router as solicitacoes_router
from .operadores import router as operadores_router

__all__ = [
    "parceiros_router",
    "vendas_router",
    "dashboard_router",
    "solicitacoes_router",
    "operadores_router",
]
