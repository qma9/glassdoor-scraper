from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Float,
    event,
)
from sqlalchemy.orm import declarative_base, relationship

# Create the base class for the models
Base = declarative_base()


class Company(Base):
    """
    Represents a company in the database.

    Attributes:
        employer_id (int): The unique identifier of the employer.
        employer_name (str): The name of the employer.
        gvkey (int): The unique identifier of the company in the Global
            Company Key (GVKEY) system.
        is_gvkey (bool): Indicates whether the company has a GVKEY.
        url_old (str): The old URL of the company.
        url_new (str): The new URL of the company.
        ticker (str): The ticker symbol of the company.
        query (str): The query used to retrieve the company information.

        number_of_pages (int): The number of pages associated with the company.
        all_reviews_count (int): The total number of reviews for the company.
        rated_reviews_count (int): The number of rated reviews for the company.
        overall_rating (float): The overall rating of the company.
        ceo_name (str): The name of the CEO of the company.
        ceo_rating (float): The rating of the CEO of the company.

        recommend_to_friend_rating (float): The rating for recommending the
            company to a friend.
        culture_and_values_rating (float): The rating for the company's culture
            and values.
        diversity_and_inclusion_rating (float): The rating for diversity and
            inclusion in the company.
        career_opportunities_rating (float): The rating for career opportunities
            in the company.
        work_life_balance_rating (float): The rating for work-life balance in
            the company.
        senior_management_rating (float): The rating for senior management in
            the company.
        compensation_and_benefits_rating (float): The rating for compensation
            and benefits in the company.
        business_outlook_rating (float): The rating for the business outlook of
            the company.

        reviews (List[Review]): The reviews associated with the company.
    """

    __tablename__ = "company"

    employer_id = Column(Integer, primary_key=True, index=True)
    employer_name = Column(String, index=True)
    gvkey = Column(Integer, unique=True, index=True, nullable=True)
    is_gvkey = Column(Boolean, index=True)
    id_not_found = Column(Boolean, index=True)
    url_old = Column(String, index=True, nullable=True)
    url_new = Column(String, index=True, nullable=True)
    ticker = Column(String, index=True, nullable=True)
    query = Column(String, index=True, nullable=True)

    number_of_pages = Column(Integer, index=True)
    all_reviews_count = Column(Integer, index=True)
    rated_reviews_count = Column(Integer, index=True)
    overall_rating = Column(Float, index=True)
    ceo_name = Column(String, index=True)
    ceo_rating = Column(Float, index=True)

    recommend_to_friend_rating = Column(Float, index=True)
    culture_and_values_rating = Column(Float, index=True)
    diversity_and_inclusion_rating = Column(Float, index=True)
    career_opportunities_rating = Column(Float, index=True)
    work_life_balance_rating = Column(Float, index=True)
    senior_management_rating = Column(Float, index=True)
    compensation_and_benefits_rating = Column(Float, index=True)
    business_outlook_rating = Column(Float, index=True)

    reviews = relationship("Review", back_populates="company")


class Review(Base):
    """
    Represents a review of an employer.

    Attributes:
        id (int): The unique identifier of the review.
        review_id (int): The identifier of the review.
        employer_id (int): The identifier of the employer associated with the review.
        date_time (datetime): The date and time when the review was created.
        review_text (str): The text content of the review.
        rating_overall (int): The overall rating given by the reviewer.
        rating_ceo (str): The rating given to the CEO by the reviewer.
        rating_business_outlook (str): The rating given to the business outlook by the reviewer.
        rating_work_life_balance (int): The rating given to the work-life balance by the reviewer.
        rating_culture_and_values (int): The rating given to the culture and values by the reviewer.
        rating_diversity_and_inclusion (int): The rating given to the diversity and inclusion by the reviewer.
        rating_senior_leadership (int): The rating given to the senior leadership by the reviewer.
        rating_recommend_to_friend (str): The rating given to recommend the employer to a friend by the reviewer.
        rating_career_opportunities (int): The rating given to the career opportunities by the reviewer.
        rating_compensation_and_benefits (int): The rating given to the compensation and benefits by the reviewer.
        is_current_job (bool): Indicates if the review is for the current job of the reviewer.
        length_of_employment (int): The length of employment in months for the reviewer.
        employment_status (str): The employment status of the reviewer.
        job_ending_year (int): The year when the job ended for the reviewer.
        job_title (str): The job title of the reviewer.
        location (str): The location of the reviewer.
        pros (str): The pros mentioned in the review.
        cons (str): The cons mentioned in the review.
        summary (str): The summary of the review.
        advice (str): The advice given in the review.
        count_helpful (int): The count of helpful votes for the review.
        count_not_helpful (int): The count of not helpful votes for the review.
        is_covid19 (bool): Indicates if the review is related to COVID-19.
        company (Company): The company associated with the review.

    Methods:
        __init__(**kwargs): Initializes a new instance of the Review class.
    """
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, index=True) 
    review_id = Column(Integer, index=True)
    employer_id = Column(Integer, ForeignKey("company.employer_id"), index=True)
    date_time = Column(DateTime, index=True)
    
    review_text = Column(String, index=True)

    rating_overall = Column(Float, index=True, nullable=True)
    rating_ceo = Column(String, index=True, nullable=True)
    rating_business_outlook = Column(String, index=True, nullable=True)
    rating_work_life_balance = Column(Float, index=True, nullable=True)
    rating_culture_and_values = Column(Float, index=True, nullable=True)
    rating_diversity_and_inclusion = Column(Float, index=True, nullable=True)
    rating_senior_leadership = Column(Float, index=True, nullable=True)
    rating_recommend_to_friend = Column(String, index=True, nullable=True)
    rating_career_opportunities = Column(Float, index=True, nullable=True)
    rating_compensation_and_benefits = Column(Float, index=True, nullable=True)

    is_current_job = Column(Boolean, index=True, nullable=True)
    length_of_employment = Column(Float, index=True, nullable=True)
    employment_status = Column(String, index=True, nullable=True)
    job_ending_year = Column(Integer, index=True, nullable=True)
    job_title = Column(String, index=True, nullable=True)
    location = Column(String, index=True, nullable=True)

    pros = Column(String, index=True, nullable=True)
    cons = Column(String, index=True, nullable=True)
    summary = Column(String, index=True, nullable=True)
    advice = Column(String, index=True, nullable=True)

    count_helpful = Column(Integer, index=True, nullable=True)
    count_not_helpful = Column(Integer, index=True, nullable=True)
    is_covid19 = Column(Boolean, index=True, nullable=True)

    company = relationship("Company", back_populates="reviews")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.review_text = f"{self.pros} {self.cons} {self.summary} {self.advice}"


# Listen for SQLAlchemy ORM events
@event.listens_for(Review, "before_insert")
@event.listens_for(Review, "before_update")

# Define a function to concatenate the review fields automatically
def concatenate_fields(mapper, connection, target) -> None:
    """
    Concatenates the fields 'pros', 'cons', 'summary', and 'advice' of the target object
    and assigns the result to the 'review_text' attribute.

    Args:
        mapper: The mapper object.
        connection: The connection object.
        target: The target object.

    Returns:
        None
    """
    target.review_text = f"{target.pros} {target.cons} {target.summary} {target.advice}"
