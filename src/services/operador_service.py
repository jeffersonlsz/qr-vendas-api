"""
Operador (Operator) Service.
Handles business logic for operator operations.
"""
import logging
from typing import Any, Dict, List, Optional

from google.cloud import firestore

from src.api.schemas.operador import OperadorCreateRequest
from src.core.exceptions import NotFoundException, ValidationException
from src.db.repositories import OperadorRepository


class OperadorService:
    """Service for managing operators."""

    def __init__(self, db: firestore.Client):
        self.db = db
        self.repo = OperadorRepository(db)
        self.logger = logging.getLogger(__name__)

    async def create_operador(self, operador_data: OperadorCreateRequest) -> Dict[str, Any]:
        """
        Creates a new operator.

        Args:
            operador_data: The data for the new operator.

        Returns:
            The created operator data.
        """
        self.logger.info("Creating new operator.")
        
        data_to_save = operador_data.model_dump()
        data_to_save["ativo"] = True

        new_operador_id = await self.repo.create(data_to_save, id_prefix="OP")
        
        created_operador = await self.repo.get_or_raise(new_operador_id)
        self.logger.info(f"Successfully created operator with ID: {new_operador_id}")
        return created_operador

    async def list_operadores(self, ativos: bool = True) -> List[Dict[str, Any]]:
        """
        Lists operators, ordered by name.

        Args:
            ativos: If True (default), lists only active operators. 
                    If False, lists all operators.

        Returns:
            A list of operators.
        """
        self.logger.info(f"Listing operators (ativos={ativos}).")
        
        filters = []
        if ativos:
            filters.append(("ativo", "==", True))
        
        # Assuming the repository's list method handles ordering
        return await self.repo.list(filters=filters, order_by="nome")

    async def validate_and_get(self, operador_id: str) -> Dict[str, Any]:
        """
        Validates that an operator exists and is active.

        Args:
            operador_id: The ID of the operator to validate.

        Returns:
            The operator's data if valid.
            
        Raises:
            NotFoundException: If the operator does not exist.
            ValidationException: If the operator is not active.
        """
        operador = await self.repo.get_or_raise(operador_id)

        if not operador.get("ativo", False):
            raise ValidationException(f"Operator {operador_id} is not active")

        return operador
