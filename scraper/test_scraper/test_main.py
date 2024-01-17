from unittest.mock import patch
from typing import List, Tuple
from sqlalchemy.orm import Session
from pydantic import ValidationError
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import asyncio
import logging

from scraper.main import main
from database.models import Company, Review
from database.base_models import CompanyBase, ReviewBase
from scraper.glassdoor import scrape_data, Url, Region
from utils import configure_logging
from database.database import URL_DB

# Configure logging
configure_logging()


@pytest.fixture
def db() -> Session:
    # Set up the database connection and session
    engine = create_engine(URL_DB)  # Use an in-memory SQLite database for testing
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create a new session
    db: Session = SessionLocal()

    # Use the session in your tests
    yield db

    # Close the session after the tests are done
    db.close()


def test_main_success(db: Session):
    # Mock the scrape_data function
    with patch("main.scrape_data") as mock_scrape_data:
        # Set the return value of the mock function
        mock_scrape_data.return_value = (
            {"employer_name": "eBay Motors Group", "employer_id": 123},
            [{"review_id": 1, "rating": 5, "content": "Great company"}],
        )

        # Call the main function
        main(db)

    # Assert that the company and review data are saved correctly
    company = db.query(Company).filter(Company.employer_id == 123).first()
    assert company.employer_name == "eBay Motors Group"

    review = db.query(Review).filter(Review.review_id == 1).first()
    assert review.rating == 5
    assert review.content == "Great company"


def test_main_invalid_data(db: Session):
    # Mock the scrape_data function
    with patch("main.scrape_data") as mock_scrape_data:
        # Set the return value of the mock function to invalid data
        mock_scrape_data.return_value = (
            {"employer_name": "eBay Motors Group", "employer_id": 123},
            [{"review_id": 1, "rating": "invalid", "content": "Great company"}],
        )

        # Call the main function
        main(db)

    # Assert that the invalid review data is logged
    assert logging.error.call_count == 1
