from datetime import datetime

from base_models import ReviewBase


def test_review_base_init():
    review_id = 1
    pros = "Good work environment"
    cons = "Long working hours"
    summary = "Overall satisfied"
    advice = "Improve work-life balance"

    review = ReviewBase(
        id=1,
        review_id=review_id,
        date_time=datetime.now(),
        employer_id=1,
        rating_overall=4,
        rating_ceo="Good",
        rating_business_outlook="Positive",
        rating_work_life_balance=3,
        rating_culture_and_values=4,
        rating_diversity_and_inclusion=4,
        rating_senior_leadership=3,
        rating_recommend_to_friend="Yes",
        rating_career_opportunities=4,
        rating_compensation_and_benefits=3,
        is_current_job=True,
        length_of_employment=2,
        employment_status="Full-time",
        job_ending_year=2022,
        job_title="Software Engineer",
        location="San Francisco",
        pros=pros,
        cons=cons,
        summary=summary,
        advice=advice,
        count_helpful=10,
        count_not_helpful=2,
        is_covid19=False,
    )

    assert review.id == 1
    assert review.review_id == review_id
    assert isinstance(review.date_time, datetime)
    assert review.employer_id == 1
    assert review.rating_overall == 4
    assert review.rating_ceo == "Good"
    assert review.rating_business_outlook == "Positive"
    assert review.rating_work_life_balance == 3
    assert review.rating_culture_and_values == 4
    assert review.rating_diversity_and_inclusion == 4
    assert review.rating_senior_leadership == 3
    assert review.rating_recommend_to_friend == "Yes"
    assert review.rating_career_opportunities == 4
    assert review.rating_compensation_and_benefits == 3
    assert review.is_current_job is True
    assert review.length_of_employment == 2
    assert review.employment_status == "Full-time"
    assert review.job_ending_year == 2022
    assert review.job_title == "Software Engineer"
    assert review.location == "San Francisco"
    assert review.pros == pros
    assert review.cons == cons
    assert review.summary == summary
    assert review.advice == advice
    assert review.count_helpful == 10
    assert review.count_not_helpful == 2
    assert review.is_covid19 is False


def test_review_base_review_text():
    review = ReviewBase(
        id=1,
        review_id=1,
        date_time=datetime.now(),
        employer_id=1,
        pros="Good work environment",
        cons="Long working hours",
        summary="Overall satisfied",
        advice="Improve work-life balance",
    )

    assert (
        review.review_text
        == "Good work environment Long working hours Overall satisfied Improve work-life balance"
    )
