"""
Base repository for Firestore operations.
Provides common CRUD operations for all repositories.
"""

import logging
from typing import Any, Dict, Generic, List, Optional, TypeVar

from google.cloud import firestore  # type: ignore[import]

from src.core.exceptions import DatabaseException, NotFoundException

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic base repository for Firestore collections.
    Provides common CRUD operations.
    """

    def __init__(self, db: firestore.Client, collection_name: str):
        """
        Initialize repository.

        Args:
            db: Firestore client
            collection_name: Name of the Firestore collection
        """
        self.db = db
        self.collection_name = collection_name
        self.collection = db.collection(collection_name)

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID with prefix."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    async def create(
        self,
        data: Dict[str, Any],
        doc_id: Optional[str] = None,
        id_prefix: Optional[str] = None,
    ) -> str:
        """
        Create a new document.

        Args:
            data: Document data
            doc_id: Optional document ID (auto-generated if not provided)
            id_prefix: Prefix for auto-generated ID

        Returns:
            Document ID
        """
        try:
            if doc_id is None:
                if id_prefix:
                    doc_id = self._generate_id(id_prefix)
                else:
                    doc_ref = self.collection.document()
                    doc_id = doc_ref.id

            doc_ref = self.collection.document(doc_id)
            doc_ref.set(data)

            logger.debug(f"Created document {doc_id} in {self.collection_name}")
            return doc_id

        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise DatabaseException(f"Failed to create document: {e}")

    async def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document data or None if not found
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc = doc_ref.get()

            if doc.exists:
                return {**doc.to_dict(), "id": doc.id}
            return None

        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            raise DatabaseException(f"Failed to get document: {e}")

    async def get_or_raise(self, doc_id: str) -> Dict[str, Any]:
        """
        Get a document by ID or raise NotFoundException.

        Args:
            doc_id: Document ID

        Returns:
            Document data

        Raises:
            NotFoundException: If document doesn't exist
        """
        doc = await self.get(doc_id)
        if doc is None:
            raise NotFoundException(
                resource=self.collection_name[:-1].title(),  # Singular form
                identifier=doc_id,
            )
        return doc

    async def update(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """
        Update a document.

        Args:
            doc_id: Document ID
            data: Fields to update

        Returns:
            True if updated successfully
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.update(data)

            logger.debug(f"Updated document {doc_id} in {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise DatabaseException(f"Failed to update document: {e}")

    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted successfully
        """
        try:
            doc_ref = self.collection.document(doc_id)
            doc_ref.delete()

            logger.debug(f"Deleted document {doc_id} in {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise DatabaseException(f"Failed to delete document: {e}")

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        List documents with optional filtering and pagination.

        Args:
            filters: Dictionary of field-value pairs to filter
            order_by: Field to order by
            descending: Order in descending order
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of documents
        """
        try:
            query = self.collection

            # Apply filters
            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)

            # Apply ordering
            if order_by:
                query = query.order_by(order_by, direction=firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING)
            else:
                # Default ordering by created_at if exists
                query = query.order_by("created_at", direction=firestore.Query.DESCENDING)

            # Apply pagination
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            docs = query.stream()
            return [{**doc.to_dict(), "id": doc.id} for doc in docs]

        except Exception as e:
            logger.error(f"Error listing documents in {self.collection_name}: {e}")
            raise DatabaseException(f"Failed to list documents: {e}")

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents with optional filtering.

        Args:
            filters: Dictionary of field-value pairs to filter

        Returns:
            Count of documents
        """
        try:
            query = self.collection

            if filters:
                for field, value in filters.items():
                    query = query.where(field, "==", value)

            docs = query.stream()
            return len(list(docs))

        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {e}")
            raise DatabaseException(f"Failed to count documents: {e}")

    async def find_by_field(
        self,
        field: str,
        value: Any,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find documents by a specific field value.

        Args:
            field: Field name
            value: Value to search for
            limit: Maximum number of documents to return

        Returns:
            List of matching documents
        """
        return await self.list(filters={field: value}, limit=limit)


class ParceiroRepository(BaseRepository):
    """
    Repository for parceiros (partners) collection.
    Handles partner-related Firestore operations.
    """

    def __init__(self, db: firestore.Client):
        """
        Initialize ParceiroRepository.

        Args:
            db: Firestore client
        """
        super().__init__(db, "parceiros")

    async def get_by_id(self, parceiro_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a partner by ID.

        Args:
            parceiro_id: Partner ID

        Returns:
            Partner data or None if not found
        """
        return await self.get(parceiro_id)

    async def get_active_partners(self) -> List[Dict[str, Any]]:
        """
        Get all active partners.

        Returns:
            List of active partners
        """
        return await self.list(filters={"ativo": True})

    async def create_partner(
        self,
        nome: str,
        telefone: str,
        percentual_comissao: float = 0.1,
        ativo: bool = True,
    ) -> str:
        """
        Create a new partner.

        Args:
            nome: Partner name
            telefone: Partner phone
            percentual_comissao: Commission percentage (default 10%)
            ativo: Whether partner is active

        Returns:
            Created partner ID
        """
        from datetime import datetime

        data = {
            "nome": nome,
            "telefone": telefone,
            "percentual_comissao": percentual_comissao,
            "ativo": ativo,
            "created_at": datetime.utcnow(),
        }
        return await self.create(data, id_prefix="PARC")


class LeadRepository(BaseRepository):
    """
    Repository for leads collection.
    Handles lead-related Firestore operations.
    """

    def __init__(self, db: firestore.Client):
        """
        Initialize LeadRepository.

        Args:
            db: Firestore client
        """
        super().__init__(db, "leads")

    async def get_by_id(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a lead by ID.

        Args:
            lead_id: Lead ID

        Returns:
            Lead data or None if not found
        """
        return await self.get(lead_id)

    async def create_lead(
        self,
        nome: str,
        telefone: str,
        parceiro_id: str,
        origem: str = "qr_code",
        status: str = "novo",
    ) -> str:
        """
        Create a new lead.

        Args:
            nome: Lead name
            telefone: Lead phone
            parceiro_id: Associated partner ID
            origem: Lead origin (default "qr_code")
            status: Lead status (default "novo")

        Returns:
            Created lead ID
        """
        from datetime import datetime

        data = {
            "nome": nome,
            "telefone": telefone,
            "parceiro_id": parceiro_id,
            "origem": origem,
            "status": status,
            "created_at": datetime.utcnow(),
        }
        return await self.create(data, id_prefix="LEAD")

    async def get_by_parceiro(self, parceiro_id: str) -> List[Dict[str, Any]]:
        """
        Get all leads from a specific partner.

        Args:
            parceiro_id: Partner ID

        Returns:
            List of leads
        """
        return await self.list(filters={"parceiro_id": parceiro_id})

    async def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get all leads with a specific status.

        Args:
            status: Lead status

        Returns:
            List of leads
        """
        return await self.list(filters={"status": status})

    async def update_status(self, lead_id: str, status: str) -> bool:
        """
        Update lead status.

        Args:
            lead_id: Lead ID
            status: New status

        Returns:
            True if updated successfully
        """
        return await self.update(lead_id, {"status": status})


class VendaRepository(BaseRepository):
    """
    Repository for vendas (sales) collection.
    Handles sales-related Firestore operations.
    """

    def __init__(self, db: firestore.Client):
        """
        Initialize VendaRepository.

        Args:
            db: Firestore client
        """
        super().__init__(db, "vendas")

    async def get_by_id(self, venda_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a sale by ID.

        Args:
            venda_id: Sale ID

        Returns:
            Sale data or None if not found
        """
        return await self.get(venda_id)

    async def create_venda(
        self,
        lead_id: str,
        parceiro_id: str,
        valor_venda: float,
        percentual_comissao: float,
        status: str = "pendente",
    ) -> str:
        """
        Create a new sale.

        Args:
            lead_id: Associated lead ID
            parceiro_id: Associated partner ID
            valor_venda: Sale value
            percentual_comissao: Commission percentage
            status: Sale status (default "pendente")

        Returns:
            Created sale ID
        """
        from datetime import datetime

        comissao = valor_venda * percentual_comissao

        data = {
            "lead_id": lead_id,
            "parceiro_id": parceiro_id,
            "valor_venda": valor_venda,
            "percentual_comissao": percentual_comissao,
            "comissao": comissao,
            "status": status,
            "created_at": datetime.utcnow(),
        }
        return await self.create(data, id_prefix="VENDA")

    async def get_by_parceiro(self, parceiro_id: str) -> List[Dict[str, Any]]:
        """
        Get all sales from a specific partner.

        Args:
            parceiro_id: Partner ID

        Returns:
            List of sales
        """
        return await self.list(filters={"parceiro_id": parceiro_id})

    async def get_by_lead(self, lead_id: str) -> List[Dict[str, Any]]:
        """
        Get all sales from a specific lead.

        Args:
            lead_id: Lead ID

        Returns:
            List of sales
        """
        return await self.list(filters={"lead_id": lead_id})

    async def update_status(self, venda_id: str, status: str) -> bool:
        """
        Update sale status.

        Args:
            venda_id: Sale ID
            status: New status

        Returns:
            True if updated successfully
        """
        return await self.update(venda_id, {"status": status})

    async def get_pending_sales(self) -> List[Dict[str, Any]]:
        """
        Get all pending sales.

        Returns:
            List of pending sales
        """
        return await self.list(filters={"status": "pendente"})

    async def get_paid_sales(self) -> List[Dict[str, Any]]:
        """
        Get all paid sales.

        Returns:
            List of paid sales
        """
        return await self.list(filters={"status": "pago"})
