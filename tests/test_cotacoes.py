import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import get_settings

settings = get_settings()
client = TestClient(app)
API_PREFIX = settings.api_prefix

def test_cotacao_abaixo_40_anos():
    """Teste para idade < 40 (25% de desconto)"""
    payload = {
        "idade": 35,
        "valor_atual": 850,
        "regime_trabalho": "CLT",
        "cidade": "Brasilia"
    }
    response = client.post(f"{API_PREFIX}/cotacoes", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 850 * 0.25 = 212.5
    # 850 - 212.5 = 637.5
    assert data["percentual_economia"] == 25
    assert data["economia_estimada"] == 212.5
    assert data["valor_estimado"] == 637.5
    assert "Amil" in data["operadoras"]
    assert data["mensagem"] == "Existem opções compatíveis com seu perfil."

def test_cotacao_acima_40_anos():
    """Teste para idade > 40 (10% de desconto)"""
    payload = {
        "idade": 45,
        "valor_atual": 1000,
        "regime_trabalho": "Autônomo",
        "cidade": "São Paulo"
    }
    response = client.post(f"{API_PREFIX}/cotacoes", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # 1000 * 0.10 = 100
    # 1000 - 100 = 900
    assert data["percentual_economia"] == 10
    assert data["economia_estimada"] == 100
    assert data["valor_estimado"] == 900

def test_cotacao_exatamente_40_anos():
    """Teste para idade == 40 (10% de desconto)"""
    payload = {
        "idade": 40,
        "valor_atual": 1000,
        "regime_trabalho": "CLT",
        "cidade": "Rio de Janeiro"
    }
    response = client.post(f"{API_PREFIX}/cotacoes", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["percentual_economia"] == 10
