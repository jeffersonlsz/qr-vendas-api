# src/api/routers/solicitacoes.py
"""
API endpoint for creating new Solicitações de Cotação.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from google.cloud.firestore_v1.base_client import BaseClient

from src.api.schemas.solicitacao import (
    DadosComerciaisSchema,
    HistoricoStatusSchema,
    SolicitacaoCreate,
    SolicitacaoListResponse,
    SolicitacaoOut,
    SolicitacaoResponse,
    StatusUpdateSchema,
)
from src.core.exceptions import ConflictException, NotFoundException
from src.db.connection import get_db
from src.db.repositories import SolicitacaoRepository
from src.services.solicitacao_service import SolicitacaoService
from src.services.solicitacao_workflow_service import SolicitacaoWorkflowService

router = APIRouter(prefix="/solicitacoes", tags=["Solicitações"])
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=SolicitacaoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lista todas as Solicitações de Cotação",
    description="Recupera uma lista de todas as solicitações de cotação existentes.",
)
async def get_all_solicitacoes_endpoint(db: BaseClient = Depends(get_db)):
    """
    Endpoint to retrieve all quotation requests (Solicitações de Cotação).
    """
    try:
        service = SolicitacaoService(db)
        solicitacoes_list = await service.get_all_solicitacoes()
        return {"solicitacoes": solicitacoes_list}
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching solicitations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the request.",
        )


@router.post(
    "",
    response_model=SolicitacaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova Solicitação de Cotação",
    description="Registra uma nova solicitação de cotação e gera um protocolo único.",
)
async def create_solicitacao_endpoint(
    solicitacao_data: SolicitacaoCreate,
    db: BaseClient = Depends(get_db),
):
    """
    Endpoint to create a new quotation request (Solicitação de Cotação).

    - **parceiro_id**: ID of the partner associated with the request.
    - **vidas**: List of lives to be quoted, each with an age.
    - **cobertura**: Desired coverage type ('nacional' or 'regional').
    - Optional fields: 'cidade', 'uf', 'cpf', 'cnpj', 'operadoras_preferidas'.

    Returns the unique protocol for the created solicitation.
    """
    try:
        service = SolicitacaoService(db)
        protocolo = await service.create_solicitacao(solicitacao_data)
        return SolicitacaoResponse(protocolo=protocolo)
    except NotFoundException as e:
        logger.warning(f"Failed to create solicitation: {e.detail}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail,
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred while creating solicitation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the request.",
        )


@router.patch(
    "/{solicitacao_id}/status",
    response_model=SolicitacaoOut,
    status_code=status.HTTP_200_OK,
    summary="Altera o status de uma Solicitação",
    description="Altera o status de uma solicitação, validando a transição de workflow e registrando o histórico.",
)
async def alterar_status_endpoint(
    solicitacao_id: str,
    status_update: StatusUpdateSchema,
    db: BaseClient = Depends(get_db),
):
    """
    Endpoint to change the status of a quotation request.
    The user performing the action can be identified via authentication later.
    """
    try:
        workflow_service = SolicitacaoWorkflowService(db)
        # TODO: Get user from auth dependency
        await workflow_service.alterar_status(solicitacao_id, status_update.status, usuario="api_user")

        repo = SolicitacaoRepository(db)
        updated_solicitacao = await repo.get_or_raise(solicitacao_id)
        return updated_solicitacao
    except (NotFoundException, ConflictException) as e:
        logger.warning(f"Failed to change status for solicitation {solicitacao_id}: {e.detail or e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.detail or e.message)
    except Exception as e:
        logger.error(f"An unexpected error occurred while changing status for {solicitacao_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred.",
        )


@router.patch(
    "/{solicitacao_id}/dados-comerciais",
    response_model=SolicitacaoOut,
    status_code=status.HTTP_200_OK,
    summary="Atualiza os Dados Comerciais de uma Solicitação",
    description="Atualiza um ou mais campos dos dados comerciais de uma solicitação.",
)
async def update_dados_comerciais_endpoint(
    solicitacao_id: str,
    dados_update: DadosComerciaisSchema,
    db: BaseClient = Depends(get_db),
):
    """
    Endpoint to partially update the commercial data of a quotation request.
    """
    try:
        service = SolicitacaoService(db)
        updated_solicitacao = await service.update_dados_comerciais(solicitacao_id, dados_update)
        return updated_solicitacao
    except NotFoundException as e:
        logger.warning(f"Failed to update commercial data for solicitation {solicitacao_id}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating commercial data for {solicitacao_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred.",
        )


@router.get(
    "/{solicitacao_id}/historico",
    response_model=List[HistoricoStatusSchema],
    status_code=status.HTTP_200_OK,
    summary="Consulta o Histórico de Status de uma Solicitação",
    description="Retorna a lista de todas as alterações de status para uma dada solicitação.",
)
async def get_historico_endpoint(
    solicitacao_id: str,
    db: BaseClient = Depends(get_db),
):
    """
    Endpoint to retrieve the status change history for a quotation request.
    """
    try:
        service = SolicitacaoService(db)
        historico = await service.get_solicitacao_historico(solicitacao_id)
        return historico
    except NotFoundException as e:
        logger.warning(f"Failed to get history for solicitation {solicitacao_id}: {e.detail}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting history for {solicitacao_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred.",
        )
