from requests import RequestException, HTTPError, ConnectionError, Timeout, TooManyRedirects
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from urllib.parse import quote
import urllib3
import simplejson as json
import requests

from typing import Dict
from dotenv import load_dotenv
from time import process_time
import time
import asyncio
import os
import sys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from database import Company, get_db
from log import logger, setup_logging
from utils import Url


async def find_company(query: str) -> Dict[str, str | int]:
    """
    Search a company on Glassdoor based on the given query (company name).

    Args:
        query (str): The company name to search for.

    Returns:
        Dict[str, str | int]: A dictionary containing the employer ID and name of the best match.

    Raises:
        HTTPError: If there is an HTTP error during the request.
        ConnectionError: If there is a network connection error.
        Timeout: If the request times out.
        TooManyRedirects: If there are too many redirects during the request.
        RequestException: If there is any other request error.

    Note:
        This function requires the following environment variables to be set:
        - SMART_USERNAME: The username for the smartproxy service.
        - SMART_PASSWORD: The password for the smartproxy service.
        or 
        - OXYLABS_USERNAME: The username for the oxylabs service.
        - OXYLABS_PASSWORD: The password for the oxylabs service.
        or
        another serivce you are using.

        Depending on the proxy service you use, you will have to change the proxy and headers objects,
        as well as the request format.
    """
    # Global variables was used for Oxylab's free trial 
    # global rate_limit_exceeded

    # You will have to change the proxies and headers objects based on the proxy service you use
    # Proxy crendetials
    cred = {
        "username": os.getenv("SMART_USERNAME"),
        "password": os.getenv("SMART_PASSWORD"),
    }
    proxies = {
        "http": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
        "https": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
    }
    headers = {"X-SU-Headles": "html"}

    # Search URL with query replaced by the company name
    url = f"https://www.glassdoor.com/searchsuggest/typeahead?numSuggestions=8&source=GD_V2&version=NEW&rf=full&fallback=token&input={quote(query)}"
    
    http_attempts, max_http_attempts = 0, 10
    network_attempts, max_network_attempts = 0, 60
    while http_attempts < max_http_attempts and network_attempts < max_network_attempts:
        response = None
        try:
            response = requests.request(
                "GET", url, verify=False, proxies=proxies, headers=headers
            )
            response.raise_for_status()
            break

            # For oxylabs free trial rate limit
            # # Check if the status code is 429
            # if response.status_code == 429:
            #     logger.error(f"Exceeded proxy network rate limit: {response.status_code}")
            #     rate_limit_exceeded = True  # Set the flag
            #     return  # Stop the task

            # # Check if the status code is not 200
            # if response.status_code != 200:
            #     logger.error(f"Unexpected status code: {response.status_code}")
            #     return  # Stop the task

        except HTTPError as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'HTTP error: {e}', extra={"status_code": status_code, "URL": url})
            http_attempts += 1
            time.sleep(1)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'Network error: {e}', extra={"status_code": status_code, "URL": url})
            network_attempts += 1
            time.sleep(30)
        except RequestException as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'Other request error: {e}', extra={"status_code": status_code, "URL": url})
            return None
    
    ########################### TESTING ###########################
    # Uncomment to check response format, this will changed based on the proxy service used
    # print(f"\nRequest URL: {response.url}")
    # print(
    #     f"\nResponse status: {response.status_code}\n\nHeaders: {response.headers}\n\nBody: {response.text}\n"
    # )

    # Load the JSON string into dictionary
    # response_json = json.loads(response.text)  # oxylabs
    suggestions = json.loads(response.text)

    # Load content from the response
    # suggestions = json.loads(response_json["results"][0]["content"])   # oxylabs

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
    
    # Check if there's a direct hit in the suggestions
    direct_hit_suggestions = [
        suggestion
        for suggestion in company_suggestions
        if suggestion["directHit"] == True
    ]

    # Check if there was a direct hit before taking search suggestion with max confidence 
    if direct_hit_suggestions:
        best_match = max(
            direct_hit_suggestions, key=lambda suggestion: suggestion["confidence"]
        )
    else:
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
    """
    Add a company anme and id to the database.

    Args:
        company_name (str): The name of the company to add.
        db (Session): The database session.
        lock (asyncio.Lock): The lock used for synchronization.

    Returns:
        None
    """
    # Global variables was used for Oxylab's free trial 
    # global rate_limit_exceeded
    # # Check the flag before sending a request
    # if rate_limit_exceeded:
    #     return

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
    """
    Find all companies in the database and add them to the database with error handling.

    Args:
        db (Session): The database session.
        lock (asyncio.Lock): The lock used for synchronization.

    Returns:
        Dict[str, str]: A dictionary with a message indicating the completion of the scraping process.
    """
    # Query the Company table
    companies = db.query(Company).all()

    async def add_company_with_error_handling(
            company: Company, db: Session, lock: asyncio.Lock
        ) -> None:
            """
            Adds a company to the database with error handling.

            Args:
                company (Company): The company object to add to the database.
                db (Session): The database session.
                lock (asyncio.Lock): The lock to synchronize access to the database.

            Raises:
                Exception: If there is an error adding the company to the database.

            """
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


def create_urls(db: Session) -> None:
    """
    Update the `url_new` field for each company in the Company table.

    Args:
        db (Session): The database session.
        lock (asyncio.Lock): The lock used for synchronization.

    Returns:
        None
    """
    # Query the Company table for only employer_id, employer_name and url_new
    stmt = select(Company.employer_id, Company.employer_name, Company.url_new)
    companies = db.execute(stmt).fetchall()

    for company in companies:
        employer_id, employer_name, _url_new = company

        # Build the URL with the Url.reviews method
        url_new = Url.reviews(employer_name, employer_id)

        # Update the url_new field with the new URL
        company.url_new = url_new

    # Commit the changes to the database
    db.commit()



if __name__ == "__main__":
    # Test response, if uncomment the code below, you will have to comment the code below the test_dict
    # test_dict = asyncio.run(find_company("NVIDIA")) # Meta id: 40772, Nvidia id: 7633, Google id: 9079
    # print(f"\nTest response: {test_dict}\n")

    # Configure logging
    listener = setup_logging()

    # Create a lock to be used in the async function
    lock = asyncio.Lock()

    # For oxlabs free trial rate limit
    # Initialize the rate_limit_exceeded flag
    # rate_limit_exceeded = False

    # Start time
    start_time = process_time()

    # Get a database session
    with get_db() as db:
        # Run find_all_companies to search for all company names in employer_name field in Company table
        asyncio.run(find_all_companies(db, lock))

    # Get a database session
    with get_db() as db:
        # Run create_urls to create the URLs for each company from employer_if and employer_name fields in Company table
        asyncio.run(create_urls(db))

    # End time
    end_time = process_time()

    # Print the time
    print(f"\nTime: {end_time - start_time} seconds\n")

    # # Stop the listener
    listener.stop()

    