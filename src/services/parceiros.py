"""
Parceiro (Partner) Service.
Handles business logic for partner operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

from src.api.schemas.parceiro import (
    ParceiroAssociacaoUpdate,
    ParceiroCreate,
    ParceiroLoteCreateRequest,
    ParceiroLoteCreateResponse,
    ParceiroResponse,
    ParceiroResumo,
    ParceiroUpdate,
)
from src.api.schemas.solicitacao import SolicitacaoOut
from src.core.config import get_settings
from src.core.exceptions import ConflictException, NotFoundException, ValidationException
from src.db.connection import get_server_timestamp
from src.db.repositories import SolicitacaoRepository
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class ParceiroService(BaseService):
    """
    Service for partner operations.
    Encapsulates business logic for partners.
    """

    COLLECTION_NAME = "parceiros"

    def __init__(self, db: firestore.Client):
        """
        Initialize service.

        Args:
            db: Firestore client
        """
        super().__init__(db, self.COLLECTION_NAME)
        self.solicitacao_repo = SolicitacaoRepository(db)

    async def get_solicitacoes_by_parceiro(self, parceiro_id: str) -> List[SolicitacaoOut]:
        """
        Get all solicitations for a specific partner.

        Args:
            parceiro_id: The ID of the partner.

        Returns:
            A list of solicitations for the partner.
        """
        await self.get_by_id_or_raise(parceiro_id)
        solicitacoes_data = await self.solicitacao_repo.find_by_parceiro_id(parceiro_id)
        return [SolicitacaoOut(**data) for data in solicitacoes_data]

    def _generate_codigo_cartao(self, numero_sequencial: int) -> str:
        """Generates a formatted card code based on the sequential number."""
        settings = get_settings()
        return f"{settings.codigo_cartao_prefix}-{numero_sequencial:06d}"

    async def create(self, data: ParceiroCreate) -> ParceiroResponse:
        """
        Create a new partner.

        Args:
            data: Partner creation data

        Returns:
            Created partner data
        """
        if data.id:
            existing = await self.get_by_id(data.id)
            if existing:
                raise ConflictException(f"Partner with ID {data.id} already exists")

        partner_id = data.id or self._generate_id("UBER")

        # Ensure numero_sequencial is always present
        if data.numero_sequencial is None:
            numero_sequencial = await self._get_proximo_numero_sequencial()
        else:
            numero_sequencial = data.numero_sequencial

        codigo_cartao = self._generate_codigo_cartao(numero_sequencial)

        partner_data = {
            "id": partner_id,
            "nome": data.nome,
            "telefone": data.telefone,
            "percentual_comissao": data.percentual_comissao,
            "status_cartao": data.status_cartao,
            "numero_sequencial": numero_sequencial,
            "codigo_cartao": codigo_cartao,
            "data_entrega_cartao": None,
            "entregue_por": None,
            "ativo": True,
            "created_at": get_server_timestamp(),
            "updated_at": get_server_timestamp(),
        }

        doc_ref = self.collection.document(partner_id)
        doc_ref.set(partner_data)

        created_doc = await self._fetch_document(partner_id)
        if not created_doc.exists:
            raise Exception(f"Failed to create partner: {partner_id}")

        logger.info(f"Created partner: {partner_id} with code {codigo_cartao}")
        return ParceiroResponse(**self._serialize_doc(created_doc))

    async def _get_proximo_numero_sequencial(self) -> int:
        """
        Find the highest sequential number in the collection and return the next one.
        """
        query = self.collection.order_by(
            "numero_sequencial", direction=firestore.Query.DESCENDING
        ).limit(1)
        docs = query.stream()

        try:
            latest_partner = next(docs)
            last_number = latest_partner.to_dict().get("numero_sequencial", 0)
            # Ensure we handle cases where numero_sequencial might be None
            return (last_number or 0) + 1
        except StopIteration:
            # No partners exist, start from 1
            return 1

    async def create_lote(
        self, data: ParceiroLoteCreateRequest
    ) -> ParceiroLoteCreateResponse:
        """
        Create a batch of new partners.
        """
        start_num = await self._get_proximo_numero_sequencial()
        end_num = start_num + data.quantidade
        created_count = 0

        logger.info(
            f"Starting batch creation of {data.quantidade} partners "
            f"with prefix '{data.prefixo_nome}' from number {start_num}."
        )

        current_batch = self.db.batch()
        batch_count = 0
        BATCH_LIMIT = 500  # Firestore batch limit

        for i in range(start_num, end_num):
            partner_id = self._generate_id("UBER")
            nome = f"{data.prefixo_nome} {i:04d}"
            codigo_cartao = self._generate_codigo_cartao(i)

            partner_data = {
                "id": partner_id,
                "nome": nome,
                "telefone": "",  # As per requirement
                "percentual_comissao": 0.1,  # Default value
                "status_cartao": "DISPONIVEL",
                "numero_sequencial": i,
                "codigo_cartao": codigo_cartao,
                "data_entrega_cartao": None,
                "entregue_por": None,
                "ativo": True,
                "created_at": get_server_timestamp(),
                "updated_at": get_server_timestamp(),
            }

            doc_ref = self.collection.document(partner_id)
            current_batch.set(doc_ref, partner_data)
            batch_count += 1
            created_count += 1

            # Commit batch if it reaches the limit
            if batch_count == BATCH_LIMIT:
                logger.info(f"Committing a batch of {batch_count} partners.")
                await asyncio.to_thread(current_batch.commit)
                # Start a new batch
                current_batch = self.db.batch()
                batch_count = 0

        # Commit any remaining items in the last batch
        if batch_count > 0:
            logger.info(f"Committing the final batch of {batch_count} partners.")
            await asyncio.to_thread(current_batch.commit)

        logger.info(f"Successfully created {created_count} partners.")

        return ParceiroLoteCreateResponse(
            quantidade_solicitada=data.quantidade,
            quantidade_criada=created_count,
            primeiro_nome=f"{data.prefixo_nome} {start_num:04d}",
            ultimo_nome=f"{data.prefixo_nome} {end_num - 1:04d}",
        )

    async def get_by_id(self, partner_id: str) -> Optional[Dict[str, Any]]:
        """
        Get partner by ID.

        Args:
            partner_id: Partner ID

        Returns:
            Partner data or None
        """
        doc = await self._fetch_document(partner_id)
        if doc.exists:
            return self._serialize_doc(doc)
        return None

    async def get_by_id_or_raise(self, partner_id: str) -> Dict[str, Any]:
        """
        Get partner by ID or raise exception.

        Args:
            partner_id: Partner ID

        Returns:
            Partner data

        Raises:
            NotFoundException: If partner doesn't exist
        """
        doc = await self._fetch_document(partner_id)
        return self._get_doc_or_raise(doc, partner_id)

    async def update(
        self, partner_id: str, data: ParceiroUpdate
    ) -> Dict[str, Any]:
        """
        Update a partner.

        Args:
            partner_id: Partner ID
            data: Update data

        Returns:
            Updated partner data
        """
        # Verify partner exists
        await self.get_by_id_or_raise(partner_id)

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = get_server_timestamp()
            doc_ref = self.collection.document(partner_id)
            doc_ref.update(update_data)

        # Re-fetch to get updated data with materialized timestamps
        updated_doc = await self._fetch_document(partner_id)
        logger.info(f"Updated partner: {partner_id}")
        return self._serialize_doc(updated_doc)

    async def delete(self, partner_id: str) -> bool:
        """
        Delete a partner (soft delete by setting ativo=False).

        Args:
            partner_id: Partner ID

        Returns:
            True if deleted
        """
        # Verify partner exists
        await self.get_by_id_or_raise(partner_id)

        doc_ref = self.collection.document(partner_id)
        doc_ref.update(
            {
                "ativo": False,
                "updated_at": get_server_timestamp(),
            }
        )

        logger.info(f"Deactivated partner: {partner_id}")
        return True

    async def hard_delete(self, partner_id: str) -> bool:
        """
        Permanently delete a partner.
        Use with caution - should only be used if partner has no associated solicitations/sales.

        Args:
            partner_id: Partner ID

        Returns:
            True if deleted
        """
        await self.get_by_id_or_raise(partner_id)

        doc_ref = self.collection.document(partner_id)
        doc_ref.delete()

        logger.warning(f"Hard deleted partner: {partner_id}")
        return True

    async def list(
        self,
        ativo: Optional[bool] = None,
        order_by: str = "created_at",
        descending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List partners with optional filtering.

        Args:
            ativo: Filter by active status
            order_by: Field to order by
            descending: Order direction
            limit: Maximum results
            offset: Results offset

        Returns:
            List of partners
        """
        query = self.collection

        if ativo is not None:
            query = query.where("ativo", "==", ativo)

        query = query.order_by(
            order_by,
            direction=firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
        )

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        docs = query.stream()
        return [self._serialize_doc(doc) for doc in docs]

    async def count(self, ativo: Optional[bool] = None) -> int:
        """
        Count partners.

        Args:
            ativo: Filter by active status

        Returns:
            Count of partners
        """
        query = self.collection
        if ativo is not None:
            query = query.where("ativo", "==", ativo)

        docs = query.stream()
        return len(list(docs))

    async def get_resumo(self, partner_id: str) -> ParceiroResumo:
        """
        Get partner summary with corrected metrics.

        Args:
            partner_id: Partner ID

        Returns:
            Partner summary with corrected metrics.
        """
        partner = await self.get_by_id_or_raise(partner_id)

        # Import here to avoid circular imports
        from src.db.repositories import SolicitacaoRepository
        from src.services.vendas import VendaService
        from src.api.schemas.venda import VendaStatus

        solicitacao_repo = SolicitacaoRepository(self.db)
        venda_service = VendaService(self.db)

        # Count all solicitations from this partner.
        total_solicitacoes = await solicitacao_repo.count(
            filters=[("parceiro_id", "==", partner_id)]
        )

        # Count valid sales (not canceled).
        total_vendas = await venda_service.count(
            parceiro_id=partner_id,
            status__not_in=[VendaStatus.CANCELADO]
        )

        # Calculate financial metrics based only on paid sales.
        vendas_pagas = await venda_service.list(
            parceiro_id=partner_id,
            status=VendaStatus.PAGO
        )
        
        total_comissao = sum(v.get("comissao", 0) for v in vendas_pagas)
        valor_total_vendas = sum(v.get("valor_venda", 0) for v in vendas_pagas)

        return ParceiroResumo(
            parceiro_id=partner_id,
            nome=partner["nome"],
            total_solicitacoes=total_solicitacoes,
            total_vendas=total_vendas,
            total_comissao=total_comissao,
            valor_total_vendas=valor_total_vendas,
        )

    async def validate_and_get(self, partner_id: str) -> Dict[str, Any]:
        """
        Validate partner exists and is active.

        Args:
            partner_id: Partner ID to validate

        Returns:
            Partner data

        Raises:
            NotFoundException: If partner doesn't exist
            ValidationException: If partner is inactive
        """
        partner = await self.get_by_id_or_raise(partner_id)

        if not partner.get("ativo", False):
            raise ValidationException(f"Partner {partner_id} is not active")

        return partner

    async def associar_cartao(self, parceiro_id: str, data: ParceiroAssociacaoUpdate) -> Dict[str, Any]:
        """
        Associates a card with a partner's details.

        This is used when a pre-generated card is physically given to a partner.

        Args:
            parceiro_id: The ID of the partner (card) to associate.
            data: The partner's details to update.

        Returns:
            The updated partner data.

        Raises:
            ConflictException: If the card is not in 'DISPONIVEL' status.
        """
        partner = await self.get_by_id_or_raise(parceiro_id)

        if partner.get("status_cartao") != "DISPONIVEL":
            raise ConflictException("Este cartão já foi associado a um parceiro.")

        update_data = data.model_dump()
        update_data["status_cartao"] = "EM_USO"
        update_data["data_entrega_cartao"] = get_server_timestamp()
        update_data["updated_at"] = get_server_timestamp()

        doc_ref = self.collection.document(parceiro_id)
        await asyncio.to_thread(doc_ref.update, update_data)

        updated_doc = await self._fetch_document(parceiro_id)
        logger.info(f"Associated card for partner: {parceiro_id}")
        return self._serialize_doc(updated_doc)

