"""
Lead Service.
Handles business logic for lead operations.
"""

import logging
from typing import Any, Dict, List, Optional

from google.cloud import firestore

from src.api.schemas.lead import LeadCreate, LeadStatus, LeadUpdate
from src.core.exceptions import NotFoundException, ValidationException
from src.db.connection import get_server_timestamp
from src.services.base import BaseService

logger = logging.getLogger(__name__)


class LeadService(BaseService):
    """
    Service for lead operations.
    Encapsulates business logic for leads.
    """

    COLLECTION_NAME = "leads"

    def __init__(self, db: firestore.Client):
        """
        Initialize service.

        Args:
            db: Firestore client
        """
        super().__init__(db, self.COLLECTION_NAME)

    async def create(
        self,
        data: LeadCreate,
        validate_parceiro: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new lead.

        Args:
            data: Lead creation data
            validate_parceiro: Whether to validate partner exists

        Returns:
            Created lead data
        """
        # Validate partner exists and is active
        if validate_parceiro:
            await self._validate_parceiro(data.parceiro_id)

        lead_id = self._generate_id("lead")

        lead_data = {
            "id": lead_id,
            "parceiro_id": data.parceiro_id,
            "nome": data.nome,
            "telefone": data.telefone,
            "origem": data.origem.value if hasattr(data.origem, "value") else data.origem,
            "status": LeadStatus.NOVO.value,
            "observacoes": data.observacoes,
            "created_at": get_server_timestamp(),
            "updated_at": get_server_timestamp(),
        }

        doc_ref = self.collection.document(lead_id)
        doc_ref.set(lead_data)

        # Re-fetch document to get materialized timestamps from Firestore
        doc = await self._fetch_document(lead_id)
        if not doc.exists:
            raise Exception(f"Failed to create lead: {lead_id}")

        logger.info(f"Created lead: {lead_id} for partner: {data.parceiro_id}")
        return self._serialize_doc(doc)

    async def get_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead data or None
        """
        doc = await self._fetch_document(lead_id)
        if doc.exists:
            return self._serialize_doc(doc)
        return None

    async def get_by_id_or_raise(self, lead_id: str) -> Dict[str, Any]:
        """
        Get lead by ID or raise exception.

        Args:
            lead_id: Lead ID

        Returns:
            Lead data

        Raises:
            NotFoundException: If lead doesn't exist
        """
        doc = await self._fetch_document(lead_id)
        return self._get_doc_or_raise(doc, lead_id)

    async def update(self, lead_id: str, data: LeadUpdate) -> Dict[str, Any]:
        """
        Update a lead.

        Args:
            lead_id: Lead ID
            data: Update data

        Returns:
            Updated lead data
        """
        # Verify lead exists
        await self.get_by_id_or_raise(lead_id)

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            # Convert enum values to strings
            if "status" in update_data and hasattr(update_data["status"], "value"):
                update_data["status"] = update_data["status"].value

            update_data["updated_at"] = get_server_timestamp()
            doc_ref = self.collection.document(lead_id)
            doc_ref.update(update_data)

        # Re-fetch to get updated data with materialized timestamps
        updated_doc = await self._fetch_document(lead_id)
        logger.info(f"Updated lead: {lead_id}")
        return self._serialize_doc(updated_doc)

    async def delete(self, lead_id: str) -> bool:
        """
        Delete a lead.

        Args:
            lead_id: Lead ID

        Returns:
            True if deleted
        """
        await self.get_by_id_or_raise(lead_id)

        doc_ref = self.collection.document(lead_id)
        doc_ref.delete()

        logger.info(f"Deleted lead: {lead_id}")
        return True

    async def list(
        self,
        parceiro_id: Optional[str] = None,
        status: Optional[LeadStatus] = None,
        order_by: str = "created_at",
        descending: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List leads with optional filtering.

        Args:
            parceiro_id: Filter by partner ID
            status: Filter by status
            order_by: Field to order by
            descending: Order direction
            limit: Maximum results
            offset: Results offset

        Returns:
            List of leads
        """
        query = self.collection

        if parceiro_id:
            query = query.where("parceiro_id", "==", parceiro_id)

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
        status: Optional[LeadStatus] = None,
    ) -> int:
        """
        Count leads.

        Args:
            parceiro_id: Filter by partner ID
            status: Filter by status

        Returns:
            Count of leads
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
        Get all leads for a partner.

        Args:
            parceiro_id: Partner ID
            limit: Maximum results

        Returns:
            List of leads
        """
        return await self.list(parceiro_id=parceiro_id, limit=limit)

    async def update_status(
        self,
        lead_id: str,
        status: LeadStatus,
    ) -> Dict[str, Any]:
        """
        Update lead status.

        Args:
            lead_id: Lead ID
            status: New status

        Returns:
            Updated lead data
        """
        return await self.update(lead_id, LeadUpdate(status=status))

    async def _validate_parceiro(self, parceiro_id: str) -> Dict[str, Any]:
        """
        Validate partner exists and is active.

        Args:
            parceiro_id: Partner ID

        Returns:
            Partner data

        Raises:
            NotFoundException: If partner doesn't exist
            ValidationException: If partner is inactive
        """
        from src.services.parceiros import ParceiroService

        parceiro_service = ParceiroService(self.db)
        return await parceiro_service.validate_and_get(parceiro_id)
