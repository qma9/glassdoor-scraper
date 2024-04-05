from pydantic import BaseModel

from typing import Optional
from datetime import datetime


class CompanyBase(BaseModel):
    """
    Represents the base model for a company.

    Attributes:
        employer_id (int): The ID of the employer.
        employer_name (str): The name of the employer.
        number_of_pages (Optional[int]): The number of pages.

        all_reviews_count (Optional[int]): The count of all reviews.
        rated_reviews_count (Optional[int]): The count of rated reviews.
        overall_rating (Optional[float]): The overall rating.
        ceo_name (Optional[str]): The name of the CEO.
        ceo_rating (Optional[float]): The rating of the CEO.

        recommend_to_friend_rating (Optional[float]): The rating for recommending to a friend.
        culture_and_values_rating (Optional[float]): The rating for culture and values.
        diversity_and_inclusion_rating (Optional[float]): The rating for diversity and inclusion.
        career_opportunities_rating (Optional[float]): The rating for career opportunities.
        work_life_balance_rating (Optional[float]): The rating for work-life balance.
        senior_management_rating (Optional[float]): The rating for senior management.
        compensation_and_benefits_rating (Optional[float]): The rating for compensation and benefits.
        business_outlook_rating (Optional[float]): The rating for business outlook.
    """

    # id: Optional[int] = None  # not required for new instances of CompanyBase
    employer_id: int
    employer_name: Optional[str] = ""
    gvkey: Optional[int] = None
    is_gvkey: Optional[bool] = False
    id_not_found: Optional[bool] = False
    url_old: Optional[str] = ""
    url_new: Optional[str] = ""
    ticker: Optional[str] = ""
    query: Optional[str] = ""

    number_of_pages: Optional[int] = None
    all_reviews_count: Optional[int] = None
    rated_reviews_count: Optional[int] = None
    overall_rating: Optional[float] = None
    ceo_name: Optional[str] = ""
    ceo_rating: Optional[float] = None

    recommend_to_friend_rating: Optional[float] = None
    culture_and_values_rating: Optional[float] = None
    diversity_and_inclusion_rating: Optional[float] = None
    career_opportunities_rating: Optional[float] = None
    work_life_balance_rating: Optional[float] = None
    senior_management_rating: Optional[float] = None
    compensation_and_benefits_rating: Optional[float] = None
    business_outlook_rating: Optional[float] = None


class ReviewBase(BaseModel):
    """
    Represents the base model for a review.

    Attributes:
        id (int): The ID of the review.
        review_id (int): The ID of the review.
        date_time (datetime): The date and time of the review.
        employer_id (int): The ID of the employer.

        rating_overall (Optional[int]): The overall rating of the review.
        rating_ceo (Optional[str]): The rating of the CEO.
        rating_business_outlook (Optional[str]): The rating of the business outlook.
        rating_work_life_balance (Optional[int]): The rating of the work-life balance.
        rating_culture_and_values (Optional[int]): The rating of the culture and values.
        rating_diversity_and_inclusion (Optional[int]): The rating of the diversity and inclusion.
        rating_senior_leadership (Optional[int]): The rating of the senior leadership.
        rating_recommend_to_friend (Optional[str]): The rating of the recommendation to a friend.
        rating_career_opportunities (Optional[int]): The rating of the career opportunities.
        rating_compensation_and_benefits (Optional[int]): The rating of the compensation and benefits.

        is_current_job (Optional[bool]): Indicates if the review is for the current job.
        length_of_employment (Optional[int]): The length of employment.
        employment_status (Optional[str]): The employment status.
        job_ending_year (Optional[int]): The year the job ended.
        job_title (Optional[str]): The job title.
        location (Optional[str]): The location.

        pros (Optional[str]): The pros of the review.
        cons (Optional[str]): The cons of the review.
        summary (Optional[str]): The summary of the review.
        advice (Optional[str]): The advice of the review.

        count_helpful (Optional[int]): The count of helpful votes.
        count_not_helpful (Optional[int]): The count of not helpful votes.
        is_covid19 (Optional[bool]): Indicates if the review is related to COVID-19.

    Properties:
        review_text (str): Returns the concatenated text of pros, cons, summary, and advice.
    """

    id: Optional[int] = None  # not required for new instances of ReviewBase
    review_id: int 
    employer_id: Optional[int] = None
    date_time: datetime

    rating_overall: Optional[float] = None
    rating_ceo: Optional[str] = ""
    rating_business_outlook: Optional[str] = ""
    rating_work_life_balance: Optional[float] = None
    rating_culture_and_values: Optional[float] = None
    rating_diversity_and_inclusion: Optional[float] = None
    rating_senior_leadership: Optional[float] = None
    rating_recommend_to_friend: Optional[str] = ""
    rating_career_opportunities: Optional[float] = None
    rating_compensation_and_benefits: Optional[float] = None

    is_current_job: Optional[bool] = None
    length_of_employment: Optional[float] = None
    employment_status: Optional[str] = ""
    job_ending_year: Optional[int] = None
    job_title: Optional[str] = ""
    location: Optional[str] = ""

    pros: Optional[str] = ""
    cons: Optional[str] = ""
    summary: Optional[str] = ""
    advice: Optional[str] = ""

    count_helpful: Optional[int] = None
    count_not_helpful: Optional[int] = None
    is_covid19: Optional[bool] = None

    @property
    def review_text(self) -> str:
        return f"{self.pros} {self.cons} {self.summary} {self.advice}"
