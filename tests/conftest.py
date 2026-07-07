"""
Test fixtures for pytest.
"""

import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

# Set environment variables before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["FIRESTORE_PROJECT_ID"] = "demo-project"
os.environ["DEBUG"] = "true"


@pytest.fixture(scope="session")
def test_settings() -> dict:
    """Test settings configuration."""
    return {
        "environment": "test",
        "debug": True,
        "firestore_emulator_host": "localhost:8080",
        "firestore_project_id": "demo-project",
    }


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """
    Create test client for API testing.
    
    Note: This requires Firestore emulator running on localhost:8080
    """
    from src.main import app
    
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_parceiro_data() -> dict:
    """Sample partner data for tests."""
    return {
        "id": "UBER_TEST_001",
        "nome": "Test Partner",
        "telefone": "+55999999999",
        "percentual_comissao": 0.15,
    }


@pytest.fixture
def sample_solicitacao_data(sample_parceiro_data) -> dict:
    """Sample solicitation data for tests."""
    return {
        "parceiro_id": sample_parceiro_data["id"],
        "vidas": [{"idade": 30}, {"idade": 25}],
        "cobertura": "regional",
        "cidade": "São Paulo",
        "uf": "SP",
    }



@pytest.fixture(scope="function")
def db(client: TestClient) -> Generator:
    """
    Firestore client fixture that provides a clean slate for each test.
    Depends on the `client` fixture to ensure the app and DB are initialized.
    Deletes all documents from 'parceiros' collection before each test run.
    """
    from src.db.connection import get_firestore_client
    
    db_client = get_firestore_client()
    
    collections_to_clear = ["parceiros", "solicitacoes", "vendas"]
    for collection_name in collections_to_clear:
        docs = db_client.collection(collection_name).stream()
        for doc in docs:
            doc.reference.delete()
        
    yield db_client


@pytest.fixture(scope="function")
def parceiro_service(db) -> "ParceiroService":
    """Provides a ParceiroService instance with a clean DB."""
    from src.services.parceiros import ParceiroService
    return ParceiroService(db)


@pytest.fixture
def sample_venda_data() -> dict:
    """Sample sale data for tests."""
    return {
        "solicitacao_id": "SOL_TEST_123",
        "valor_venda": 1500.00,
        "descricao": "Test sale",
    }
