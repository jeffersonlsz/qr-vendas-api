"""
Firestore database module.
"""

from .connection import get_firestore_client, get_db
from .repositories import (
    BaseRepository,
    ParceiroRepository,
    SolicitacaoRepository,
    OperadorRepository
)
# VendaRepository não está definido nos arquivos de contexto, mas mantendo a estrutura
# from .repositories import VendaRepository

__all__ = [
    "get_firestore_client",
    "get_db",
    "BaseRepository",
    "ParceiroRepository",
    "SolicitacaoRepository",
    "OperadorRepository",
    # "VendaRepository",
]
