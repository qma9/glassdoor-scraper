from playwright.async_api import async_playwright
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pandas as pd

from typing import Dict, Annotated, List
import json
import asyncio
from dotenv import load_dotenv
import os
import sys

from database.database import engine
from database.models import Company
from database.base_models import CompanyBase


# Load .env file
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
load_dotenv()

from utils import get_db, get_unique_companies
from log.setup import logger, setup_logging

# Configure logging
setup_logging()

# Create the Company table
Company.__table__.create(bind=engine)

# Create the FastAPI instance
app = FastAPI()

# Bright Data headless browser authentication credentials
cred = {
    "host": os.getenv("HOST"),
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD"),
}
auth = f'{cred["username"]}:{cred["password"]}'
browser_url = f'wss://{auth}@{cred["host"]}'

# Database dependency
db_dependency = Annotated[Session, Depends(get_db)]


async def find_company(query: str) -> Dict[int, str]:
    """
    Find company Glassdoor ID and name by query. e.g. "nvidia" will return "NVIDIA" with ID 7633.

    Args:
        query (str): The query string to search for a company.

    Returns:
        Dict[int, str]: A dictionary containing the Glassdoor ID and name of the company.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(browser_url)
        page = await browser.new_page()

        # Abort unnecessary requests
        await page.route(
            "**/*",
            lambda route, request: route.continue_()
            if request.resource_type == "document"
            else route.abort(),
        )
        # Navigate to the search page
        await page.goto(
            f"https://www.glassdoor.com/searchsuggest/typeahead?numSuggestions=8&source=GD_V2&version=NEW&rf=full&fallback=token&input={query}",
            timeout=120000,
        )
        search_page = await page.content()

        data = json.loads(search_page)

        # Add a short pause
        await asyncio.sleep(1)

    if not data:
        logger.error(f"No search results for company {query} on Glassdoor")
        raise HTTPException(
            status_code=404,
            detail=f"No search results for company {query} on Glassdoor",
        )

    if data[0]["category"] == "company" or "multicat":
        return {
            "employer_id": data[0]["employerId"],
            "employer_name": data[0]["suggestion"],
        }
    else:
        logger.error(f"Company {query} not found on Glassdoor")
        raise HTTPException(
            status_code=404, detail=f"Company {query} not found on Glassdoor"
        )


async def add_company_to_db(company_name: str, db: Session) -> None:
    """
    Add company_id and company_name to company table.

    Args:
        company_name (str): The name of the company to add to the database.
        db (Session): The database session.

    Raises:
        HTTPException: If the data for the company is invalid.

    Returns:
        None
    """
    company_data = await find_company(company_name)

    # Validate the data with CompanyBase
    try:
        valid_data = CompanyBase.model_validate(company_data)
    except Exception as e:
        logger.error(f"Invalid data for company {company_name}: {e}")
        raise HTTPException(
            status_code=400, detail=f"Invalid data for company {company_name}: {e}"
        )

    observation = Company(**valid_data.model_dump())
    db.add(observation)
    db.commit()


@app.post("/companies/")
def find_all_companies(
    background_tasks: BackgroundTasks, companies: List[str], db: Session = db_dependency
) -> Dict[str, str]:
    """
    Endpoint to scrape company ids and names on Glassdoor and add them to company table.

    Args:
        background_tasks (BackgroundTasks): BackgroundTasks object to handle asynchronous tasks.
        companies (List[str]): List of company names to be added to the database.
        db (Session, optional): Database session object. Defaults to db_dependency.

    Returns:
        dict: A dictionary with a message indicating the completion of scraping and addition of company details to the database.
    """
    for company in companies:
        try:
            background_tasks.add_task(add_company_to_db, company, db)
        except Exception as e:
            # Log the error and the company name
            logger.error(
                f"An error occurred while adding {company} to the database: {e}"
            )
            # Raise an HTTPException with a custom message
            raise HTTPException(
                status_code=400,
                detail=f"An error occurred while adding {company} to the database: {e}",
            )

    return {"message": "Scraping complete, company id and name added to the database"}


# Load companies
df = pd.read_csv(os.getenv("COMPANY_NAMES"))

# Keep the observation with the lowest tier for each gvkey
df_unique = get_unique_companies(df)

# Convert query column to a list
companies = df_unique["employer"].tolist()


if __name__ == "__main__":
    # Create a TestClient instance
    client = TestClient(app)

    # Send a POST request to the "/companies/" endpoint
    response = client.post("/companies/", json={"companies": companies})

    # Print the response
    print(response.json())
