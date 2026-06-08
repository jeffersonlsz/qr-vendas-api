"""
Pydantic schemas for Dashboard and Metrics.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MetricasParceiro(BaseModel):
    """Metrics for a specific partner."""

    total_leads: int = Field(default=0, description="Total leads generated")
    leads_novos: int = Field(default=0, description="New leads")
    leads_em_atendimento: int = Field(default=0, description="Leads in attendance")
    leads_convertidos: int = Field(default=0, description="Converted leads")
    leads_perdidos: int = Field(default=0, description="Lost leads")
    total_vendas: int = Field(default=0, description="Total sales")
    vendas_pendentes: int = Field(default=0, description="Pending sales")
    vendas_pagas: int = Field(default=0, description="Paid sales")
    valor_total_vendas: float = Field(default=0.0, description="Total sales value")
    total_comissao: float = Field(default=0.0, description="Total commission")
    comissao_paga: float = Field(default=0.0, description="Paid commission")
    comissao_pendente: float = Field(default=0.0, description="Pending commission")
    taxa_conversao: float = Field(default=0.0, description="Conversion rate (0-1)")


class DashboardResumo(BaseModel):
    """Dashboard summary for a partner."""

    parceiro_id: str
    parceiro_nome: str
    metricas: MetricasParceiro
    ultimas_vendas: list[dict] = Field(default_factory=list)
    ultimos_leads: list[dict] = Field(default_factory=list)


class DashboardGeral(BaseModel):
    """General dashboard for admin view."""

    total_parceiros: int = Field(default=0, description="Total partners")
    parceiros_ativos: int = Field(default=0, description="Active partners")
    total_leads: int = Field(default=0, description="Total leads")
    total_vendas: int = Field(default=0, description="Total sales")
    valor_total_vendas: float = Field(default=0.0, description="Total sales value")
    total_comissoes: float = Field(default=0.0, description="Total commissions")
    taxa_conversao_geral: float = Field(default=0.0, description="Overall conversion rate")
    top_parceiros: list[dict] = Field(default_factory=list, description="Top partners by sales")


class PeriodoMetricas(BaseModel):
    """Metrics for a specific period."""

    data_inicio: datetime
    data_fim: datetime
    total_leads: int = 0
    total_vendas: int = 0
    valor_total_vendas: float = 0.0
    total_comissao: float = 0.0
