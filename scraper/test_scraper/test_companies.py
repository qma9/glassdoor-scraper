from fastapi.testclient import TestClient
from unittest.mock import patch

from companies import app
from utils import configure_logging

# Configure logging
configure_logging()

client = TestClient(app)


def test_find_all_companies_success():
    companies = ["company1", "company2", "company3"]

    with patch("app.add_company_to_db") as mock_add_company_to_db:
        response = client.post("/companies/", json={"companies": companies})

    assert response.status_code == 200
    assert response.json() == {
        "message": "Scraping complete, company id and name added to the database"
    }
    assert mock_add_company_to_db.call_count == len(companies)


def test_find_all_companies_error():
    companies = ["company1", "company2", "company3"]

    with patch("app.add_company_to_db") as mock_add_company_to_db:
        mock_add_company_to_db.side_effect = Exception("Some error")

        response = client.post("/companies/", json={"companies": companies})

    assert response.status_code == 400
    assert response.json() == {
        "detail": "An error occurred while adding company1 to the database: Some error"
    }
    assert mock_add_company_to_db.call_count == 1
    assert logging.error.call_count == len(companies)
