from bs4 import BeautifulSoup
import requests
from graphql import parse, print_ast
import simplejson as json

from typing import Optional, Dict, Tuple, List
from datetime import datetime
from enum import Enum

# import json
import re
import asyncio
from dotenv import load_dotenv
import sys
import os
import re

# Load .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from log.setup import logger, setup_logging

# Configure logging
setup_logging()


def get_apollostate(url: str) -> dict:

    # OxyLabs proxy crendetials
    cred = {
        "username": os.getenv("OXY_USERNAME"),
        "password": os.getenv("OXY_PASSWORD"),
    }

    # Structure payload.
    payload = {
        "source": "universal",
        "url": url,
    }

    # Get response.
    response = requests.request(
        "POST",
        "https://realtime.oxylabs.io/v1/queries",
        auth=(cred["username"], cred["password"]),
        json=payload,
    )

    # Load the JSON string into dictionary
    app_cache_json = json.loads(response.text)

    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(app_cache_json["results"][0]["content"], "html.parser")

    # Find script tag that contains the apolloState object, should only be 1
    script_tags = str(soup.find_all("script", string=re.compile("apolloState")))

    # Extract the apolloState object from the script tag
    match = re.search('apolloState":({.*?})};</script>', script_tags, re.DOTALL)
    apollostate = match.group(1)

    # Find all GraphQL queries in the JSON string
    graphql_queries = re.findall(r'"[^"]*\({[^)]*}\)"', apollostate)

    # Replace each GraphQL query with its string representation
    query_to_string = {}

    for query in graphql_queries:
        # Extract the actual GraphQL query from the string
        actual_query = re.search(r'(?<=")[^"]*(?=")', query).group()

        # Extract the operation name from the actual query
        operation_name = actual_query.split("(")[0].strip()

        # Prepend the operation type and the operation name to the GraphQL operation
        # Add a selection set for the operation
        actual_query = f"query {{ {operation_name} {{ id }} }}"

        # Parse the query into an AST
        ast = parse(actual_query)

        # Convert the AST back into a string
        string = print_ast(ast)

        # Remove the {}, \t, \n, \r, and space characters from the string
        # Add the query and its string representation to the mapping
        query_to_string[query] = (
            string.replace("{", "")
            .replace("}", "")
            .replace("\t", "")
            .replace("\n", "")
            .replace("\r", "")
            .replace(" ", "")
            .strip()
        )

    # Replace each GraphQL query with its string representation in the JSON string
    for query, string in query_to_string.items():
        # Enclose the string representation in double quotes to make it a valid JSON key
        apollostate = apollostate.replace(query, f'"{string}"')

    # Load the JSON string into a Python dictionary
    # This will automatically remove duplicate keys
    data = json.loads(apollostate)

    # Convert the dictionary back into a JSON string
    # This will create a new JSON object without duplicate keys
    apollostate = json.dumps(data)

    # Now can parse the JSON string without duplicate error
    data = json.loads(apollostate)

    return data


def parse_overview(apollo_state: str) -> Dict[str, str | int]:
    """
    Parse overview from Glassdoor page HTML.

    Args:
        result (str): The HTML content of the Glassdoor page.

    Returns:
        Dict[str, str | int]: A dictionary containing the parsed overview data.

    """
    overview_data = {}
    cache = apollo_state  # find_hidden_data(result)
    if not cache:
        logger.error(f"No hidden data found in Glassdoor page html")
    else:
        try:
            root_query = cache["ROOT_QUERY"]
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
        except KeyError:
            logger.error(f"ROOT_QUERY key not found in cache")

    try:
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
            "ceo_name": (
                overview_data["ratings"]["ratedCeo"]["name"]
                if overview_data["ratings"]["ratedCeo"] is not None
                and "name" in overview_data["ratings"]["ratedCeo"]
                else None
            ),
            "ceo_rating": overview_data["ratings"]["ceoRating"],
            "recommend_to_friend_rating": overview_data["ratings"][
                "recommendToFriendRating"
            ],
            "culture_and_values_rating": overview_data["ratings"][
                "cultureAndValuesRating"
            ],
            "diversity_and_inclusion_rating": overview_data["ratings"][
                "diversityAndInclusionRating"
            ],
            "career_opportunities_rating": overview_data["ratings"][
                "careerOpportunitiesRating"
            ],
            "work_life_balance_rating": overview_data["ratings"][
                "workLifeBalanceRating"
            ],
            "senior_management_rating": overview_data["ratings"][
                "seniorManagementRating"
            ],
            "compensation_and_benefits_rating": overview_data["ratings"][
                "compensationAndBenefitsRating"
            ],
            "business_outlook_rating": overview_data["ratings"][
                "businessOutlookRating"
            ],
        }

    except KeyError as e:
        logger.error(f"Key {e} not found in overview_data")
        raise

    return overview


def parse_reviews(apollo_state: str) -> Dict[str, Dict[str, str | int]]:
    """
    Parse data from Glassdoor page HTML.

    Args:
        result (str): The HTML content of the Glassdoor page.

    Returns:
        Dict[str, Dict[str, str | int]]: A dictionary containing parsed review data.
            The keys are review IDs and the values are dictionaries containing
            various attributes of the review, such as review ID, employer ID,
            date and time, ratings, job details, location, pros and cons, etc.
    """
    cache = apollo_state  # find_hidden_data(result)
    if not cache:
        logger.error(f"No hidden data found in Glassdoor page html")
    else:
        try:
            root_query = cache["ROOT_QUERY"]
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
        except KeyError:
            logger.error(f"ROOT_QUERY key not found in cache")

    try:
        # Extract city and job title names
        city_job_title = {
            key: value
            for key, value in cache.items()
            if key.startswith(("City", "JobTitle"))
        }
    except KeyError as e:
        logger.error(f"Key {e} not found in cache")

    try:
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
                "rating_ceo": (
                    review["ratingCeo"] if review["ratingCeo"] is not None else None
                ),
                "rating_business_outlook": review["ratingBusinessOutlook"],
                "rating_work_life_balance": review["ratingWorkLifeBalance"],
                "rating_culture_and_values": review["ratingCultureAndValues"],
                "rating_diversity_and_inclusion": review["ratingDiversityAndInclusion"],
                "rating_senior_seadership": review["ratingSeniorLeadership"],
                "rating_recommend_to_friend": review["ratingRecommendToFriend"],
                "rating_career_opportunities": review["ratingCareerOpportunities"],
                "rating_compensation_and_benefits": review[
                    "ratingCompensationAndBenefits"
                ],
                "is_current_job": bool(review["isCurrentJob"]),
                "length_of_employment": review["lengthOfEmployment"],
                "employment_status": review["employmentStatus"],
                "job_ending_year": (
                    review["jobEndingYear"]
                    if review["jobEndingYear"] is not None
                    else None
                ),
                "job_title": (
                    review["jobTitle"]["text"]
                    if review["jobTitle"] is not None and "text" in review["jobTitle"]
                    else (
                        review["jobTitle"]["__ref"]
                        if review["jobTitle"] is not None
                        and "__ref" in review["jobTitle"]
                        else None
                    )
                ),
                "location": (
                    review["location"]["__ref"]
                    if review["location"] is not None
                    else None
                ),
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
                extracted_review["location"] = city_job_title[
                    extracted_review["location"]
                ]["name"]

            # Add review to reviews
            reviews[review["reviewId"]] = extracted_review

    except KeyError as e:
        logger.error(f"Key {e} not found in review", extra={"review": review})
        raise

    return reviews


async def scrape_data(
    url: str, max_pages: Optional[int] = None
) -> Tuple[Dict[str, int | float], Dict[str, Dict[str, str | int]]] | None:
    """Scrape Glassdoor reviews listings from reviews pages (with pagination).

    Args:
        url (str): The URL of the reviews page to scrape.
        max_pages (Optional[int], optional): The maximum number of pages to scrape. Defaults to None.

    Returns:
        Tuple[Dict[str, int | float], Dict[str, Dict[str, str | int]]]: A tuple containing the overview information and the scraped reviews.

    """
    logger.info("scraping reviews from %s", url)

    # Extract the apolloState property from the window.appCache object
    apollo_state = get_apollostate(url)

    if not apollo_state:
        logger.error("window.appCache.apolloState is not present in the script tag")
        return None

    overview = parse_overview(apollo_state)
    reviews = parse_reviews(apollo_state)

    total_pages = overview["number_of_pages"]

    if max_pages and max_pages < total_pages:
        total_pages = max_pages

    logger.info(
        "scraped first page of reviews of %s, scraping remaining %d pages",
        url,
        total_pages - 1,
    )

    for page_num in range(2, total_pages + 1):
        page_url = Url.change_page(url, page=page_num)

        # Check if the window.appCache object is present in the script
        apollo_state = get_apollostate(page_url)

        if not apollo_state:
            logger.error(
                "window.appCache is not present in the script tag on page %d",
                page_num,
            )
            continue  # Skip this page and move on to the next one

        if apollo_state:  # Check if the page was successfully scraped
            new_reviews = parse_reviews(apollo_state)
            reviews.update(new_reviews)
        else:
            logger.error("failed to scrape %s", page_url)

        # Add a delay
        await asyncio.sleep(1)

    logger.info(
        "scraped %d reviews from %s in %d pages", len(reviews), url, total_pages
    )

    return overview, reviews


class Region(Enum):
    """
    Glassdoor region ids.
    """

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
    Helper URL generator for Glassdoor pages from given employer name and id.

    For example:
    GlassdoorUrl.overview("NVIDIA", "7633")
    https://www.glassdoor.com/Overview/Working-at-NVIDIA-EI_IE7633.11,17.htm

    Glassdoor allows any prefix for employer name and to indicate the prefix suffix numbers are used like:
    https://www.glassdoor.com/Overview/Working-at-NVIDIA-EI_IE7633.11,17.htm
    11,17 is the slice where employer name is
    """

    @staticmethod
    def overview(
        employer: str, employer_id: str, region: Optional[Region] = None
    ) -> str:
        """
        Generate the URL for the overview page of a specific employer on Glassdoor.

        Args:
            employer (str): The name of the employer.
            employer_id (str): The ID of the employer.
            region (Optional[Region], optional): The region to filter the results by. Defaults to None.

        Returns:
            str: The generated URL.

        """
        employer = employer.replace(" ", "-")
        url = f"https://www.glassdoor.com/Overview/Working-at-{employer}-EI_IE{employer_id}"
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
        """
        Generate the URL for the reviews page of a specific employer on Glassdoor.

        Args:
            employer (str): The name of the employer.
            employer_id (str): The ID of the employer.
            regions (Optional[List[Region]], optional): The regions to filter the results by. Defaults to None.

        Returns:
            str: The generated URL.

        """
        employer = employer.replace(" ", "-")
        url = (
            f"https://www.glassdoor.com/Reviews/{employer}-Reviews-E{employer_id}.htm?"
        )
        if regions:
            url += "&".join(f"filter.countryId={region.value}" for region in regions)
        return url

    @staticmethod
    def change_page(url: str, page: int) -> str:
        """
        Update the page number in a Glassdoor URL.

        Args:
            url (str): The original URL.
            page (int): The new page number.

        Returns:
            str: The updated URL.

        """
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
                "NVIDIA", "7633", regions=[Region.UNITED_STATES, Region.CANADA_ENGLISH]
            ),
            max_pages=1,
        )
    )
    print("\n\n")
    print("Overview:", overview)
    print("\n\n")
    print("Reviews:", reviews)
