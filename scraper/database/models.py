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

    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, unique=True, index=True)
    employer_name = Column(String, index=True)
    gvkey = Column(Integer, unique=True, index=True)
    is_gvkey = Column(Boolean, index=True)
    url_old = Column(String, index=True)
    url_new = Column(String, index=True)
    ticker = Column(String, index=True)
    query = Column(String, index=True)

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

    __tablename__ = "review"

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

    company = relationship("Company", back_populates="reviews")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.review_text = f"{self.pros} {self.cons} {self.summary} {self.advice}"


# Listen for SQLAlchemy ORM events
@event.listens_for(Review, "before_insert")
@event.listens_for(Review, "before_update")

# Define a function to concatenate the review fields automatically
def concatenate_fields(mapper, connection, target):
    target.review_text = f"{target.pros} {target.cons} {target.summary} {target.advice}"
