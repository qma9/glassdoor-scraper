from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import ValidationError

from typing import Tuple, List
from time import process_time
import asyncio
import json

from database import Company, Review, CompanyBase, ReviewBase, get_db
from scraper.glassdoor import scrape_data
from log.setup import logger, setup_logging


async def main(session: Session) -> None:
    lock = asyncio.Lock()

    def get_all_urls(session: Session) -> List[Tuple[int, str]]:

        # Set to filter for public companies with a gvkey
        return (
            session.query(Company.url_new)
            .filter(Company.is_gvkey == 1, Company.url_new.isnot(None))
            .all()
        )

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    with get_db() as session:
        urls = get_all_urls(session)

        for url in urls:
            try:
                overview_data, reviews_data = loop.run_until_complete(scrape_data(url))
            except (json.JSONDecodeError, KeyError, asyncio.TimeoutError) as e:
                logger.error(
                    f"Error scraping data: {e}",
                    extra={"url": url},
                )
                continue  # Skip to the next company if there is an error

            # Validate the data with CompanyBase
            try:
                valid_data = CompanyBase(**overview_data)
            except ValidationError as e:
                logger.error(
                    f"Invalid data from {url}: {e}",
                    extra={"overview": overview_data},
                )
                continue  # Skip to the next company if the data is invalid
            try:
                # Fetch the existing company from the database
                company = (
                    session.query(Company)
                    .filter(Company.employer_id == valid_data.employer_id)
                    .first()
                )

                # Update the company's fields with the new data
                for key, value in valid_data.model_dump().items():
                    setattr(company, key, value)

                session.commit()

                # Initialize a counter
                counter = 0

                # For each item in your scraped data...
                for review in reviews_data:
                    # Validate the data with ReviewBase
                    try:
                        valid_review = ReviewBase(**review)
                    except ValidationError as e:
                        logger.error(
                            f"Invalid data for review: {e}", extra={"review": review}
                        )
                        continue  # Skip to the next review if the data is invalid

                    # Create a new Review object with the validated data
                    observation = Review(**valid_review.model_dump())

                    # Associate the review with the company
                    observation.company = company

                    # Add the new review to the session
                    session.add(observation)

                    # Increment the counter
                    counter += 1

                    # If the counter reaches 100, commit the session and reset the counter
                    if counter >= 100:
                        async with lock:
                            session.commit()
                        counter = 0

                # Commit any remaining reviews that didn't reach the counter limit
                if counter > 0:
                    async with lock:
                        session.commit()
            except (IntegrityError, Exception) as e:
                session.rollback()
                logger.error(
                    f"Error updating data: {e}",
                    extra={"url": url},
                )


if __name__ == "__main__":

    # Setup logging
    listener = setup_logging()

    # Start time
    start_time = process_time()

    # Run the main function
    asyncio.run(main())

    # End time
    end_time = process_time()

    # Log the time taken
    logger.info(
        f"Time taken: {end_time - start_time} seconds",
        extra={"time": end_time - start_time},
    )
    print(f"Time taken: {end_time - start_time} seconds")

    # Stop listener
    listener.stop()
