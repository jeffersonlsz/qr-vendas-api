from pydantic import BaseModel
from typing import List

class CotacaoRequest(BaseModel):
    idade: int
    valor_atual: float
    regime_trabalho: str
    cidade: str

class CotacaoResponse(BaseModel):
    economia_estimada: float
    percentual_economia: float
    valor_estimado: float
    operadoras: List[str]
    mensagem: str
