"""
Firestore database module.
"""

from .connection import get_firestore_client, get_db
from .repositories import (
    BaseRepository,
    ParceiroRepository,
    VendaRepository,
)

__all__ = [
    "get_firestore_client",
    "get_db",
    "BaseRepository",
    "ParceiroRepository",
    "VendaRepository",
]
