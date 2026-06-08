"""
Dashboard Service.
Handles business logic for dashboard and metrics operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google.cloud import firestore

from src.api.schemas.dashboard import (
    DashboardGeral,
    DashboardResumo,
    MetricasParceiro,
    PeriodoMetricas,
)
from src.api.schemas.lead import LeadStatus
from src.api.schemas.venda import VendaStatus
from src.core.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class DashboardService:
    """
    Service for dashboard and metrics operations.
    Provides aggregated data for dashboards.
    """

    def __init__(self, db: firestore.Client):
        """
        Initialize service.

        Args:
            db: Firestore client
        """
        self.db = db

    async def get_parceiro_dashboard(
        self,
        parceiro_id: str,
    ) -> DashboardResumo:
        """
        Get dashboard summary for a specific partner.

        Args:
            parceiro_id: Partner ID

        Returns:
            Partner dashboard with metrics
        """
        from src.services.parceiros import ParceiroService

        parceiro_service = ParceiroService(self.db)
        parceiro = await parceiro_service.get_by_id_or_raise(parceiro_id)

        metricas = await self._calculate_parceiro_metricas(parceiro_id)

        # Get recent sales
        from src.services.vendas import VendaService

        venda_service = VendaService(self.db)
        vendas_recentes = await venda_service.list(
            parceiro_id=parceiro_id,
            limit=5,
        )

        # Get recent leads
        from src.services.leads import LeadService

        lead_service = LeadService(self.db)
        leads_recentes = await lead_service.list(
            parceiro_id=parceiro_id,
            limit=5,
        )

        return DashboardResumo(
            parceiro_id=parceiro_id,
            parceiro_nome=parceiro["nome"],
            metricas=metricas,
            ultimas_vendas=[
                {
                    "id": v["id"],
                    "valor_venda": v["valor_venda"],
                    "comissao": v["comissao"],
                    "status": v["status"],
                    "created_at": v["created_at"],
                }
                for v in vendas_recentes
            ],
            ultimos_leads=[
                {
                    "id": l["id"],
                    "nome": l["nome"],
                    "status": l["status"],
                    "created_at": l["created_at"],
                }
                for l in leads_recentes
            ],
        )

    async def get_geral_dashboard(self) -> DashboardGeral:
        """
        Get general dashboard for admin view.

        Returns:
            General dashboard with aggregated metrics
        """
        from src.services.parceiros import ParceiroService
        from src.services.leads import LeadService
        from src.services.vendas import VendaService

        parceiro_service = ParceiroService(self.db)
        lead_service = LeadService(self.db)
        venda_service = VendaService(self.db)

        # Count partners
        total_parceiros = await parceiro_service.count()
        parceiros_ativos = await parceiro_service.count(ativo=True)

        # Count leads
        total_leads = await lead_service.count()
        leads_convertidos = await lead_service.count(status=LeadStatus.CONVERTIDO)

        # Count sales
        total_vendas = await venda_service.count()
        valor_total_vendas = await venda_service.get_total_comissoes()

        # Calculate total commissions
        total_comissoes = await venda_service.get_total_comissoes()

        # Calculate conversion rate
        taxa_conversao = (leads_convertidos / total_leads) if total_leads > 0 else 0.0

        # Get top partners
        top_parceiros = await self._get_top_parceiros(limit=5)

        return DashboardGeral(
            total_parceiros=total_parceiros,
            parceiros_ativos=parceiros_ativos,
            total_leads=total_leads,
            total_vendas=total_vendas,
            valor_total_vendas=valor_total_vendas,
            total_comissoes=total_comissoes,
            taxa_conversao_geral=taxa_conversao,
            top_parceiros=top_parceiros,
        )

    async def get_periodo_metricas(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        parceiro_id: Optional[str] = None,
    ) -> PeriodoMetricas:
        """
        Get metrics for a specific period.

        Args:
            data_inicio: Start date
            data_fim: End date
            parceiro_id: Optional partner ID filter

        Returns:
            Metrics for the period
        """
        from src.services.leads import LeadService
        from src.services.vendas import VendaService

        lead_service = LeadService(self.db)
        venda_service = VendaService(self.db)

        # Get leads in period
        leads = await lead_service.list(
            parceiro_id=parceiro_id,
            limit=1000,
        )

        # Filter by date range (client-side filtering for simplicity)
        leads_no_periodo = [
            l
            for l in leads
            if self._is_in_period(l.get("created_at"), data_inicio, data_fim)
        ]

        # Get sales in period
        vendas = await venda_service.list(
            parceiro_id=parceiro_id,
            limit=1000,
        )

        vendas_no_periodo = [
            v
            for v in vendas
            if self._is_in_period(v.get("created_at"), data_inicio, data_fim)
        ]

        total_leads = len(leads_no_periodo)
        total_vendas = len(vendas_no_periodo)
        valor_total_vendas = sum(v.get("valor_venda", 0) for v in vendas_no_periodo)
        total_comissao = sum(v.get("comissao", 0) for v in vendas_no_periodo)

        return PeriodoMetricas(
            data_inicio=data_inicio,
            data_fim=data_fim,
            total_leads=total_leads,
            total_vendas=total_vendas,
            valor_total_vendas=valor_total_vendas,
            total_comissao=total_comissao,
        )

    async def _calculate_parceiro_metricas(
        self,
        parceiro_id: str,
    ) -> MetricasParceiro:
        """
        Calculate detailed metrics for a partner.

        Args:
            parceiro_id: Partner ID

        Returns:
            Partner metrics
        """
        from src.services.leads import LeadService
        from src.services.vendas import VendaService

        lead_service = LeadService(self.db)
        venda_service = VendaService(self.db)

        # Lead counts by status
        total_leads = await lead_service.count(parceiro_id=parceiro_id)
        leads_novos = await lead_service.count(
            parceiro_id=parceiro_id,
            status=LeadStatus.NOVO,
        )
        leads_em_atendimento = await lead_service.count(
            parceiro_id=parceiro_id,
            status=LeadStatus.EM_ATENDIMENTO,
        )
        leads_convertidos = await lead_service.count(
            parceiro_id=parceiro_id,
            status=LeadStatus.CONVERTIDO,
        )
        leads_perdidos = await lead_service.count(
            parceiro_id=parceiro_id,
            status=LeadStatus.PERDIDO,
        )

        # Sales counts by status
        total_vendas = await venda_service.count(parceiro_id=parceiro_id)
        vendas_pendentes = await venda_service.count(
            parceiro_id=parceiro_id,
            status=VendaStatus.PENDENTE,
        )
        vendas_pagas = await venda_service.count(
            parceiro_id=parceiro_id,
            status=VendaStatus.PAGO,
        )

        # Financial metrics
        todas_vendas = await venda_service.list(parceiro_id=parceiro_id, limit=1000)
        valor_total_vendas = sum(v.get("valor_venda", 0) for v in todas_vendas)
        total_comissao = sum(v.get("comissao", 0) for v in todas_vendas)

        comissao_paga = sum(
            v.get("comissao", 0)
            for v in todas_vendas
            if v.get("status") == VendaStatus.PAGO.value
        )
        comissao_pendente = total_comissao - comissao_paga

        # Conversion rate
        taxa_conversao = (leads_convertidos / total_leads) if total_leads > 0 else 0.0

        return MetricasParceiro(
            total_leads=total_leads,
            leads_novos=leads_novos,
            leads_em_atendimento=leads_em_atendimento,
            leads_convertidos=leads_convertidos,
            leads_perdidos=leads_perdidos,
            total_vendas=total_vendas,
            vendas_pendentes=vendas_pendentes,
            vendas_pagas=vendas_pagas,
            valor_total_vendas=valor_total_vendas,
            total_comissao=total_comissao,
            comissao_paga=comissao_paga,
            comissao_pendente=comissao_pendente,
            taxa_conversao=taxa_conversao,
        )

    async def _get_top_parceiros(
        self,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get top partners by sales value.

        Args:
            limit: Number of partners to return

        Returns:
            List of top partners with metrics
        """
        from src.services.parceiros import ParceiroService
        from src.services.vendas import VendaService

        parceiro_service = ParceiroService(self.db)
        venda_service = VendaService(self.db)

        # Get all active partners
        parceiros = await parceiro_service.list(ativo=True, limit=100)

        # Calculate sales for each partner
        parceiros_com_vendas = []
        for parceiro in parceiros:
            resumo = await parceiro_service.get_resumo(parceiro["id"])
            if resumo.total_vendas > 0:
                parceiros_com_vendas.append(
                    {
                        "parceiro_id": parceiro["id"],
                        "nome": parceiro["nome"],
                        "total_vendas": resumo.total_vendas,
                        "valor_total": resumo.valor_total_vendas,
                        "total_comissao": resumo.total_comissao,
                    }
                )

        # Sort by total sales value and return top N
        parceiros_com_vendas.sort(key=lambda x: x["valor_total"], reverse=True)
        return parceiros_com_vendas[:limit]

    def _is_in_period(
        self,
        timestamp,
        data_inicio: datetime,
        data_fim: datetime,
    ) -> bool:
        """
        Check if a timestamp is within a period.

        Args:
            timestamp: Timestamp to check
            data_inicio: Start date
            data_fim: End date

        Returns:
            True if in period
        """
        if timestamp is None:
            return False

        # Convert Firestore timestamp to datetime if needed
        if hasattr(timestamp, "to_datetime"):
            timestamp = timestamp.to_datetime()
        elif isinstance(timestamp, (int, float)):
            timestamp = datetime.fromtimestamp(timestamp / 1000)

        return data_inicio <= timestamp <= data_fim
