"""
Pydantic schemas for Venda (Sale) model.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VendaStatus(str, Enum):
    """Sale status enumeration."""

    PENDENTE = "pendente"
    PAGO = "pago"
    CANCELADO = "cancelado"


class VendaBase(BaseModel):
    """Base schema for Venda with common fields."""

    solicitacao_id: str = Field(..., description="ID da Solicitação associada a esta venda")
    valor_venda: float = Field(..., gt=0, description="Sale value")
    descricao: Optional[str] = Field(None, max_length=500, description="Sale description")


class VendaCreate(VendaBase):
    """Schema for creating a new sale."""

    status: VendaStatus = Field(default=VendaStatus.PENDENTE)


class VendaUpdate(BaseModel):
    """Schema for updating a sale."""

    valor_venda: Optional[float] = Field(None, gt=0)
    descricao: Optional[str] = Field(None, max_length=500)
    status: Optional[VendaStatus] = None


class VendaResponse(BaseModel):
    """Schema for sale response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    solicitacao_id: str
    parceiro_id: str
    valor_venda: float
    percentual_comissao: float
    comissao: float
    status: VendaStatus
    descricao: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pago_em: Optional[str] = None

    @field_validator("created_at", "updated_at", "pago_em", mode="before")
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


class VendaListResponse(BaseModel):
    """Schema for sale list response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    solicitacao_id: str
    parceiro_id: str
    valor_venda: float
    percentual_comissao: float
    comissao: float
    status: VendaStatus
    descricao: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    pago_em: Optional[str] = None

    @field_validator("created_at", "updated_at", "pago_em", mode="before")
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


class VendaComResumo(BaseModel):
    """Schema for sale with lead and partner summary."""

    venda: VendaResponse
    solicitacao_protocolo: str
    solicitacao_cidade: Optional[str] = None
    parceiro_nome: str
