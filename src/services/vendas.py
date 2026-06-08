"""
Venda (Sale) Service.
Handles business logic for sale operations.
"""

import logging
from typing import Any, Dict, List, Optional

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
        # Validate lead exists and get partner info
        lead = await self._validate_lead(data.lead_id)
        parceiro = await self._get_parceiro(lead["parceiro_id"])

        # Calculate commission
        percentual_comissao = parceiro.get("percentual_comissao", 0.1)
        comissao = data.valor_venda * percentual_comissao

        venda_id = self._generate_id("venda")

        venda_data = {
            "id": venda_id,
            "lead_id": data.lead_id,
            "parceiro_id": lead["parceiro_id"],
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

        # Update lead status to converted
        await self._update_lead_status(data.lead_id)

        logger.info(f"Created sale: {venda_id} for lead: {data.lead_id}")
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
        lead_id: Optional[str] = None,
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
            lead_id: Filter by lead ID
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

        if lead_id:
            query = query.where("lead_id", "==", lead_id)

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

    async def get_by_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Get all sales for a lead.

        Args:
            lead_id: Lead ID

        Returns:
            List of sales
        """
        return await self.list(lead_id=lead_id)

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

    async def _validate_lead(self, lead_id: str) -> Dict[str, Any]:
        """
        Validate lead exists.

        Args:
            lead_id: Lead ID

        Returns:
            Lead data

        Raises:
            NotFoundException: If lead doesn't exist
        """
        from src.services.leads import LeadService

        lead_service = LeadService(self.db)
        return await lead_service.get_by_id_or_raise(lead_id)

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

    async def _update_lead_status(self, lead_id: str) -> None:
        """
        Update lead status to converted when a sale is created.

        Args:
            lead_id: Lead ID
        """
        from src.services.leads import LeadService, LeadStatus

        lead_service = LeadService(self.db)
        await lead_service.update_status(lead_id, LeadStatus.CONVERTIDO)
