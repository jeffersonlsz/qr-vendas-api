"""
Tests for Leads API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestLeadsEndpoints:
    """Test lead-related endpoints."""

    def test_create_lead(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test creating a new lead."""
        # First create the partner
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        
        # Then create the lead
        response = client.post("/api/v1/leads", json=sample_lead_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["nome"] == sample_lead_data["nome"]
        assert data["data"]["parceiro_id"] == sample_lead_data["parceiro_id"]
        assert data["data"]["status"] == "novo"

    def test_create_lead_invalid_parceiro(self, client: TestClient, sample_lead_data: dict):
        """Test creating a lead with invalid partner."""
        response = client.post("/api/v1/leads", json=sample_lead_data)
        
        # Should fail because partner doesn't exist
        assert response.status_code in [400, 404]

    def test_get_lead(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test getting a lead by ID."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        create_response = client.post("/api/v1/leads", json=sample_lead_data)
        lead_id = create_response.json()["data"]["id"]
        
        # Get the lead
        response = client.get(f"/api/v1/leads/{lead_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["id"] == lead_id

    def test_list_leads(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test listing leads."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        client.post("/api/v1/leads", json=sample_lead_data)
        
        response = client.get("/api/v1/leads")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "leads" in data
        assert "total" in data

    def test_list_leads_by_parceiro(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test listing leads by partner."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        client.post("/api/v1/leads", json=sample_lead_data)
        
        response = client.get(f"/api/v1/leads/parceiro/{sample_parceiro_data['id']}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] >= 1

    def test_update_lead_status(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test updating lead status."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        create_response = client.post("/api/v1/leads", json=sample_lead_data)
        lead_id = create_response.json()["data"]["id"]
        
        # Update status
        response = client.patch(
            f"/api/v1/leads/{lead_id}",
            json={"status": "em_atendimento"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["status"] == "em_atendimento"

    def test_delete_lead(
        self,
        client: TestClient,
        sample_parceiro_data: dict,
        sample_lead_data: dict,
    ):
        """Test deleting a lead."""
        # Create partner and lead first
        client.post("/api/v1/parceiros", json=sample_parceiro_data)
        create_response = client.post("/api/v1/leads", json=sample_lead_data)
        lead_id = create_response.json()["data"]["id"]
        
        # Delete the lead
        response = client.delete(f"/api/v1/leads/{lead_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
