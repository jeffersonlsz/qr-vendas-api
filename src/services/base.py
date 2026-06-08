"""
Base service for Firestore operations.
Provides common patterns and helpers for all services.
"""

import logging
from typing import Any, Dict, Generic, Optional, TypeVar
from google.cloud import firestore
from google.cloud.firestore_v1.base_document import DocumentSnapshot

from src.core.exceptions import NotFoundException
from src.db.connection import serialize_firestore_datetime

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseService(Generic[T]):
    """
    Base service for Firestore operations.
    Provides common patterns for document serialization and retrieval.
    """

    COLLECTION_NAME: str

    def __init__(self, db: firestore.Client, collection_name: str):
        """
        Initialize base service.

        Args:
            db: Firestore client
            collection_name: Name of the Firestore collection
        """
        self.db = db
        self.collection_name = collection_name
        self.collection = db.collection(collection_name)

    def _serialize_doc(self, doc: DocumentSnapshot) -> Dict[str, Any]:
        """
        Serialize a Firestore document to a dictionary.

        This method ensures that:
        - Document data is properly converted from Firestore types
        - The document ID is included in the result
        - DatetimeWithNanoseconds fields are converted to ISO strings
        - SERVER_TIMESTAMP sentinels are not returned (they are materialized on read)

        Args:
            doc: Firestore document snapshot

        Returns:
            Serialized document data with ID
        """
        if not doc.exists:
            return {}
        
        doc_data = doc.to_dict()
        
        # Serialize datetime fields to ISO strings
        for field in ["created_at", "updated_at"]:
            if field in doc_data and doc_data[field] is not None:
                doc_data[field] = serialize_firestore_datetime(doc_data[field])
        
        return {**doc_data, "id": doc.id}

    def _get_doc_or_raise(
        self,
        doc: DocumentSnapshot,
        doc_id: str,
    ) -> Dict[str, Any]:
        """
        Get document data or raise NotFoundException.

        Args:
            doc: Firestore document snapshot
            doc_id: Document ID (for error message)

        Returns:
            Serialized document data

        Raises:
            NotFoundException: If document doesn't exist
        """
        if not doc.exists:
            resource_name = self.collection_name[:-1].title()  # Singular form
            raise NotFoundException(resource_name, doc_id)
        return self._serialize_doc(doc)

    async def _fetch_document(self, doc_id: str) -> DocumentSnapshot:
        """
        Fetch a document from Firestore.

        Args:
            doc_id: Document ID

        Returns:
            Document snapshot
        """
        doc_ref = self.collection.document(doc_id)
        return doc_ref.get()

    async def _fetch_and_serialize(
        self,
        doc_id: str,
        raise_on_missing: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch and serialize a document.

        Args:
            doc_id: Document ID
            raise_on_missing: Raise exception if document doesn't exist

        Returns:
            Serialized document data or None

        Raises:
            NotFoundException: If raise_on_missing is True and doc doesn't exist
        """
        doc = await self._fetch_document(doc_id)

        if raise_on_missing:
            return self._get_doc_or_raise(doc, doc_id)

        if doc.exists:
            return self._serialize_doc(doc)
        return None

    def _generate_id(self, prefix: str) -> str:
        """
        Generate a unique ID with prefix.

        Args:
            prefix: ID prefix (e.g., "PARC", "LEAD", "VENDA")

        Returns:
            Generated ID
        """
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:8]}"
