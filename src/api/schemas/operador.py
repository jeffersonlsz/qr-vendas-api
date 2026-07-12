"""
Pydantic schemas for Operador (Operator) model.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OperadorBase(BaseModel):
    """Base schema for Operador with common fields."""

    nome: str = Field(..., min_length=2, max_length=100, description="Operator name")
    telefone: str = Field(..., max_length=20, description="Phone number, e.g., +5561999999999")


class OperadorCreateRequest(OperadorBase):
    """Schema for creating a new operator."""

    pass


class OperadorResponse(OperadorBase):
    """Schema for a single operator response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    ativo: bool
    created_at: datetime
    updated_at: datetime


class OperadorInfo(BaseModel):
    """Schema for essential operator information."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    nome: str
    telefone: str
    ativo: bool

