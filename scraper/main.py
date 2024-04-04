from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.engine import Row
from pydantic import ValidationError

from typing import List
from time import process_time 
import asyncio
import json

from database import Company, Review, CompanyBase, ReviewBase, get_db, engine, Base
from glassdoor import scrape_data  # play with relative imports
from log.setup import logger, setup_logging


async def main() -> None:
    Review.__table__.create(bind=engine, checkfirst=True) 
    lock = asyncio.Lock()

    def get_all_urls(session: Session) -> List[Row]:
        """
        Retrieves list of company Glassdoor URLs from database.

        Args:
            session (Session): The database session.

        Returns:
            List[Tuple[int, str]]: A list of tuples containing the gvkey and URL for each company.
        """
        # Testing 
        ticker_to_ids = {
            'MSFT': 1651, 
            'AAPL': 1138, 
            'INTC': 1519, 
            'NVDA': 7633, 
            'MU': 1648, 
            'META': 40772, 
            'AMD': 15
        }
        return (
            session.query(Company.url_new)
            .filter(Company.is_gvkey == 1, 
                    Company.url_new.isnot(None), 
                    Company.ticker.isnot(None),
                    Company.employer_id.in_(ticker_to_ids.values())  # testing
            )
            .all()
        )

    # Create a new event loop
    loop = asyncio.new_event_loop() 
    asyncio.set_event_loop(loop)

    with get_db() as session:
        urls = get_all_urls(session)

        for url in urls:
            try:
                overview_data, reviews_data = await scrape_data(url.url_new, max_pages=3000)  # can add max_pages if want to limit number of reviews from a single company
            except (json.JSONDecodeError, KeyError, asyncio.TimeoutError) as e:               # FYI: 10 reviews per page
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
                for review in reviews_data.values():  
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
        f"Scraping complete, time taken: {end_time - start_time} seconds",
        extra={"time": end_time - start_time},
    )
    print(f"Time taken: {end_time - start_time} seconds")

    # Stop listener
    listener.stop()
