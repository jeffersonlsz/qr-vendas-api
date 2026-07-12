"""
Operadores (Operators) API Router.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, Query, status
from google.cloud import firestore

from src.api.schemas.common import DataResponse
from src.api.schemas.operador import (
    OperadorCreateRequest,
    OperadorInfo,
    OperadorResponse,
)
from src.db.connection import get_db
from src.services.operador_service import OperadorService

router = APIRouter(prefix="/operadores", tags=["Operadores"])
logger = logging.getLogger(__name__)


def get_operador_service(db: firestore.Client = Depends(get_db)) -> OperadorService:
    """Dependency injection for OperadorService."""
    return OperadorService(db)


@router.post(
    "",
    response_model=DataResponse[OperadorResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new operator",
)
async def create_operador(
    operador_data: OperadorCreateRequest,
    service: OperadorService = Depends(get_operador_service),
):
    """
    Creates a new operator in the system.
    """
    new_operador = await service.create_operador(operador_data)
    return DataResponse(success=True, data=new_operador, message="Operador criado com sucesso.")


@router.get(
    "",
    response_model=DataResponse[List[OperadorInfo]],
    summary="List operators",
    description="Returns a list of operators, ordered alphabetically by name.",
)
async def list_operadores(
    ativos: bool = Query(
        True,
        description="By default, returns only active operators. If false, returns all operators.",
    ),
    service: OperadorService = Depends(get_operador_service),
):
    """
    Retrieves a list of operators.

    - By default, only **active** operators are returned, sorted by name.
    - Use `?ativos=false` to include inactive operators in the list.
    """
    operadores = await service.list_operadores(ativos=ativos)
    return DataResponse(success=True, data=operadores)
