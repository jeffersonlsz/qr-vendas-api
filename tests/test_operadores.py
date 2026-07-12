"""
Tests for Operadores API endpoints.
"""

from fastapi.testclient import TestClient
import pytest

# Mark all tests in this module with the 'db_access' marker
pytestmark = pytest.mark.db_access

@pytest.fixture(scope="function")
def setup_operadores(db):
    """Fixture to create a predictable set of operators for testing."""
    operadores_ref = db.collection("operadores")
    
    # Clean up before test
    docs = operadores_ref.stream()
    for doc in docs:
        doc.reference.delete()

    # Create test data
    operador_ativo_1 = {"id": "OP_ATIVO_1", "nome": "Carla", "telefone": "111", "ativo": True}
    operador_ativo_2 = {"id": "OP_ATIVO_2", "nome": "Bruno", "telefone": "222", "ativo": True}
    operador_inativo = {"id": "OP_INATIVO_1", "nome": "Ana", "telefone": "333", "ativo": False}
    
    operadores_ref.document(operador_ativo_1["id"]).set(operador_ativo_1)
    operadores_ref.document(operador_ativo_2["id"]).set(operador_ativo_2)
    operadores_ref.document(operador_inativo["id"]).set(operador_inativo)
    
    return [operador_ativo_1, operador_ativo_2, operador_inativo]


class TestListOperadores:
    """Test GET /operadores endpoint."""

    API_PREFIX = "/api/v1"

    def test_list_operadores_ativos_only_default(self, client: TestClient, setup_operadores):
        """Test that GET /operadores returns only active operators by default and is sorted by name."""
        response = client.get(f"{self.API_PREFIX}/operadores")
        
        assert response.status_code == 200
        resp_data = response.json()
        
        assert resp_data["success"] is True
        assert isinstance(resp_data["data"], list)
        
        # Should return 2 active operators
        assert len(resp_data["data"]) == 2
        
        # Check if all returned operators are active
        for operador in resp_data["data"]:
            assert operador["ativo"] is True
            
        # Check for alphabetical order by 'nome'
        nomes = [op["nome"] for op in resp_data["data"]]
        assert nomes == ["Bruno", "Carla"]

    def test_list_operadores_todos_com_parametro(self, client: TestClient, setup_operadores):
        """Test that GET /operadores?ativos=false returns all operators (active and inactive), sorted by name."""
        response = client.get(f"{self.API_PREFIX}/operadores?ativos=false")
        
        assert response.status_code == 200
        resp_data = response.json()
        
        assert resp_data["success"] is True
        assert isinstance(resp_data["data"], list)
        
        # Should return all 3 operators
        assert len(resp_data["data"]) == 3
        
        # Check for alphabetical order by 'nome'
        nomes = [op["nome"] for op in resp_data["data"]]
        assert nomes == ["Ana", "Bruno", "Carla"]
        
        # Verify active and inactive are present
        ativos_status = [op["ativo"] for op in resp_data["data"]]
        assert True in ativos_status
        assert False in ativos_status

    def test_list_operadores_retorna_lista_vazia(self, client: TestClient, db):
        """Test that GET /operadores returns an empty list when there are no operators."""
        # Clean up any existing operators
        operadores_ref = db.collection("operadores")
        docs = operadores_ref.stream()
        for doc in docs:
            doc.reference.delete()
            
        response = client.get(f"{self.API_PREFIX}/operadores")
        
        assert response.status_code == 200
        resp_data = response.json()
        
        assert resp_data["success"] is True
        assert resp_data["data"] == []

    def test_create_operador(self, client: TestClient):
        """Test creating a new operator via POST /operadores."""
        sample_operador_data = {"nome": "Teste Operador", "telefone": "+5561987654321"}
        
        response = client.post(f"{self.API_PREFIX}/operadores", json=sample_operador_data)
        
        assert response.status_code == 201
        resp_data = response.json()
        
        assert resp_data["success"] is True
        assert "id" in resp_data["data"]
        assert resp_data["data"]["nome"] == sample_operador_data["nome"]
        assert resp_data["data"]["telefone"] == sample_operador_data["telefone"]
        assert resp_data["data"]["ativo"] is True
        assert "created_at" in resp_data["data"]
