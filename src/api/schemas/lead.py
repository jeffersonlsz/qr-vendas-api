"""
Pydantic schemas for Lead model.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LeadStatus(str, Enum):
    """Lead status enumeration."""

    NOVO = "novo"
    EM_ATENDIMENTO = "em_atendimento"
    CONVERTIDO = "convertido"
    PERDIDO = "perdido"


class LeadOrigem(str, Enum):
    """Lead origin enumeration."""

    QR_CODE = "qr_code"
    WHATSAPP = "whatsapp"
    FORMULARIO = "formulario"
    OUTRO = "outro"


class LeadBase(BaseModel):
    """Base schema for Lead with common fields."""

    nome: str = Field(..., min_length=2, max_length=100, description="Lead name")
    telefone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    parceiro_id: str = Field(..., description="Partner ID who referred this lead")
    origem: LeadOrigem = Field(default=LeadOrigem.QR_CODE, description="Lead origin")


class LeadCreate(LeadBase):
    """Schema for creating a new lead."""

    observacoes: Optional[str] = Field(None, max_length=500, description="Optional observations")


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""

    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    telefone: Optional[str] = Field(None, min_length=10, max_length=20)
    status: Optional[LeadStatus] = None
    observacoes: Optional[str] = Field(None, max_length=500)


class LeadResponse(LeadBase):
    """Schema for lead response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    status: LeadStatus = LeadStatus.NOVO
    observacoes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def convert_timestamp(cls, v):
        """
        Convert Firestore timestamp to ISO string.

        Handles:
        - DatetimeWithNanoseconds (Firestore native)
        - Standard datetime objects
        - Already serialized strings
        - None values
        """
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            iso_string = v.isoformat()
            if iso_string.endswith("+00:00"):
                iso_string = iso_string.replace("+00:00", "Z")
            return iso_string
        if isinstance(v, str):
            return v
        return str(v) if v else None


class LeadListResponse(BaseModel):
    """Schema for lead list response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    telefone: str
    parceiro_id: str
    origem: LeadOrigem = LeadOrigem.QR_CODE
    status: LeadStatus = LeadStatus.NOVO
    observacoes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def convert_timestamp(cls, v):
        """Convert Firestore timestamp to ISO string."""
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            iso_string = v.isoformat()
            if iso_string.endswith("+00:00"):
                iso_string = iso_string.replace("+00:00", "Z")
            return iso_string
        if isinstance(v, str):
            return v
        return str(v) if v else None
