"""
Firestore client connection and initialization.
Supports both production Firestore and local emulator.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from google.cloud import firestore  # type: ignore[import]

from src.core.config import Settings

import json
from google.oauth2 import service_account


logger = logging.getLogger(__name__)

# Global client instance
_firestore_client: Optional[firestore.Client] = None


def initialize_firestore(settings: Settings) -> firestore.Client:
    """
    Initialize Firestore client based on settings.

    Args:
        settings: Application settings

    Returns:
        Firestore client instance
    """
    global _firestore_client

    if _firestore_client is not None:
        return _firestore_client

    try:
        # Check if using emulator
        if settings.using_firestore_emulator:
            logger.info(f"Connecting to Firestore emulator at {settings.firestore_emulator_host}")
            # Set environment variable for emulator connection
            os.environ["FIRESTORE_EMULATOR_HOST"] = settings.firestore_emulator_host
            _firestore_client = firestore.Client(
                project=settings.firestore_project_id or "demo-project",
            )
        else:
            # Production connection
            if settings.firestore_credentials_path:
                logger.info(
                    f"Connecting to Firestore with credentials: {settings.firestore_credentials_path}"
                )
                _firestore_client = firestore.Client.from_service_account_json(
                    settings.firestore_credentials_path
                )
                            
            else:
                credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

                if credentials_json:
                    logger.info(
                        "Connecting to Firestore using credentials JSON from environment"
                    )

                    credentials_info = json.loads(credentials_json)

                    credentials = service_account.Credentials.from_service_account_info(
                        credentials_info
                    )

                    _firestore_client = firestore.Client(
                        project=credentials_info["project_id"],
                        credentials=credentials,
                    )

                else:
                    logger.info("Connecting to Firestore using default credentials")

                    _firestore_client = firestore.Client(
                        project=settings.firestore_project_id
                    )
                


        # Test connection (skip in development to allow offline startup)
        if not settings.is_development:
            _firestore_client.collection("_health_check").limit(1).get()
            logger.info("Firestore connection established successfully")
        else:
            logger.info("Firestore client initialized (development mode - skipping health check)")

        return _firestore_client

    except Exception as e:
        logger.error(f"Failed to initialize Firestore: {e}")
        raise


def get_firestore_client() -> firestore.Client:
    """
    Get the Firestore client instance.
    Must be initialized first with initialize_firestore().
    """
    if _firestore_client is None:
        raise RuntimeError(
            "Firestore client not initialized. Call initialize_firestore() first."
        )
    return _firestore_client


def get_db() -> firestore.Client:
    """
    Dependency function for FastAPI.
    Returns the Firestore database client.
    """
    return get_firestore_client()


def get_server_timestamp():
    """Get server timestamp for consistent timestamp handling."""
    return firestore.SERVER_TIMESTAMP


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Firestore timestamp (milliseconds)."""
    return int(dt.timestamp() * 1000)


def timestamp_to_datetime(ts) -> Optional[datetime]:
    """Convert Firestore timestamp to datetime."""
    if ts is None:
        return None
    if hasattr(ts, "to_datetime"):
        return ts.to_datetime()
    return datetime.fromtimestamp(ts / 1000)


def serialize_firestore_datetime(value: Any) -> Optional[str]:
    """
    Convert Firestore DatetimeWithNanoseconds to ISO 8601 string.

    Handles multiple timestamp formats:
    - DatetimeWithNanoseconds (Firestore native)
    - Standard datetime objects
    - Already serialized strings
    - None values

    Args:
        value: The timestamp value to serialize

    Returns:
        ISO 8601 formatted string (e.g., "2024-03-31T15:30:00Z") or None
    """
    if value is None:
        return None

    # Firestore DatetimeWithNanoseconds or datetime-like objects
    if hasattr(value, "isoformat"):
        iso_string = value.isoformat()
        # Ensure UTC timezone indicator
        if iso_string.endswith("+00:00"):
            iso_string = iso_string.replace("+00:00", "Z")
        return iso_string

    # Already a string (pass-through)
    if isinstance(value, str):
        return value

    # Fallback: try to convert to datetime
    try:
        return datetime.fromtimestamp(float(value)).isoformat()
    except (TypeError, ValueError, OSError):
        logger.warning(f"Could not serialize timestamp value: {value!r}")
        return str(value) if value else None


def serialize_parceiro(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize a partner document from Firestore to API response format.

    Converts Firestore-specific types to JSON-serializable formats:
    - DatetimeWithNanoseconds -> ISO 8601 string
    - Ensures all fields are properly typed

    Args:
        doc_data: Raw document data from Firestore

    Returns:
        Serialized partner data ready for API response
    """
    return {
        "id": doc_data.get("id", ""),
        "nome": doc_data.get("nome", ""),
        "telefone": doc_data.get("telefone", ""),
        "percentual_comissao": doc_data.get("percentual_comissao", 0.1),
        "ativo": doc_data.get("ativo", False),
        "created_at": serialize_firestore_datetime(doc_data.get("created_at")),
        "updated_at": serialize_firestore_datetime(doc_data.get("updated_at")),
    }
