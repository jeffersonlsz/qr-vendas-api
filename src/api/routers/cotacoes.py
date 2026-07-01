# src\api\routers\cotacoes.py
from fastapi import APIRouter
from src.api.schemas.cotacao import CotacaoRequest, CotacaoResponse

router = APIRouter(prefix="/cotacoes", tags=["Cotações"])

@router.post("", response_model=CotacaoResponse)
async def criar_cotacao(request: CotacaoRequest):
    """
    Realiza uma simulação de cotação baseada na idade e valor atual.
    
    Regras:
    - idade < 40 -> desconto de 25%
    - idade >= 40 -> desconto de 10%
    """
    if request.idade < 40:
        desconto = 0.25
    else:
        desconto = 0.10
    
    valor_estimado = request.valor_atual * (1 - desconto)
    economia_estimada = request.valor_atual - valor_estimado
    percentual_economia = desconto * 100
    
    return CotacaoResponse(
        economia_estimada=economia_estimada,
        percentual_economia=percentual_economia,
        valor_estimado=valor_estimado,
        operadoras=["Amil", "Bradesco", "Hapvida"],
        mensagem="Existem opções compatíveis com seu perfil."
    )
