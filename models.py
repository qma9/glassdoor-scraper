from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy import event

from database import Base


class Company(Base):
    """
    Represents company table in glassdoor database.

    Attributes:
        employer_id (int): A unique identifier for the company.
        employer_name (str): The name of the company.
        number_of_pages (int): The number of pages for the company's reviews.
        all_reviews_count (int): The total number of reviews for the company.
        rated_reviews_count (int): The number of rated reviews for the company.
        overall_rating (float): The overall rating for the company.
        ceo_name (str): The name of the CEO of the company.
        ceo_rating (float): The rating for the CEO.
        recommend_to_friend_rating (float): The rating for recommending the company to a friend.
        culture_and_values_rating (float): The rating for the company's culture and values.
        diversity_and_inclusion_rating (float): The rating for the company's diversity and inclusion.
        career_opportunities_rating (float): The rating for the company's career opportunities.
        work_life_balance_rating (float): The rating for the company's work-life balance.
        senior_management_rating (float): The rating for the company's senior management.
        compensation_and_benefits_rating (float): The rating for the company's compensation and benefits.
        business_outlook_rating (float): The rating for the company's business outlook.
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
    Represents review table in glassdoor database.

    Attributes:
        id (int): The unique identifier of the review.
        review_id (int): The identifier of the review.
        employer_id (int): The identifier of the employer associated with the review.
        date_time (datetime): The date and time when the review was created.
        review_text (str): The text of the review.
        rating_overall (int): The overall rating given by the reviewer.
        rating_ceo (str): The rating of the CEO given by the reviewer.
        rating_business_outlook (str): The rating of the business outlook given by the reviewer.
        rating_work_life_balance (int): The rating of work-life balance given by the reviewer.
        rating_culture_and_values (int): The rating of culture and values given by the reviewer.
        rating_diversity_and_inclusion (int): The rating of diversity and inclusion given by the reviewer.
        rating_senior_leadership (int): The rating of senior leadership given by the reviewer.
        rating_recommend_to_friend (str): The rating of recommendation to a friend given by the reviewer.
        rating_career_opportunities (int): The rating of career opportunities given by the reviewer.
        rating_compensation_and_benefits (int): The rating of compensation and benefits given by the reviewer.
        is_current_job (bool): Indicates if the review is for the current job of the reviewer.
        length_of_employment (int): The length of employment in months.
        employment_status (str): The employment status of the reviewer.
        job_ending_year (int): The year when the job ended.
        job_title (str): The title of the job.
        location (str): The location of the job.
        pros (str): The pros mentioned in the review.
        cons (str): The cons mentioned in the review.
        summary (str): The summary of the review.
        advice (str): The advice given in the review.
        count_helpful (int): The number of users who found the review helpful.
        count_not_helpful (int): The number of users who found the review not helpful.
        is_covid19 (bool): Indicates if the review is related to COVID-19.

    Methods:
        __init__(self, **kwargs): Initializes review_text field by concatenating the pros, cons, summary, and advice fields.
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.review_text = f"{self.pros} {self.cons} {self.summary} {self.advice}"


# Listen for SQLAlchemy ORM events
@event.listens_for(Review, "before_insert")
@event.listens_for(Review, "before_update")

# Define a function to concatenate the review fields automatically
def concatenate_fields(mapper, connection, target):
    target.review_text = f"{target.pros} {target.cons} {target.summary} {target.advice}"
