# src/api/schemas/solicitacao.py
"""
Schemas for Solicitação de Cotação feature.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr


class OperadoraPermitida(str, Enum):
    """Allowed health insurance operators."""
    AMIL = "Amil"
    BRADESCO = "Bradesco Saúde"
    SULAMERICA = "SulAmérica"
    PORTO = "Porto Saúde"
    HAPVIDA = "Hapvida"
    PLENUM = "Plenum Saúde"
    MEDSENIOR = "MedSênior"
    BEST_SENIOR = "Best Senior"
    UNITY = "Unity"


class Cobertura(str, Enum):
    """Coverage type."""
    NACIONAL = "nacional"
    REGIONAL = "regional"


class StatusSolicitacao(str, Enum):
    """Solicitação status flow."""
    NOVA = "nova"
    WHATSAPP_INICIADO = "whatsapp_iniciado"
    EM_ATENDIMENTO = "em_atendimento"
    PROPOSTA_ENVIADA = "proposta_enviada"
    CONVERTIDA = "convertida"
    PERDIDA = "perdida"


class TipoContratacao(str, Enum):
    """Contract type."""
    PF = "pf"
    PJ = "pj"


class DadosComerciaisSchema(BaseModel):
    """Schema for commercial data related to a quotation."""
    operadora: Optional[str] = Field(None, description="Nome da operadora para a proposta final.")
    plano: Optional[str] = Field(None, description="Nome do plano oferecido na proposta.")
    valor_mensal: Optional[float] = Field(None, description="Valor mensal do plano proposto.")
    valor_adesao: Optional[float] = Field(None, description="Valor da taxa de adesão da proposta.")
    vendedor: Optional[str] = Field(None, description="Nome do vendedor responsável pela negociação.")
    observacoes: Optional[str] = Field(None, description="Observações relevantes sobre a negociação ou o cliente.")


class HistoricoStatusSchema(BaseModel):
    """Schema for a status change event in the solicitation history."""
    status: StatusSolicitacao = Field(..., description="O novo status atribuído à solicitação.")
    data: datetime = Field(..., description="Data e hora da mudança de status.")
    usuario: Optional[str] = Field(None, description="ID ou nome do usuário que efetuou a alteração.")


class VidaInput(BaseModel):
    """Represents a life to be included in the quotation."""
    idade: conint(gt=0, lt=120) = Field(..., description="Idade da vida")


class SolicitacaoCore(BaseModel):
    """Core schema for a Solicitação, with shared fields."""
    parceiro_id: str = Field(..., description="ID do parceiro associado")
    vidas: List[VidaInput] = Field(..., min_length=1, description="Lista de vidas para a cotação")
    cobertura: Cobertura = Field(..., description="Tipo de cobertura desejada")
    
    # Optional fields
    cidade: Optional[str] = Field(None, description="Cidade do solicitante")
    uf: Optional[constr(min_length=2, max_length=2)] = Field(None, description="UF do solicitante")
    cpf: Optional[str] = Field(None, description="CPF do solicitante (para contrato PF)")
    cnpj: Optional[str] = Field(None, description="CNPJ do solicitante (para contrato PJ)")
    operadoras_preferidas: Optional[List[OperadoraPermitida]] = Field(None, description="Lista de operadoras de preferência")

class SolicitacaoCreate(SolicitacaoCore):
    """Schema for creating a new Solicitação."""
    @property
    def tipo_contratacao(self) -> Optional[TipoContratacao]:
        if self.cnpj:
            return TipoContratacao.PJ
        if self.cpf:
            return TipoContratacao.PF
        return None
    
    @property
    def quantidade_vidas(self) -> int:
        return len(self.vidas)


class SolicitacaoBase(SolicitacaoCore):
    """Base schema for a Solicitação, including DB fields."""
    protocolo: str = Field(..., description="Protocolo único da solicitação")
    status: StatusSolicitacao = Field(StatusSolicitacao.NOVA, description="Status atual da solicitação")
    tipo_contratacao: Optional[TipoContratacao] = Field(None, description="Tipo de contratação inferido (PF/PJ)")
    motivo_perda: Optional[str] = Field(None, description="Justificativa para a marcação da solicitação como 'perdida'.")
    dados_comerciais: Optional[DadosComerciaisSchema] = Field(None, description="Dados comerciais preenchidos ao gerar uma proposta ou converter a venda.")
    historico_status: Optional[List[HistoricoStatusSchema]] = Field(None, description="Lista de eventos de mudança de status da solicitação.")


class SolicitacaoInDB(SolicitacaoBase):
    """Schema for a Solicitação as stored in Firestore."""
    id: str = Field(..., description="ID único do documento")
    created_at: datetime = Field(..., description="Timestamp de criação (UTC)")
    updated_at: datetime = Field(..., description="Timestamp da última atualização (UTC)")


class SolicitacaoResponse(BaseModel):
    """Schema for the API response after creating a Solicitação."""
    protocolo: str


class SolicitacaoOut(SolicitacaoBase):
    """Schema for representing a Solicitação in list responses."""
    id: str = Field(..., description="ID único do documento")
    created_at: datetime = Field(..., description="Timestamp de criação (UTC)")
    updated_at: datetime = Field(..., description="Timestamp da última atualização (UTC)")


class StatusUpdateSchema(BaseModel):
    """Schema for updating the status of a solicitation."""
    status: StatusSolicitacao = Field(..., description="O novo status para a solicitação.")


class SolicitacaoListResponse(BaseModel):
    """Schema for the API response for a list of Solicitações."""
    solicitacoes: List[SolicitacaoOut]
