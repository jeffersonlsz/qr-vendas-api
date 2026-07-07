"""
Tests for consolidating the Parceiros backend logic, including batch creation,
sequential numbering, and card code generation.
"""

import asyncio
from typing import List
import pytest
from fastapi.testclient import TestClient
from google.cloud import firestore

# All tests in this file use the database fixture
pytestmark = pytest.mark.usefixtures("db")


class TestParceirosConsolidation:
    """
    Test suite for features implemented in Phases 1, 2, and 2.5.
    Focuses on integration tests via the API client.
    """

    def test_create_individual_parceiro(self, client: TestClient, db: firestore.Client):
        """
        Tests the creation of a single partner, validating all auto-generated fields.
        Corresponds to the "Cadastro individual" mandatory test case.
        """
        parceiro_data = {
            "nome": "John Doe",
            "telefone": "11987654321",
            "percentual_comissao": 0.1,
        }
        response = client.post("/api/v1/parceiros", json=parceiro_data)

        # 1. Validate API Response
        assert response.status_code == 201
        response_data = response.json()["data"]

        assert response_data["nome"] == "John Doe"
        assert response_data["ativo"] is True
        assert response_data["status_cartao"] == "DISPONIVEL"
        assert response_data["data_entrega_cartao"] is None
        assert response_data["entregue_por"] is None

        # Check for sequential number and card code
        assert response_data["numero_sequencial"] == 1
        assert response_data["codigo_cartao"] == "CARD-000001"
        parceiro_id = response_data["id"]

        # 2. Validate Database State
        doc_ref = db.collection("parceiros").document(parceiro_id)
        doc = doc_ref.get()

        assert doc.exists
        db_data = doc.to_dict()

        assert db_data["nome"] == "John Doe"
        assert db_data["ativo"] is True
        assert db_data["status_cartao"] == "DISPONIVEL"
        assert db_data["data_entrega_cartao"] is None
        assert db_data["entregue_por"] is None
        assert db_data["numero_sequencial"] == 1
        assert db_data["codigo_cartao"] == "CARD-000001"

    def test_create_parceiros_lote(self, client: TestClient, db: firestore.Client):
        """
        Tests creating a batch of partners, validating the response and data integrity.
        Corresponds to the "Cadastro em lote" mandatory test case.
        """
        QUANTIDADE = 5
        PREFIXO = "Lote Test"
        response = client.post(
            "/api/v1/parceiros/lote",
            json={"quantidade": QUANTIDADE, "prefixo_nome": PREFIXO},
        )

        # 1. Validate API Response
        assert response.status_code == 201
        response_data = response.json()["data"]

        assert response_data["quantidade_solicitada"] == QUANTIDADE
        assert response_data["quantidade_criada"] == QUANTIDADE
        assert response_data["primeiro_nome"] == f"{PREFIXO} 0001"
        assert response_data["ultimo_nome"] == f"{PREFIXO} {QUANTIDADE:04d}"

        # 2. Validate Database State
        docs = db.collection("parceiros").stream()
        all_parceiros = [doc.to_dict() for doc in docs]

        assert len(all_parceiros) == QUANTIDADE

        numeros_sequenciais = {p["numero_sequencial"] for p in all_parceiros}
        codigos_cartao = {p["codigo_cartao"] for p in all_parceiros}

        assert len(numeros_sequenciais) == QUANTIDADE  # All unique
        assert len(codigos_cartao) == QUANTIDADE      # All unique
        assert min(numeros_sequenciais) == 1
        assert max(numeros_sequenciais) == QUANTIDADE

    def test_numero_sequencial_continuity(self, client: TestClient, db: firestore.Client):
        """
        Tests that the sequential number is continuous across single and batch creations.
        Corresponds to the "Numeração" mandatory test case.
        """
        # 1. Create a single partner
        res1 = client.post("/api/v1/parceiros", json={"nome": "Primeiro", "telefone": "11999999991"})
        assert res1.status_code == 201
        assert res1.json()["data"]["numero_sequencial"] == 1

        # 2. Create a batch of 5
        res2 = client.post("/api/v1/parceiros/lote", json={"quantidade": 5})
        assert res2.status_code == 201
        assert res2.json()["data"]["primeiro_nome"] == "Parceiro 0002"
        assert res2.json()["data"]["ultimo_nome"] == "Parceiro 0006"

        # 3. Create another single partner
        res3 = client.post("/api/v1/parceiros", json={"nome": "Setimo", "telefone": "11999999997"})
        assert res3.status_code == 201
        assert res3.json()["data"]["numero_sequencial"] == 7

        # 4. Validate final DB state
        docs = db.collection("parceiros").order_by("numero_sequencial").stream()
        all_parceiros = [doc.to_dict() for doc in docs]

        assert len(all_parceiros) == 7
        expected_seq = [1, 2, 3, 4, 5, 6, 7]
        actual_seq = [p["numero_sequencial"] for p in all_parceiros]
        assert actual_seq == expected_seq

    def test_create_parceiros_lote_multi_batch(self, client: TestClient, db: firestore.Client):
        """
        Tests creating a batch of over 500 partners, forcing multiple
        batch writes to Firestore.
        Corresponds to the "Batch Write" mandatory test case.
        """
        QUANTIDADE = 501
        response = client.post(
            "/api/v1/parceiros/lote",
            json={"quantidade": QUANTIDADE, "prefixo_nome": "MultiBatch"},
        )
        assert response.status_code == 201
        
        # Verify the count in the database directly
        docs = db.collection("parceiros").stream()
        count = len(list(docs))
        assert count == QUANTIDADE

    def test_update_parceiro_immutability(self, client: TestClient):
        """
        Tests that updating a partner does not change immutable fields.
        Corresponds to the "Atualização" mandatory test case.
        """
        # 1. Create a partner
        res_create = client.post("/api/v1/parceiros", json={"nome": "Imutável", "telefone": "11999999123"})
        assert res_create.status_code == 201
        data_created = res_create.json()["data"]
        parceiro_id = data_created["id"]
        original_seq = data_created["numero_sequencial"]
        original_code = data_created["codigo_cartao"]

        # 2. Update the partner
        update_payload = {"nome": "Nome Alterado", "telefone": "11988888987"}
        res_update = client.patch(f"/api/v1/parceiros/{parceiro_id}", json=update_payload)
        assert res_update.status_code == 200
        data_updated = res_update.json()["data"]

        # 3. Verify immutable fields
        assert data_updated["nome"] == "Nome Alterado"
        assert data_updated["numero_sequencial"] == original_seq
        assert data_updated["codigo_cartao"] == original_code

    def test_backward_compatibility_for_old_parceiros(self, client: TestClient, db: firestore.Client):
        """
        Tests that the API can handle partners created before the new fields were added.
        Corresponds to the "Parceiros antigos" mandatory test case.
        """
        parceiro_id_antigo = "OLD_PARTNER_001"
        # Manually create a document with an old structure
        db.collection("parceiros").document(parceiro_id_antigo).set({
            "id": parceiro_id_antigo,
            "nome": "Parceiro Antigo",
            "telefone": "1199998888",
            "ativo": True
            # Missing status_cartao, numero_sequencial, codigo_cartao, etc.
        })

        response = client.get(f"/api/v1/parceiros/{parceiro_id_antigo}")
        assert response.status_code == 200
        data = response.json()["data"]

        # Default value from schema for status_cartao
        assert data["status_cartao"] == "DISPONIVEL" 
        # Optional fields should be None
        assert data["numero_sequencial"] is None
        assert data["codigo_cartao"] is None
        assert data["data_entrega_cartao"] is None
        assert data["entregue_por"] is None

    @pytest.mark.parametrize("quantity", [0, -1, 1001])
    def test_create_lote_invalid_quantity(self, client: TestClient, quantity: int):
        """
        Tests that the batch creation endpoint rejects invalid quantities.
        Corresponds to the "Casos inválidos" mandatory test case.
        """
        response = client.post(
            "/api/v1/parceiros/lote",
            json={"quantidade": quantity, "prefixo_nome": "Invalid"},
        )
        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="Demonstrates the race condition in sequential number generation.",
        strict=True
    )
    async def test_concurrency_race_condition(self, db: firestore.Client):
        """
        Attempts to trigger the race condition in numero_sequencial generation.
        This test is expected to fail with the current implementation.
        Corresponds to the "Concorrência" analysis case.
        """
        from httpx import AsyncClient
        from src.main import app

        NUM_CONCURRENT_REQUESTS = 10
        tasks = []

        # Use a longer phone number to pass validation
        valid_phone = "11999990000"

        async with AsyncClient(app=app, base_url="http://test") as aclient:
            for i in range(NUM_CONCURRENT_REQUESTS):
                task = aclient.post(
                    "/api/v1/parceiros",
                    json={"nome": f"Concurrent-{i}", "telefone": f"{valid_phone[:-2]}{i:02d}"}
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)

        # Check that all requests were technically successful
        for response in responses:
            assert response.status_code == 201

        # Now, check the database for duplicate numero_sequencial
        docs = db.collection("parceiros").stream()
        all_parceiros = [doc.to_dict() for doc in docs]

        assert len(all_parceiros) == NUM_CONCURRENT_REQUESTS
        
        numeros_sequenciais = {p["numero_sequencial"] for p in all_parceiros}
        
        # This assertion is expected to fail due to the race condition
        assert len(numeros_sequenciais) == NUM_CONCURRENT_REQUESTS

