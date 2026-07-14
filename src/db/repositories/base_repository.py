# src/db/repositories/base_repository.py
"""
Base repository for Firestore operations.
Provides common CRUD operations for all repositories.
"""
import asyncio
import logging
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar

from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

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

    async def update(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates a document by its ID.
        """
        # Ensure the document exists before updating
        await self.get_or_raise(doc_id)

        update_data = data.copy()
        update_data["updated_at"] = get_server_timestamp()

        doc_ref = self.collection.document(doc_id)
        await asyncio.to_thread(doc_ref.update, update_data)

        self.logger.info(f"Updated document {doc_id} in {self.collection.id}")
        
        # Re-fetch the document to get the updated version with server timestamp
        updated_doc = await self.get_or_raise(doc_id)
        return updated_doc

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

    async def count(
        self,
        filters: Optional[List[Tuple[str, str, Any]]] = None,
    ) -> int:
        """
        Counts documents with optional filtering.
        """
        query = self.collection

        if filters:
            for field, op, value in filters:
                query = query.where(field, op, value)

        # Use Firestore's count aggregation
        aggregate_query = query.count()
        result = await asyncio.to_thread(aggregate_query.get)
        # The result is a list of AggregateResult, we need the first one
        # and then its value property
        return result[0][0].value