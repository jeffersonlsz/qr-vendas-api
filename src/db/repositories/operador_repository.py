# src/db/repositories/operador_repository.py
"""
Repository for handling database operations for Operadores.
"""
from google.cloud.firestore_v1.base_client import BaseClient
from .base_repository import BaseRepository


class OperadorRepository(BaseRepository):
    """
    Manages database interactions for the 'operadores' collection.
    """

    def __init__(self, db: BaseClient):
        """
        Initializes the repository for the 'operadores' collection.
        """
        super().__init__(db, "operadores")
