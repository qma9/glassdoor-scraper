from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import requests

from typing import Optional, Dict, Tuple, List
from datetime import datetime
from enum import Enum
import json
import re
import asyncio
import logging
from dotenv import load_dotenv
import sys
import os

# Load .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from utils import configure_logging

# Configure logging
configure_logging()

# Bright Data headless browser authentication credentials
cred = {
    "host": os.getenv("HOST"),
    "username": os.getenv("USERNAME"),
    "password": os.getenv("PASSWORD"),
}
auth = f'{cred["username"]}:{cred["password"]}'
browser_url = f'wss://{auth}@{cred["host"]}'


def find_hidden_data(result: str) -> dict:
    """
    Extract hidden web cache (Apollo Graphql framework) from Glassdoor page HTML
    It's either in NEXT_DATA script or direct apolloState js variable
    """
    # Create a BeautifulSoup object from the response text
    soup = BeautifulSoup(result, "html.parser")

    # data can be in __NEXT_DATA__ cache
    data = soup.select_one("script#__NEXT_DATA__")
    if data:
        data = json.loads(data.string)["props"]["pageProps"]["apolloCache"]
    else:  # or in direct apolloState cache
        matches = re.findall(r'apolloState":\s*({.+})};', result)
        if matches:
            data = json.loads(matches[0])
        else:  # or in gd-reviews.bundle.3d5cc.js file
            script_tag = soup.find(
                "script", attrs={"src": re.compile(r"gd-reviews\.bundle\.3d5cc\.js$")}
            )
            if script_tag:
                # Fetch the gd-reviews.bundle.3d5cc.js file
                response = requests.get(script_tag["src"])

                # Extract the apolloState data from the file
                matches = re.findall(r'apolloState":\s*({.+})};', response.text)
                if matches:
                    data = json.loads(matches[0])
                else:
                    data = {}  # or some other default value
            else:
                data = {}  # or some other default value

    return data


def parse_overview(result: str) -> Dict[str, str | int]:
    """
    Parse overview from Glassdoor page HTML
    """
    cache = find_hidden_data(result)
    root_query = cache.get("ROOT_QUERY", {})
    overview_data = next(
        (
            value
            for key, value in root_query.items()
            if key.startswith("employerReviewsRG")
            and isinstance(value, dict)
            and value.get("__typename") == "EmployerReviewsRG"
        ),
        {},
    )

    # Extract company overview information
    overview = {
        "employer_id": int(
            overview_data["employer"]["__ref"].split(":")[1]
            if "employer" in overview_data
            else None
        ),  # comment out later once all companies are retrieved
        # "employer_name": overview_data["employer"]["name"],
        "number_of_pages": overview_data["numberOfPages"],
        "all_reviews_count": overview_data["allReviewsCount"],
        "rated_reviews_count": overview_data["ratedReviewsCount"],
        "overall_rating": overview_data["ratings"]["overallRating"],
        "ceo_name": overview_data["ratings"]["ratedCeo"]["name"]
        if overview_data["ratings"]["ratedCeo"] is not None
        else None,
        "ceo_rating": overview_data["ratings"]["ceoRating"],
        "recommend_to_friend_rating": overview_data["ratings"][
            "recommendToFriendRating"
        ],
        "culture_and_values_rating": overview_data["ratings"]["cultureAndValuesRating"],
        "diversity_and_inclusion_rating": overview_data["ratings"][
            "diversityAndInclusionRating"
        ],
        "career_opportunities_rating": overview_data["ratings"][
            "careerOpportunitiesRating"
        ],
        "work_life_balance_rating": overview_data["ratings"]["workLifeBalanceRating"],
        "senior_management_rating": overview_data["ratings"]["seniorManagementRating"],
        "compensation_and_benefits_rating": overview_data["ratings"][
            "compensationAndBenefitsRating"
        ],
        "business_outlook_rating": overview_data["ratings"]["businessOutlookRating"],
    }

    return overview


def parse_reviews(result: str) -> Dict[str, Dict[str, str | int]]:
    """
    Parse data from Glassdoor page HTML
    """
    cache = find_hidden_data(result)
    root_query = cache.get("ROOT_QUERY", {})
    reviews_data = next(
        (
            value["reviews"]
            for key, value in root_query.items()
            if key.startswith("employerReviewsRG")
            and isinstance(value, dict)
            and value.get("__typename") == "EmployerReviewsRG"
            and "reviews" in value
        ),
        [],
    )

    # Extract city and job title names
    city_job_title = {
        key: value
        for key, value in cache.items()
        if key.startswith(("City", "JobTitle"))
    }

    # Extract reviews
    reviews = {}

    for review in reviews_data:
        extracted_review = {
            "review_id": review["reviewId"],
            "employer_id": int(review["employer"]["__ref"].split(":")[1]),
            "date_time": datetime.fromisoformat(
                review["reviewDateTime"].replace("T", " ")
            ),
            "rating_overall": review["ratingOverall"],
            "rating_ceo": review["ratingCeo"]
            if review["ratingCeo"] is not None
            else None,
            "rating_business_outlook": review["ratingBusinessOutlook"],
            "rating_work_life_balance": review["ratingWorkLifeBalance"],
            "rating_culture_and_values": review["ratingCultureAndValues"],
            "rating_diversity_and_inclusion": review["ratingDiversityAndInclusion"],
            "rating_senior_seadership": review["ratingSeniorLeadership"],
            "rating_recommend_to_friend": review["ratingRecommendToFriend"],
            "rating_career_opportunities": review["ratingCareerOpportunities"],
            "rating_compensation_and_benefits": review["ratingCompensationAndBenefits"],
            "is_current_job": bool(review["isCurrentJob"]),
            "length_of_employment": review["lengthOfEmployment"],
            "employment_status": review["employmentStatus"],
            "job_ending_year": review["jobEndingYear"]
            if review["jobEndingYear"] is not None
            else None,
            "job_title": review["jobTitle"]["text"]
            if review["jobTitle"] is not None and "text" in review["jobTitle"]
            else review["jobTitle"]["__ref"]
            if review["jobTitle"] is not None and "__ref" in review["jobTitle"]
            else None,
            "location": review["location"]["__ref"]
            if review["location"] is not None
            else None,
            "pros": review["pros"],
            "cons": review["cons"],
            "summary": review["summary"],
            "advice": review["advice"],
            "count_helpful": review["countHelpful"],
            "count_not_helpful": review["countNotHelpful"],
            "is_covid19": bool(review["isCovid19"]),
        }

        # Add job title
        if extracted_review["job_title"] in city_job_title:
            extracted_review["job_title"] = city_job_title[
                extracted_review["job_title"]
            ]["text"]

        # Add city name
        if extracted_review["location"] in city_job_title:
            extracted_review["location"] = city_job_title[extracted_review["location"]][
                "name"
            ]

        # Add review to reviews
        reviews[review["reviewId"]] = extracted_review

    return reviews


async def scrape_data(
    url: str, max_pages: Optional[int] = None
) -> Tuple[Dict[str, int | float], Dict[str, Dict[str, str | int]]]:
    """Scrape Glassdoor reviews listings from reviews page (with pagination)"""
    logging.info("scraping reviews from %s", url)

    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(browser_url)
        page = await browser.new_page()

        # Only allow document requests
        await page.route(
            "**/*",
            lambda route, request: route.continue_()
            if request.resource_type == "document"
            else route.abort(),
        )

        # Navigate to the first page
        await page.goto(url, timeout=120000)
        first_page = await page.content()

        overview = parse_overview(first_page)
        reviews = parse_reviews(first_page)
        total_pages = overview["number_of_pages"]

        if max_pages and max_pages < total_pages:
            total_pages = max_pages

        logging.info(
            "scraped first page of reviews of %s, scraping remaining %d pages",
            url,
            total_pages - 1,
        )

        for page_num in range(2, total_pages + 1):
            page_url = Url.change_page(url, page=page_num)
            await page.goto(page_url, timeout=120000)
            result = await page.content()

            if result:  # Check if the page was successfully scraped
                new_reviews = parse_reviews(result)
                reviews.update(new_reviews)
            else:
                logging.error("failed to scrape %s", page_url)

            # Add a delay
            await asyncio.sleep(1)

        logging.info(
            "scraped %d reviews from %s in %d pages", len(reviews), url, total_pages
        )

    return overview, reviews


class Region(Enum):
    """glassdoor.com region codes"""

    UNITED_STATES = "1"
    UNITED_KINGDOM = "2"
    CANADA_ENGLISH = "3"
    INDIA = "4"
    AUSTRALIA = "5"
    FRANCE = "6"
    GERMANY = "7"
    SPAIN = "8"
    BRAZIL = "9"
    NETHERLANDS = "10"
    AUSTRIA = "11"
    MEXICO = "12"
    ARGENTINA = "13"
    BELGIUM_NEDERLANDS = "14"
    BELGIUM_FRENCH = "15"
    SWITZERLAND_GERMAN = "16"
    SWITZERLAND_FRENCH = "17"
    IRELAND = "18"
    CANADA_FRENCH = "19"
    HONG_KONG = "20"
    NEW_ZEALAND = "21"
    SINGAPORE = "22"
    ITALY = "23"


class Url:
    """
    Helper URL generator that generates full URLs for glassdoor.com pages
    from given employer name and ID
    For example:
    > GlassdoorUrl.overview("eBay Motors Group", "4189745")
    https://www.glassdoor.com/Overview/Working-at-eBay-Motors-Group-EI_IE4189745.11,28.htm

    Note that URL formatting is important when it comes to scraping Glassdoor
    as unusual URL formats can lead to scraper blocking.
    """

    @staticmethod
    def overview(
        employer: str, employer_id: str, region: Optional[Region] = None
    ) -> str:
        employer = employer.replace(" ", "-")
        url = f"https://www.glassdoor.com/Overview/Working-at-{employer}-EI_IE{employer_id}"
        # glassdoor is allowing any prefix for employer name and
        # to indicate the prefix suffix numbers are used like:
        # https://www.glassdoor.com/Overview/Working-at-eBay-Motors-Group-EI_IE4189745.11,28.htm
        # 11,28 is the slice where employer name is
        _start = url.split("/Overview/")[1].find(employer)
        _end = _start + len(employer)
        url += f".{_start},{_end}.htm"
        if region:
            return url + f"?filter.countryId={region.value}"
        return url

    @staticmethod
    def reviews(
        employer: str, employer_id: str, regions: Optional[List[Region]] = None
    ) -> str:
        employer = employer.replace(" ", "-")
        url = (
            f"https://www.glassdoor.com/Reviews/{employer}-Reviews-E{employer_id}.htm?"
        )
        if regions:
            url += "&".join(f"filter.countryId={region.value}" for region in regions)
        return url

    @staticmethod
    def change_page(url: str, page: int) -> str:
        """update page number in a glassdoor url"""
        if re.search(r"_P\d+\.htm", url):
            new = re.sub(r"(?:_P\d+)*.htm", f"_P{page}.htm", url)
        else:
            new = re.sub(".htm", f"_P{page}.htm", url)
        assert new != url
        return new


if __name__ == "__main__":
    # test script
    overview, reviews = asyncio.run(
        scrape_data(
            Url.reviews(
                "eBay Motors Group",
                "4189745",
                regions=[Region.UNITED_STATES, Region.CANADA_ENGLISH],
            ),
            max_pages=1,
        )
    )
    print("Overview:", overview)
    print("\n\n")
    print("Reviews:", reviews)
