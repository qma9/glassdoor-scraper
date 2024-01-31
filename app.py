from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from typing import Annotated

from scraper.main import main
from database.database import engine
from database.models import Review
from log.setup import logger, setup_logging
from utils import get_db

# Configure logging
setup_logging()

# Create the database tables
Review.__table__.create(bind=engine)

# Create the FastAPI instance
app = FastAPI()

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]


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
        logger.error(f"An error occurred while scraping: {e}")
        # Raise an HTTPException with a custom message
        raise HTTPException(
            status_code=500, detail=f"An error occurred while scraping: {e}"
        )

    logger.info(
        "Scraping complete, overview information and reviews added to respective tables"
    )
    return {
        "message": "Scraping complete, overview information and reviews added to respective tables"
    }


if __name__ == "__main__":
    # Create a TestClient instance
    client = TestClient(app)

    # Run the endpoint
    response = client.post("/glassdoor/")

    # Print the response
    print(response.json())
