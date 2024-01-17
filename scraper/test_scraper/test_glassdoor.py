from datetime import datetime
from typing import Dict
from unittest.mock import patch

from scraper.glassdoor import parse_reviews


def test_parse_reviews():
    result = {
        "ROOT_QUERY": {
            "employerReviewsRG1": {
                "__typename": "EmployerReviewsRG",
                "reviews": [
                    {
                        "reviewId": "1",
                        "employer": {"__ref": "employer:123"},
                        "reviewDateTime": "2022-01-01T12:00:00",
                        "ratingOverall": 4,
                        "ratingCeo": 5,
                        "ratingBusinessOutlook": 4,
                        "ratingWorkLifeBalance": 3,
                        "ratingCultureAndValues": 4,
                        "ratingDiversityAndInclusion": 3,
                        "ratingSeniorLeadership": 4,
                        "ratingRecommendToFriend": 5,
                        "ratingCareerOpportunities": 4,
                        "ratingCompensationAndBenefits": 4,
                        "isCurrentJob": True,
                        "lengthOfEmployment": "1-2 years",
                        "employmentStatus": "Full-time",
                        "jobEndingYear": None,
                        "jobTitle": {"text": "Software Engineer"},
                        "location": {"__ref": "City:456"},
                        "pros": "Good work environment",
                        "cons": "Long working hours",
                        "summary": "Great company to work for",
                        "advice": "Improve work-life balance",
                        "countHelpful": 10,
                        "countNotHelpful": 2,
                        "isCovid19": False,
                    }
                ],
            },
        },
        "City:456": {"name": "San Francisco"},
        "JobTitle:789": {"text": "Product Manager"},
    }

    expected_reviews = {
        "1": {
            "review_id": "1",
            "employer_id": 123,
            "date_time": datetime(2022, 1, 1, 12, 0, 0),
            "rating_overall": 4,
            "rating_ceo": 5,
            "rating_business_outlook": 4,
            "rating_work_life_balance": 3,
            "rating_culture_and_values": 4,
            "rating_diversity_and_inclusion": 3,
            "rating_senior_seadership": 4,
            "rating_recommend_to_friend": 5,
            "rating_career_opportunities": 4,
            "rating_compensation_and_benefits": 4,
            "is_current_job": True,
            "length_of_employment": "1-2 years",
            "employment_status": "Full-time",
            "job_ending_year": None,
            "job_title": "Software Engineer",
            "location": "San Francisco",
            "pros": "Good work environment",
            "cons": "Long working hours",
            "summary": "Great company to work for",
            "advice": "Improve work-life balance",
            "count_helpful": 10,
            "count_not_helpful": 2,
            "is_covid19": False,
        }
    }

    with patch("scraper.glassdoor.find_hidden_data") as mock_find_hidden_data:
        mock_find_hidden_data.return_value = result

        reviews = parse_reviews("dummy_html")

    assert reviews == expected_reviews
