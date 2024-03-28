from scraper.database.models import Review


def test_review_init():
    review_id = 1
    pros = "Good work environment"
    cons = "Long working hours"
    summary = "Overall satisfied"
    advice = "Improve work-life balance"

    review = Review(review_id, pros=pros, cons=cons, summary=summary, advice=advice)

    assert review.review_id == review_id
    assert review.pros == pros
    assert review.cons == cons
    assert review.summary == summary
    assert review.advice == advice
    assert review.review_text == f"{pros} {cons} {summary} {advice}"


def test_review_attributes():
    review = Review(review_id=1)

    assert hasattr(review, "id")
    assert hasattr(review, "date_time")
    assert hasattr(review, "employer_id")
    assert hasattr(review, "rating_overall")
    assert hasattr(review, "rating_ceo")
    assert hasattr(review, "rating_business_outlook")
    assert hasattr(review, "rating_work_life_balance")
    assert hasattr(review, "rating_culture_and_values")
    assert hasattr(review, "rating_diversity_and_inclusion")
    assert hasattr(review, "rating_senior_leadership")
    assert hasattr(review, "rating_recommend_to_friend")
    assert hasattr(review, "rating_career_opportunities")
    assert hasattr(review, "rating_compensation_and_benefits")
    assert hasattr(review, "is_current_job")
    assert hasattr(review, "length_of_employment")
    assert hasattr(review, "employment_status")
    assert hasattr(review, "job_ending_year")
    assert hasattr(review, "job_title")
    assert hasattr(review, "location")
    assert hasattr(review, "pros")
    assert hasattr(review, "cons")
    assert hasattr(review, "summary")
    assert hasattr(review, "advice")
    assert hasattr(review, "count_helpful")
    assert hasattr(review, "count_not_helpful")
    assert hasattr(review, "is_covid19")
