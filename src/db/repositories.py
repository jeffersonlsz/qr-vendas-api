"""
Base repository for Firestore operations.
Provides common CRUD operations for all repositories.
"""
import asyncio
import logging
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot
from google.cloud.firestore_v1.base_query import FieldFilter

from src.core.exceptions import NotFoundException
from src.db.connection import get_server_timestamp

T = TypeVar("T")

class BaseRepository(Generic[T]):
    """
    Base repository for Firestore operations.
    """

    def __init__(self, db: firestore.Client, collection_name: str):
        """
        Initialize BaseRepository.
        """
        self.db = db
        self.collection = db.collection(collection_name)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _serialize_doc(self, doc: DocumentSnapshot) -> Dict[str, Any]:
        """Serialize a Firestore document to a dictionary, including the ID."""
        if not doc.exists:
            return {}
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    def _generate_id(self, prefix: str) -> str:
        """
        Generate a unique ID with prefix.
        """
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8].upper()}"

    async def create(self, data: Dict[str, Any], id_prefix: str) -> str:
        """
        Creates a new document with a generated ID.
        """
        doc_id = self._generate_id(id_prefix)
        data["id"] = doc_id
        data["created_at"] = get_server_timestamp()
        data["updated_at"] = get_server_timestamp()

        doc_ref = self.collection.document(doc_id)
        await asyncio.to_thread(doc_ref.set, data)
        self.logger.info(f"Created document {doc_id} in {self.collection.id}")
        return doc_id

    async def get_or_raise(self, doc_id: str) -> Dict[str, Any]:
        """
        Retrieves a document by its ID, raising an exception if not found.
        """
        doc_ref = self.collection.document(doc_id)
        doc = await asyncio.to_thread(doc_ref.get)

        if not doc.exists:
            raise NotFoundException(resource=self.collection.id, identifier=doc_id)
        
        return self._serialize_doc(doc)

    async def list(
        self,
        filters: Optional[List[Tuple[str, str, Any]]] = None,
        order_by: Optional[str] = None,
        descending: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Lists documents with optional filtering, ordering, and pagination.
        """
        query = self.collection

        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)

        if order_by:
            direction = firestore.Query.DESCENDING if descending else firestore.Query.ASCENDING
            query = query.order_by(order_by, direction=direction)

        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)

        docs = await asyncio.to_thread(list, query.stream())
        return [self._serialize_doc(doc) for doc in docs]

    async def count(self, filters: Optional[List[Tuple[str, str, Any]]] = None) -> int:
        """
        Count documents with optional filtering.
        """
        query = self.collection
        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)
        
        # Inefficient, but works without aggregation queries.
        # For high-performance counting, a separate counter or aggregation is needed.
        docs = await asyncio.to_thread(list, query.stream())
        return len(docs)


class VendaRepository(BaseRepository):
    def __init__(self, db: firestore.Client):
        super().__init__(db, "vendas")

class SolicitacaoRepository(BaseRepository):
    def __init__(self, db: firestore.Client):
        super().__init__(db, "solicitacoes")
        
    async def find_by_parceiro_id(self, parceiro_id: str) -> List[Dict[str, Any]]:
        """
        Find solicitations by parceiro_id.
        """
        return await self.list(filters=[("parceiro_id", "==", parceiro_id)])

class ParceiroRepository(BaseRepository):
    """
    Repository for 'parceiros' collection.
    """

    def __init__(self, db: firestore.Client):
        super().__init__(db, "parceiros")

    async def get_next_sequencial(self) -> int:
        """
        Get the next sequential number for a new partner.
        """
        query = self.collection.order_by("numero_sequencial", direction=firestore.Query.DESCENDING).limit(1)
        docs = await asyncio.to_thread(query.get)
        
        if docs:
            last_sequencial = docs[0].to_dict().get("numero_sequencial", 0)
            return (last_sequencial or 0) + 1
        return 1

class OperadorRepository(BaseRepository):
    """
    Repository for the 'operadores' (operators) collection.
    """

    def __init__(self, db: firestore.Client):
        super().__init__(db, "operadores")
