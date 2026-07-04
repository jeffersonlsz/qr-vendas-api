"""
Services module - Business logic layer.
"""

from .base import BaseService
from .parceiros import ParceiroService
from .vendas import VendaService
from .dashboard import DashboardService

__all__ = [
    "BaseService",
    "ParceiroService",
    "VendaService",
    "DashboardService",
]
