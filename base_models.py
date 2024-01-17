from pydantic import BaseModel

from typing import Optional
from datetime import datetime

class CompanyBase(BaseModel):
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