from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy import event

from database import Base


class Company(Base):
    """
    Represents the company table in glassdoor database.

    Attributes:
        id (Integer): The primary key for this table.
        employer_id (Integer): A unique identifier for the company.
        employer_name (String): The name of the company.
        all_reviews_count (Integer): The total number of reviews for the company.
        rated_reviews_count (Integer): The number of rated reviews for the company.
        overall_rating (Integer): The overall rating for the company.
        ceo_name (String): The name of the CEO of the company.
        ceo_rating (Integer): The rating for the CEO.
        recommend_to_friend_rating (Integer): The rating for recommending the company to a friend.
        culture_and_values_rating (Integer): The rating for the company's culture and values.
        diversity_and_inclusion_rating (Integer): The rating for the company's diversity and inclusion.
        career_opportunities_rating (Integer): The rating for the company's career opportunities.
        work_life_balance_rating (Integer): The rating for the company's work-life balance.
        senior_management_rating (Integer): The rating for the company's senior management.
        compensation_and_benefits_rating (Integer): The rating for the company's compensation and benefits.
        business_outlook_rating (Integer): The rating for the company's business outlook.
    """
    __tablename__ = "company"

    employer_id = Column(Integer, primary_key=True, index=True)
    employer_name = Column(String, index=True)

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


class Review(Base):
    """
    Represents the reviews table in glassdoor database.

    Attributes:
        id (Integer): The primary key for this table.
        review_id (Integer): A unique identifier for the review.
        date_time (DateTime): The date and time the review was posted.
        review_text (String): The text of the review.
        employer_id (Integer): The id of the company the review is for.
        rating_overall (Integer): The overall rating given in the review.
        rating_ceo (String): The rating for the CEO given in the review.
        rating_business_outlook (String): The business outlook rating given in the review.
        rating_work_life_balance (Integer): The work-life balance rating given in the review.
        rating_culture_and_values (Integer): The culture and values rating given in the review.
        rating_diversity_and_inclusion (Integer): The diversity and inclusion rating given in the review.
        rating_senior_leadership (Integer): The senior leadership rating given in the review.
        rating_recommend_to_friend (String): The recommend to friend rating given in the review.
        rating_career_opportunities (Integer): The career opportunities rating given in the review.
        rating_compensation_and_benefits (Integer): The compensation and benefits rating given in the review.
        is_current_job (Boolean): Whether the review is for a current job.
        length_of_employment (Integer): The length of employment in years.
        employment_status (String): The employment status of the reviewer.
        job_ending_year (Integer): The year the job ended.
        job_title (String): The title of the job the review is for.
        location (String): The location of the job the review is for.
        pros (String): The pros mentioned in the review.
        cons (String): The cons mentioned in the review.
        summary (String): The summary of the review.
        advice (String): Any advice given in the review.
        count_helpful (Integer): The number of helpful votes the review received.
        count_not_helpful (Integer): The number of not helpful votes the review received.
        is_covid19 (Boolean): Whether the review is related to COVID-19.
    """
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, index=True)
    employer_id = Column(Integer, ForeignKey("company.employer_id"), index=True)

    date_time = Column(DateTime, index=True)
    review_text = Column(String, index=True)
    
    rating_overall = Column(Integer, index=True, nullable=True)
    rating_ceo = Column(String, index=True, nullable=True)
    rating_business_outlook = Column(String, index=True, nullable=True)
    rating_work_life_balance = Column(Integer, index=True, nullable=True)
    rating_culture_and_values = Column(Integer, index=True, nullable=True)
    rating_diversity_and_inclusion = Column(Integer, index=True, nullable=True)
    rating_senior_leadership = Column(Integer, index=True, nullable=True)
    rating_recommend_to_friend = Column(String, index=True, nullable=True)
    rating_career_opportunities = Column(Integer, index=True, nullable=True)
    rating_compensation_and_benefits = Column(Integer, index=True, nullable=True)

    is_current_job = Column(Boolean, index=True, nullable=True)
    length_of_employment = Column(Integer, index=True, nullable=True)
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

    def __init__(self, review_id, **kwargs):
        super().__init__(**kwargs)
        self.review_id = review_id
        self.review_text = f"{self.pros} {self.cons} {self.summary} {self.advice}"

# Listen for SQLAlchemy ORM events
@event.listens_for(Review, 'before_insert')
@event.listens_for(Review, 'before_update')

# Define a function to concatenate the review fields automatically
def concatenate_fields(mapper, connection, target):
    target.review_text = f"{target.pros} {target.cons} {target.summary} {target.advice}"

