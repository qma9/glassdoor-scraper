from sqlalchemy.orm import Session
from pydantic import ValidationError

import asyncio
from typing import Tuple, List

from database.models import Company, Review
from database.base_models import CompanyBase, ReviewBase
from scraper.glassdoor import scrape_data, Region, Url
from log.setup import logger, setup_logging

# Setup logging
setup_logging()


def main(db: Session) -> None:
    """
    Scrape Glassdoor reviews.

    Args:
        db (Session): The database session object

    Returns:
        None
    """

    def get_all_companies(db: Session) -> List[Tuple[int, str]]:
        """
        Get all companie id and names from the database.

        Args:
            db (Session): The database session object

        Returns:
            List[Tuple[int, str]]: A list of tuples containing company id and names
        """
        return db.query(Company.employer_name, Company.employer_id).all()

    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Get all companies from the database
    companies = get_all_companies(db)

    for employer_name, employer_id in companies:
        overview_data, reviews_data = loop.run_until_complete(
            scrape_data(
                Url.reviews(
                    employer_name,
                    employer_id,
                    regions=[Region.UNITED_STATES, Region.CANADA_ENGLISH],
                ),
                max_pages=1,
            )
        )

        # Validate the data with CompanyBase
        try:
            valid_data = CompanyBase(**overview_data)
        except ValidationError as e:
            logger.error(f"Invalid data for company {employer_name}: {e}")
            return  # Exit the function if the data is invalid

        # Fetch the existing company from the database
        company = (
            db.query(Company)
            .filter(Company.employer_id == valid_data.employer_id)
            .first()
        )

        # Update the company's fields with the new data
        for key, value in valid_data.model_dump().items():
            setattr(company, key, value)

        db.commit()

        # For each item in your scraped data...
        for review in reviews_data:
            # Validate the data with ReviewBase
            try:
                valid_review = ReviewBase(**review)
            except ValidationError as e:
                logger.error(f"Invalid data for review: {e}")
                continue  # Skip to the next review if the data is invalid

            # Create a new Review object with the validated data
            observation = Review(**valid_review.model_dump())
            # Add the new review to the session
            db.add(observation)

        # Commit the session to save the changes to the database
        db.commit()
