# tests/api/routers/test_templates.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import app
from src.core.exceptions import NotFoundException


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_db():
    with patch("src.db.connection.get_db") as mock:
        yield mock


def test_save_layout_success(client, mock_db):
    """
    Test successful creation/update of a template layout.
    """
    template_id = "modelo-cartaz-001.png"
    layout_payload = {
        "version": 1,
        "elements": {
            "qr": {
                "leftPercent": 0.5,
                "topPercent": 0.6,
                "sizePercent": 0.4
            }
        }
    }

    # Mock the service layer
    with patch("src.api.routers.templates.TemplateLayoutService") as MockService:
        mock_service_instance = MockService.return_value
        # The save_layout service method returns the full template document
        mock_service_instance.save_layout = AsyncMock(return_value={
            "id": template_id,
            "layout": layout_payload
        })

        response = client.put(f"/templates/{template_id}/layout", json=layout_payload)

        assert response.status_code == 200
        assert response.json() == layout_payload
        mock_service_instance.save_layout.assert_awaited_once()


def test_get_layout_found(client, mock_db):
    """
    Test successfully retrieving an existing template layout.
    """
    template_id = "modelo-cartaz-001.png"
    expected_layout = {
        "version": 1,
        "elements": {
            "qr": {
                "leftPercent": 0.5,
                "topPercent": 0.6,
                "sizePercent": 0.4
            }
        }
    }

    with patch("src.api.routers.templates.TemplateLayoutService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.get_layout = AsyncMock(return_value=expected_layout)

        response = client.get(f"/templates/{template_id}/layout")

        assert response.status_code == 200
        assert response.json() == expected_layout
        mock_service_instance.get_layout.assert_awaited_with(template_id)


def test_get_layout_not_found(client, mock_db):
    """
    Test retrieving a layout that does not exist, expecting a 404.
    """
    template_id = "non-existent-template.png"

    with patch("src.api.routers.templates.TemplateLayoutService") as MockService:
        mock_service_instance = MockService.return_value
        # Simulate the service returning None when the layout is not found
        mock_service_instance.get_layout = AsyncMock(return_value=None)

        response = client.get(f"/templates/{template_id}/layout")

        assert response.status_code == 404
        assert response.json() == {"detail": f"Layout not found for template '{template_id}'."}


def test_save_layout_internal_error(client, mock_db):
    """
    Test internal server error during layout save.
    """
    template_id = "modelo-cartaz-001.png"
    layout_payload = {
        "version": 1,
        "elements": {
            "qr": {
                "leftPercent": 0.5,
                "topPercent": 0.6,
                "sizePercent": 0.4
            }
        }
    }

    with patch("src.api.routers.templates.TemplateLayoutService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.save_layout = AsyncMock(side_effect=Exception("Database error"))

        response = client.put(f"/templates/{template_id}/layout", json=layout_payload)

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error."}