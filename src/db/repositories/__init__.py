# src/db/repositories/__init__.py
"""
This package contains all the Firestore repository classes.
"""

from .base_repository import BaseRepository
from .parceiro_repository import ParceiroRepository
from .solicitacao_repository import SolicitacaoRepository
from .operador_repository import OperadorRepository

__all__ = [
    "BaseRepository",
    "ParceiroRepository",
    "SolicitacaoRepository",
    "OperadorRepository",
]
