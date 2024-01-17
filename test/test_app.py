from fastapi.testclient import TestClient
import pytest

from unittest.mock import patch
from utils import configure_logging

from app import app

configure_logging()


@patch("app.main")
def test_scrape_success(mock_main):
    client = TestClient(app)
    response = client.post("/glassdoor/")
    mock_main.assert_called_once()
    assert response.status_code == 200
    assert response.json() == {
        "message": "Scraping complete, overview information and reviews added to respective tables"
    }


@patch("app.main", side_effect=Exception("Test error"))
def test_scrape_error(mock_main):
    client = TestClient(app)
    response = client.post("/glassdoor/")
    mock_main.assert_called_once()
    assert response.status_code == 400
    assert response.json() == {"detail": "An error occurred while scraping: Test error"}
