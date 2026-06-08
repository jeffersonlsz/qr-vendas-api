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
def sample_lead_data(sample_parceiro_data) -> dict:
    """Sample lead data for tests."""
    return {
        "nome": "Test Lead",
        "telefone": "+55988888888",
        "parceiro_id": sample_parceiro_data["id"],
        "origem": "qr_code",
        "observacoes": "Test observation",
    }


@pytest.fixture
def sample_venda_data(sample_lead_data) -> dict:
    """Sample sale data for tests."""
    return {
        "lead_id": None,  # Will be set after lead creation
        "valor_venda": 1500.00,
        "descricao": "Test sale",
    }
