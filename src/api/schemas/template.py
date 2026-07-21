# src/api/schemas/template.py
"""
Pydantic schemas for Template and Template Layout management.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field, confloat


class ElementLayoutSchema(BaseModel):
    """Defines the position and size of a dynamic element on a template."""
    leftPercent: confloat(ge=0, le=1) = Field(..., description="Percentage distance from the left edge (0.0 to 1.0).")
    topPercent: confloat(ge=0, le=1) = Field(..., description="Percentage distance from the top edge (0.0 to 1.0).")
    sizePercent: confloat(gt=0) = Field(..., description="Percentage size of the element relative to a base dimension (e.g., page width).")


class TemplateLayoutSchema(BaseModel):
    """
    Represents the complete layout structure for a template,
    containing all dynamic elements.
    """
    version: int = Field(..., description="Layout structure version.")
    elements: Dict[str, ElementLayoutSchema] = Field(..., description="Dictionary of all layout elements.")

    class Config:
        # Allows ignoring extra fields sent in the payload,
        # making it forward-compatible.
        extra = 'ignore'


class TemplateInDB(BaseModel):
    """Represents a template document as stored in the database."""
    id: str
    layout: Optional[TemplateLayoutSchema] = None