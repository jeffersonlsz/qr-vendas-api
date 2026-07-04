"""
Venda (Sale) Service.
Handles business logic for sale operations.
"""

import logging
from typing import Any, Dict, List, Optional
from src.api.schemas.solicitacao import StatusSolicitacao
from google.cloud import firestore

from src.api.schemas.venda import VendaCreate, VendaStatus, VendaUpdate
from src.core.exceptions import NotFoundException, ValidationException
from src.db.connection import get_server_timestamp
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class VendaService(BaseService):
    """
    Service for sale operations.
    Encapsulates business logic for sales and commission calculations.
    """

    COLLECTION_NAME = "vendas"

    def __init__(self, db: firestore.Client):
        """
        Initialize service.

        Args:
            db: Firestore client
        """
        super().__init__(db, self.COLLECTION_NAME)

    async def create(self, data: VendaCreate) -> Dict[str, Any]:
        """
        Create a new sale.

        Args:
            data: Sale creation data

        Returns:
            Created sale data
        """
        # Validate solicitation exists and get partner info
        solicitacao = await self._validate_solicitacao(data.solicitacao_id)
        parceiro = await self._get_parceiro(solicitacao["parceiro_id"])

        # Calculate commission
        percentual_comissao = parceiro.get("percentual_comissao", 0.1)
        comissao = data.valor_venda * percentual_comissao

        venda_id = self._generate_id("venda")

        venda_data = {
            "id": venda_id,
            "solicitacao_id": data.solicitacao_id,
            "parceiro_id": solicitacao["parceiro_id"],
            "valor_venda": data.valor_venda,
            "percentual_comissao": percentual_comissao,
            "comissao": comissao,
            "status": data.status.value if hasattr(data.status, "value") else data.status,
            "descricao": data.descricao,
            "created_at": get_server_timestamp(),
            "updated_at": get_server_timestamp(),
            "pago_em": None,
        }

        doc_ref = self.collection.document(venda_id)
        doc_ref.set(venda_data)

        # Re-fetch document to get materialized timestamps from Firestore
        doc = await self._fetch_document(venda_id)
        if not doc.exists:
            raise Exception(f"Failed to create sale: {venda_id}")

        # Update solicitation status to converted
        await self._update_solicitacao_status(data.solicitacao_id, StatusSolicitacao.CONVERTIDA)

        logger.info(f"Created sale: {venda_id} for solicitation: {data.solicitacao_id}")
        return self._serialize_doc(doc)

    async def get_by_id(self, venda_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sale by ID.

        Args:
            venda_id: Sale ID

        Returns:
            Sale data or None
        """
        doc = await self._fetch_document(venda_id)
        if doc.exists:
            return self._serialize_doc(doc)
        return None

    async def get_by_id_or_raise(self, venda_id: str) -> Dict[str, Any]:
        """
        Get sale by ID or raise exception.

        Args:
            venda_id: Sale ID

        Returns:
            Sale data

        Raises:
            NotFoundException: If sale doesn't exist
        """
        doc = await self._fetch_document(venda_id)
        return self._get_doc_or_raise(doc, venda_id)

    async def update(self, venda_id: str, data: VendaUpdate) -> Dict[str, Any]:
        """
        Update a sale.

        Args:
            venda_id: Sale ID
            data: Update data

        Returns:
            Updated sale data
        """
        existing = await self.get_by_id_or_raise(venda_id)

        update_data = data.model_dump(exclude_unset=True)

        # Recalculate commission if value changed
        if "valor_venda" in update_data:
            percentual_comissao = existing.get("percentual_comissao", 0.1)
            update_data["comissao"] = update_data["valor_venda"] * percentual_comissao

        # Set pago_em timestamp if status changed to PAGO
        if update_data.get("status") == VendaStatus.PAGO.value:
            if existing.get("status") != VendaStatus.PAGO.value:
                update_data["pago_em"] = get_server_timestamp()
        elif "status" in update_data:
            # Clear pago_em if status changed from PAGO
            if existing.get("status") == VendaStatus.PAGO.value:
                update_data["pago_em"] = None

        if update_data:
            update_data["updated_at"] = get_server_timestamp()
            doc_ref = self.collection.document(venda_id)
            doc_ref.update(update_data)

        # Re-fetch to get updated data with materialized timestamps
        updated_doc = await self._fetch_document(venda_id)
        logger.info(f"Updated sale: {venda_id}")
        return self._serialize_doc(updated_doc)

    async def delete(self, venda_id: str) -> bool:
        """
        Delete a sale.

        Args:
            venda_id: Sale ID

        Returns:
            True if deleted
        """
        await self.get_by_id_or_raise(venda_id)

        doc_ref = self.collection.document(venda_id)
        doc_ref.delete()

        logger.info(f"Deleted sale: {venda_id}")
        return True

    async def list(
        self,
        parceiro_id: Optional[str] = None,
        solicitacao_id: Optional[str] = None,
        status: Optional[VendaStatus] = None,
        order_by: str = "created_at",
        descending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List sales with optional filtering.

        Args:
            parceiro_id: Filter by partner ID
            solicitacao_id: Filter by solicitation ID
            status: Filter by status
            order_by: Field to order by
            descending: Order direction
            limit: Maximum results
            offset: Results offset

        Returns:
            List of sales
        """
        query = self.collection

        if parceiro_id:
            query = query.where("parceiro_id", "==", parceiro_id)

        if solicitacao_id:
            query = query.where("solicitacao_id", "==", solicitacao_id)

        if status:
            status_value = status.value if hasattr(status, "value") else status
            query = query.where("status", "==", status_value)

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

    async def count(
        self,
        parceiro_id: Optional[str] = None,
        status: Optional[VendaStatus] = None,
    ) -> int:
        """
        Count sales.

        Args:
            parceiro_id: Filter by partner ID
            status: Filter by status

        Returns:
            Count of sales
        """
        query = self.collection

        if parceiro_id:
            query = query.where("parceiro_id", "==", parceiro_id)

        if status:
            status_value = status.value if hasattr(status, "value") else status
            query = query.where("status", "==", status_value)

        docs = query.stream()
        return len(list(docs))

    async def get_by_parceiro(
        self,
        parceiro_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get all sales for a partner.

        Args:
            parceiro_id: Partner ID
            limit: Maximum results

        Returns:
            List of sales
        """
        return await self.list(parceiro_id=parceiro_id, limit=limit)

    async def get_by_solicitacao(self, solicitacao_id: str) -> List[Dict[str, Any]]:
        """
        Get all sales for a solicitation.

        Args:
            solicitacao_id: Solicitation ID

        Returns:
            List of sales
        """
        return await self.list(solicitacao_id=solicitacao_id)

    async def mark_as_paid(self, venda_id: str) -> Dict[str, Any]:
        """
        Mark a sale as paid.

        Args:
            venda_id: Sale ID

        Returns:
            Updated sale data
        """
        return await self.update(
            venda_id,
            VendaUpdate(status=VendaStatus.PAGO),
        )

    async def get_total_comissoes(
        self,
        parceiro_id: Optional[str] = None,
        status: Optional[VendaStatus] = None,
    ) -> float:
        """
        Get total commissions.

        Args:
            parceiro_id: Filter by partner ID
            status: Filter by status

        Returns:
            Total commission amount
        """
        vendas = await self.list(parceiro_id=parceiro_id, status=status, limit=1000)
        return sum(v.get("comissao", 0) for v in vendas)

    async def _validate_solicitacao(self, solicitacao_id: str) -> Dict[str, Any]:
        """
        Validate solicitation exists.

        Args:
            solicitacao_id: Solicitation ID

        Returns:
            Solicitation data

        Raises:
            NotFoundException: If solicitation doesn't exist
        """
        from src.db.repositories import SolicitacaoRepository

        solicitacao_repo = SolicitacaoRepository(self.db)
        return await solicitacao_repo.get_or_raise(solicitacao_id)

    async def _get_parceiro(self, parceiro_id: str) -> Dict[str, Any]:
        """
        Get partner data.

        Args:
            parceiro_id: Partner ID

        Returns:
            Partner data

        Raises:
            NotFoundException: If partner doesn't exist
        """
        from src.services.parceiros import ParceiroService

        parceiro_service = ParceiroService(self.db)
        return await parceiro_service.get_by_id_or_raise(parceiro_id)

    async def _update_solicitacao_status(self, solicitacao_id: str, status: StatusSolicitacao) -> None:
        """
        Update solicitation status.

        Args:
            solicitacao_id: Solicitation ID
            status: New status
        """
        from src.db.repositories import SolicitacaoRepository

        solicitacao_repo = SolicitacaoRepository(self.db)
        await solicitacao_repo.update(solicitacao_id, {"status": status.value, "updated_at": get_server_timestamp()})
