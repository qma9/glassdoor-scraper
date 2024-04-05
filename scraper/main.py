from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.engine import Row
from pydantic import ValidationError

from multiprocessing import Pool, cpu_count
from logging.handlers import QueueHandler, QueueListener
from typing import List
from time import process_time 
import json

from database import Company, Review, CompanyBase, ReviewBase, get_db, engine
from glassdoor import scrape_data  # play with relative imports
from log import logger, setup_logging, get_queue


def get_all_urls(session: Session) -> List[Row]:
        """
        Retrieves list of company Glassdoor URLs from database.

        Args:
            session (Session): The database session.

        Returns:
            List[Tuple[int, str]]: A list of tuples containing the gvkey and URL for each company.
        """
        ############# Testing #############
        ticker_to_ids = {
            'MSFT': 1651, 
            'AAPL': 1138, 
            # 'INTC': 1519, 
            # 'NVDA': 7633, 
            # 'MU': 1648, 
            'META': 40772, 
            # 'AMD': 15
        }
        return (
            session.query(Company.url_new)
            .filter(Company.is_gvkey == 1,           # Edit filter for user needs
                    Company.url_new.isnot(None), 
                    Company.ticker.isnot(None),
                    Company.employer_id.in_(ticker_to_ids.values())  # Remove for production 
            )
            .all()
        )


def scrape_and_store(urls: List[Row]) -> None:

    ########## Debug print statement ########## 
    print(f"Processing {len(urls)} URLs")

    # Set up a QueueHandler for the logger in this worker process
    queue = get_queue()
    handler = QueueHandler(queue)
    logger.addHandler(handler)

    with get_db() as session:
        for url in urls:
            try:
                overview_data, reviews_data = scrape_data(url.url_new, max_pages=50) 

                ########## Debug print statement ##########
                # print(f"Scraped data for {url}")

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error scraping data: {e}", extra={"url": url})
                continue  # Skip to the next company if there is an error

            # Validate the data with CompanyBase
            try:
                valid_data = CompanyBase(**overview_data)

                ########## Debug print statement ##########
                print(f"Validated company data for {url}")

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

                    if key in valid_data.__dict__:

                        ########## Debug print statement ##########
                        # print(f"{key}: {type(value)}") 

                        setattr(company, key, value)

                session.commit()

                ########## Debug print statement ##########
                print(f"Committed company data for {url}")

            except (IntegrityError, Exception) as e:
                session.rollback()
                logger.error(
                    f"Error updating company data: {e}",
                    extra={"url": url}, 
                )
                continue  # Skip to the next company if there is an error

            # Initialize a counter
            counter = 0

            # For each item in your scraped data...
            for review in reviews_data.values():  
                try:
                    # Validate the data with ReviewBase
                    valid_review = ReviewBase(**review)

                    ########## Debug print statement ##########
                    # print(f"Validated review data for {url}")

                except ValidationError as e:
                    logger.error(
                        f"Invalid data for review: {e}", extra={"review": review}
                    )
                    continue  # Skip to the next review if the data is invalid

                try:
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
                        session.commit()

                        ########## Debug print statement ##########
                        print(f"Committed 100 reviews for {url}")

                        counter = 0
                except (IntegrityError, Exception) as e:
                    session.rollback()
                    logger.error(
                        f"Error updating review data: {e}",
                        extra={"url": url, "review": review}, 
                    )

            # Commit any remaining reviews that didn't reach the counter limit
            if counter > 0:
                session.commit()

                ########## Debug print statement ##########
                print(f"Committed remaining reviews for {url}")
            
            ########## Debug print statement ##########
            print(f"Finished processing {len(urls)} URLs")


def main() -> None:
    # Set up a QueueListener for the logger in the main process
    queue = get_queue()
    listener = QueueListener(queue, *logger.handlers)
    listener.start()

    Review.__table__.create(bind=engine, checkfirst=True) 

    with get_db() as session:
        urls = get_all_urls(session)

     # Divide the URLs among the workers
    num_workers = cpu_count()
    if num_workers > len(urls):
        num_workers = len(urls)
    urls_per_worker, remainder = divmod(len(urls), num_workers)
    urls_for_workers = [urls[i:i + urls_per_worker + (1 if i < remainder else 0)] for i in range(0, len(urls), urls_per_worker)]

    # Create a pool of worker processes
    with Pool(num_workers) as pool:
        ########## Debug print statement ##########
        print(f"Starting work with {num_workers} workers")

        # Use the pool to run the scrape_and_store function for each URL in parallel
        pool.map(scrape_and_store, urls_for_workers)

        ########## Debug print statement ##########
        print("Finished processing all URLs")

    # Stop the QueueListener
    listener.stop()


if __name__ == "__main__":

    # Setup logging
    listener, lt = setup_logging()

    # Start time
    start_time = process_time()

    # Run the main function
    main()

    # End time
    end_time = process_time()

    # Log the time taken
    logger.info(
        f"Scraping complete, time taken: {end_time - start_time} seconds",
        extra={"time": end_time - start_time},
    )
    print(f"\n\nTime taken: {end_time - start_time} seconds\n\n")

    # Stop listener
    log_queue = listener.queue
    log_queue.put(None)
    lt.join()
    listener.stop()

