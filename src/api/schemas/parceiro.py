"""
Pydantic schemas for Parceiro (Partner) model.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParceiroBase(BaseModel):
    """Base schema for Parceiro with common fields."""

    nome: str = Field(..., min_length=2, max_length=100, description="Partner name")
    telefone: str = Field(..., min_length=0, max_length=20, description="Phone number")
    percentual_comissao: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Commission percentage (0-1)",
    )


class ParceiroCreate(ParceiroBase):
    """Schema for creating a new partner."""

    id: Optional[str] = Field(
        None,
        description="Optional partner ID (e.g., UBER_123). Auto-generated if not provided.",
    )
    status_cartao: str = Field(
        "DISPONIVEL",
        description="Card status. Can be 'DISPONIVEL' or 'EM_USO'.",
    )
    numero_sequencial: Optional[int] = Field(
        None,
        description="Sequential number for batch-created partners.",
    )

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate partner ID format if provided."""
        if v and not v.startswith(("UBER_", "PARCEIRO_")):
            raise ValueError("ID must start with 'UBER_' or 'PARCEIRO_'")
        return v


class ParceiroUpdate(BaseModel):
    """Schema for updating a partner."""

    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    telefone: Optional[str] = Field(None, min_length=0, max_length=20)
    percentual_comissao: Optional[float] = Field(None, ge=0, le=1)
    ativo: Optional[bool] = None
    status_cartao: Optional[str] = Field(
        None,
        description="Card status. Can be 'DISPONIVEL' or 'EM_USO'.",
    )
    numero_sequencial: Optional[int] = Field(
        None,
        description="Sequential number for batch-created partners.",
    )
    data_entrega_cartao: Optional[datetime] = Field(
        None,
        description="Timestamp when the card was delivered.",
    )
    entregue_por: Optional[str] = Field(
        None,
        max_length=100,
        description="Person who delivered the card.",
    )


class ParceiroAssociacaoUpdate(BaseModel):
    """Schema for associating a card with a partner's details."""

    nome: str = Field(..., min_length=2, max_length=100, description="Partner name")
    telefone: str = Field(..., min_length=0, max_length=20, description="Phone number")
    percentual_comissao: float = Field(
        default=0.1,
        ge=0,
        le=1,
        description="Commission percentage (0-1)",
    )
    ativo: bool = Field(True, description="Whether partner is active")




class ParceiroResponse(ParceiroBase):
    """Schema for partner response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    ativo: bool = True
    status_cartao: str = Field("DISPONIVEL", description="Card status.")
    numero_sequencial: Optional[int] = None
    codigo_cartao: Optional[str] = Field(
        None,
        description="Permanent and unique card identifier.",
    )
    data_entrega_cartao: Optional[str] = None
    entregue_por: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("created_at", "updated_at", "data_entrega_cartao", mode="before")
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
        # Firestore DatetimeWithNanoseconds or datetime-like objects
        if hasattr(v, "isoformat"):
            iso_string = v.isoformat()
            # Ensure UTC timezone indicator
            if iso_string.endswith("+00:00"):
                iso_string = iso_string.replace("+00:00", "Z")
            return iso_string
        # Already a string (pass-through)
        if isinstance(v, str):
            return v
        # Fallback
        return str(v) if v else None


class ParceiroListResponse(BaseModel):
    """Schema for partner list response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    telefone: str
    percentual_comissao: float
    ativo: bool = True
    status_cartao: str = Field("DISPONIVEL", description="Card status.")
    numero_sequencial: Optional[int] = None
    codigo_cartao: Optional[str] = Field(
        None,
        description="Permanent and unique card identifier.",
    )
    data_entrega_cartao: Optional[str] = None
    entregue_por: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("created_at", "updated_at", "data_entrega_cartao", mode="before")
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


class ParceiroResumo(BaseModel):
    """Schema for partner summary in dashboard."""

    parceiro_id: str
    nome: str
    total_solicitacoes: int = 0
    total_vendas: int = 0
    total_comissao: float = 0.0
    valor_total_vendas: float = 0.0


# --- Batch Creation Schemas ---


class ParceiroLoteCreateRequest(BaseModel):
    """Schema for batch creating partners."""

    quantidade: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Number of partners to create.",
    )
    prefixo_nome: str = Field(
        "Parceiro",
        description="Prefix for the partner name.",
    )


class ParceiroLoteCreateResponse(BaseModel):
    """Schema for batch creation response."""

    quantidade_solicitada: int
    quantidade_criada: int
    primeiro_nome: str
    ultimo_nome: str
