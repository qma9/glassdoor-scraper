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

    employer_id: int
    employer_name: str
    number_of_pages: Optional[int]

    all_reviews_count: Optional[int]
    rated_reviews_count: Optional[int]
    overall_rating: Optional[float]
    ceo_name: Optional[str]
    ceo_rating: Optional[float]

    recommend_to_friend_rating: Optional[float]
    culture_and_values_rating: Optional[float]
    diversity_and_inclusion_rating: Optional[float]
    career_opportunities_rating: Optional[float]
    work_life_balance_rating: Optional[float]
    senior_management_rating: Optional[float]
    compensation_and_benefits_rating: Optional[float]
    business_outlook_rating: Optional[float]


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

    id: int
    review_id: int
    date_time: datetime
    employer_id: int

    rating_overall: Optional[int]
    rating_ceo: Optional[str]
    rating_business_outlook: Optional[str]
    rating_work_life_balance: Optional[int]
    rating_culture_and_values: Optional[int]
    rating_diversity_and_inclusion: Optional[int]
    rating_senior_leadership: Optional[int]
    rating_recommend_to_friend: Optional[str]
    rating_career_opportunities: Optional[int]
    rating_compensation_and_benefits: Optional[int]

    is_current_job: Optional[bool]
    length_of_employment: Optional[int]
    employment_status: Optional[str]
    job_ending_year: Optional[int]
    job_title: Optional[str]
    location: Optional[str]

    pros: Optional[str]
    cons: Optional[str]
    summary: Optional[str]
    advice: Optional[str]

    count_helpful: Optional[int]
    count_not_helpful: Optional[int]
    is_covid19: Optional[bool]

    @property
    def review_text(self) -> str:
        return f"{self.pros} {self.cons} {self.summary} {self.advice}"
