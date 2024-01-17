from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from typing import Annotated
import logging

from scraper.main import main
from database import engine
from models import Review
from utils import get_db, configure_logging

# Configure logging
configure_logging()

# Create the database tables
Review.__table__.create(bind=engine)

# Create the FastAPI instance
app = FastAPI()

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]


# Route to scrape Glassdoor overview and reviews
@app.post("/glassdoor/")
def scrape(db: Session = db_dependency):
    """
    Endpoint for scraping Glassdoor data and adding it to the database.

    Args:
        db (Session): The database session.

    Returns:
        dict: A dictionary with a message indicating the completion of scraping.
    """
    try:
        # You can now use `db` as a database session in this route
        main(db)
    except Exception as e:
        # Log the error
        logging.error(f"An error occurred while scraping: {e}")
        # Raise an HTTPException with a custom message
        raise HTTPException(
            status_code=400, detail=f"An error occurred while scraping: {e}"
        )

    return {
        "message": "Scraping complete, overview information and reviews added to respective tables"
    }


if __name__ == "__main__":
    # Create a TestClient instance
    client = TestClient(app)

    # Test the endpoint
    response = client.post("/glassdoor/")

    # Print the response
    print(response.json())
