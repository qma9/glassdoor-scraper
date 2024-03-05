from requests.exceptions import RequestException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from urllib.parse import quote
import simplejson as json
import requests

from typing import Dict
from dotenv import load_dotenv
from time import process_time
import asyncio
import os
import sys


# Load .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import Company, get_db
from log import logger, setup_logging


async def find_company(query: str) -> Dict[str, str | int]:

    global rate_limit_exceeded

    # You will have to change the request format based on the proxy service used
    # Proxy crendetials
    cred = {
        "username": os.getenv("OXY_USERNAME"),
        "password": os.getenv("OXY_PASSWORD"),
    }

    # Structure payload.
    payload = {
        "source": "universal",
        "url": f"https://www.glassdoor.com/searchsuggest/typeahead?numSuggestions=8&source=GD_V2&version=NEW&rf=full&fallback=token&input={quote(query)}",
    }

    try:
        # Get response.
        response = requests.request(
            "POST",
            "https://realtime.oxylabs.io/v1/queries",
            auth=(cred["username"], cred["password"]),
            json=payload,
        )

        ########################### TESTING ###########################
        # Check response format, will changed based on proxy service used
        # print(f"\nRequest URL: {response.url}\nPayload: {payload}")
        # print(
        #     f"\nResponse status: {response.status_code}\nHeaders: {response.headers}\nBody: {response.text}"
        # )

        # Check if the status code is 429
        if response.status_code == 429:
            logger.error(f"Exceeded proxy network rate limit: {response.status_code}")
            rate_limit_exceeded = True  # Set the flag
            return  # Stop the task

        # Check if the status code is not 200
        if response.status_code != 200:
            logger.error(f"Unexpected status code: {response.status_code}")
            return  # Stop the task

    except RequestException as e:
        raise Exception(f"Request error to Glassdoor: {e}")

    # Load the JSON string into dictionary
    response_json = json.loads(response.text)

    # TESTING
    # print(f"\nResponse JSON:\n{response_json}\n")

    # Load content from the response
    suggestions = json.loads(response_json["results"][0]["content"])

    # Filter the suggestions to only include those with category as company or multicat
    company_suggestions = [
        suggestion
        for suggestion in suggestions
        if suggestion["category"] in ["company", "multicat"]
    ]

    # If there are no company suggestions, raise an exception
    if not company_suggestions:
        logger.error(f"No search results on Glassdoor: {query}")
        return None

    # Select the suggestion with the highest confidence value
    best_match = max(
        company_suggestions, key=lambda suggestion: suggestion["confidence"]
    )

    # Check if employer_name is None or an empty string
    if not best_match["suggestion"]:
        logger.error(f"Employer name not found: {query}")
        return None

    return {
        "employer_id": best_match["employerId"],
        "employer_name": best_match["suggestion"],
    }


async def add_company_to_db(company_name: str, db: Session, lock: asyncio.Lock) -> None:

    global rate_limit_exceeded
    # Check the flag before sending a request
    if rate_limit_exceeded:
        return

    async with lock:
        company_data = await find_company(company_name)

        # Check if a company with the same employer_name already exists
        existing_company = (
            db.query(Company).filter_by(employer_name=company_name).first()
        )

        if company_data is None:
            if existing_company:
                existing_company.id_not_found = True
                db.commit()
            return
        elif company_data == {}:
            return

        if existing_company is not None:
            # If it does, update the existing company
            for key, value in company_data.items():
                setattr(existing_company, key, value)
        else:
            # If it doesn't, add a new company
            observation = Company(**company_data)
            db.add(observation)

        try:
            db.commit()
            logger.info(f"Successfully added company to database: {company_name}")
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Error for database commit: {company_name}, {str(e.orig)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error for database commit: {company_name}, {e}")


async def find_all_companies(db: Session, lock: asyncio.Lock) -> Dict[str, str]:

    # Query the Company table
    companies = db.query(Company).all()

    async def add_company_with_error_handling(
        company: Company, db: Session, lock: asyncio.Lock
    ) -> None:
        try:
            await add_company_to_db(company.employer_name, db, lock)
        except Exception as e:
            logger.error(f"Error adding to database: {company.employer_name}, {e}")

    tasks = []
    for company in companies:
        # Skip companies that were not found in a previous run
        if company.id_not_found != 1:
            tasks.append(add_company_with_error_handling(company, db, lock))

    await asyncio.gather(*tasks)

    logger.info("Scraping complete, employer id and name added to the database")
    return {"message": "Scraping complete, employer id added to the database"}


if __name__ == "__main__":
    # Configure logging
    listener = setup_logging()

    # Create a lock to be used in the async function
    lock = asyncio.Lock()

    # Initialize the rate_limit_exceeded flag
    rate_limit_exceeded = False

    # Start time
    start_time = process_time()

    # Get a database session
    with get_db() as db:
        asyncio.run(find_all_companies(db, lock))

    # End time
    end_time = process_time()

    # Print the time
    print(f"\nTime: {end_time - start_time} seconds\n")

    # # Stop the listener
    listener.stop()
