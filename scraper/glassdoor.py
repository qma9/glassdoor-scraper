from graphql import parse, print_ast
from bs4 import BeautifulSoup
import requests
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
listener = setup_logging()


def get_apollocache(url: str) -> dict:

    cred = {
        "username": os.getenv("SMART_USERNAME"),
        "password": os.getenv("SMART_PASSWORD"),
    }

    proxies = {
        "http": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
        "https": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
    }

    # headers = {"X-SU-Geo": "United States"}

    response = requests.request("GET", url, verify=False, proxies=proxies)

    # TESTING
    print(f"\nURL: {url}\n")

    # TESTING
    with open("scraper/structure/zen_response.txt", "w") as f:
        f.write(response.text)

    # Load the JSON string into dictionary
    # app_cache_json = json.loads(response.text)

    # Parse the HTML with BeautifulSoup
    # soup = BeautifulSoup(app_cache_json["results"][0]["content"], "html.parser")
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        # Find script tag that contains the apolloCache object
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

        if script_tag:
            # Extract the JSON string from the script tag
            apollo_cache_str = script_tag.string
        else:
            # Find script tag that contains the apolloState object
            script_tag = soup.find("script", string=re.compile("apolloState"))
            if script_tag:
                # Extract the apolloState object from the script tag
                match = re.search(
                    'apolloState":({.*?})};</script>', str(script_tag), re.DOTALL
                )  # added ( at neginning of apollostate and str() around script_tag
                if match:
                    apollo_cache_str = match.group(1)
                else:
                    raise ValueError("No apolloState object found in script tag")
            else:
                raise ValueError("No script tag with apolloState found")
    except ValueError as e:
        print(f"Error: {e}")
        # Handle the error as needed

    # Find all GraphQL queries in the JSON string
    graphql_queries = re.findall(r'"[^"]*\({[^)]*}\)"', apollo_cache_str)

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
            string.replace("query", "")
            .replace("{", "")
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
        apollo_cache_str = apollo_cache_str.replace(query, f'"{string}"')

    # TESTING
    with open("scraper/structure/apollo_cache_str.json", "w") as f:
        apollo_cache_str_json = json.loads(apollo_cache_str)
        f.write(json.dumps(apollo_cache_str_json, indent=4))

    if "apolloCache" in apollo_cache_str:
        # Load the JSON string into a Python dictionary
        data = json.loads(apollo_cache_str)

        # Access the apolloCache object from the dictionary
        apollo_cache = data["props"]["pageProps"]["apolloCache"]
    else:
        # This will automatically remove duplicate keys
        data = json.loads(apollo_cache_str)

        # Convert the dictionary back into a JSON string
        # This will create a new JSON object without duplicate keys
        apollo_str_temp = json.dumps(data)

        # Now can parse the JSON string without duplicate error
        apollo_cache = json.loads(apollo_str_temp)

    # TESTING
    with open("scraper/structure/apollo_cache.json", "w") as f:
        f.write(json.dumps(apollo_cache, indent=4))

    return apollo_cache


def parse_overview(apollo_cache: dict) -> Dict[str, str | int]:

    overview_data = {}

    try:
        root_query = apollo_cache["ROOT_QUERY"]
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
    except KeyError as e:
        logger.error(f"ROOT_QUERY key not found in cache: {e}")

    ceo_name = None
    for key, value in root_query.items():
        if key.startswith("Ceo:") and isinstance(value, dict):
            ceo_name = value.get("name")
            break

    try:
        # Extract company overview information
        overview = {
            "employer_id": (
                int(overview_data["employerid"]["__ref"].split(":")[1])
                if "employer" in overview_data
                else None
            ),
            "number_of_pages": overview_data["numberOfPages"],
            "all_reviews_count": overview_data["allReviewsCount"],
            "rated_reviews_count": overview_data["ratedReviewsCount"],
            "overall_rating": overview_data["ratings"]["overallRating"],
            "ceo_name": ceo_name
            or (
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
        logger.error(
            f"Key not found in overview data: {e}", extra={"overview": overview_data}
        )
        return None

    return overview


def parse_reviews(apollo_cache: dict) -> Dict[str, Dict[str, str | int]]:

    try:
        root_query = apollo_cache["ROOT_QUERY"]
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
            for key, value in apollo_cache.items()
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
        logger.error(f"Key not found in review data: {e}", extra={"review": review})
        raise

    return reviews


async def scrape_data(
    url: str, max_pages: Optional[int] = None
) -> Tuple[Dict[str, int | float], Dict[str, Dict[str, str | int]]] | None:

    logger.info(f"Scraping reviews from {url}")

    # Extract the apollocache property from __NEXT_DATA__ script tag
    apollo_cache = get_apollocache(url)

    if not apollo_cache:
        logger.error("No data found in apollocache. Exiting.")
        return None

    overview = parse_overview(apollo_cache)
    reviews = parse_reviews(apollo_cache)

    # TESTING ###################################################
    with open("scraper/structure/overview.json", "w") as f:
        f.write(json.dumps(overview, indent=4))
    with open("scraper/structure/reviews.json", "w") as f:
        f.write(json.dumps(reviews, indent=4))

    total_pages = overview["number_of_pages"]

    if max_pages and max_pages < total_pages:
        total_pages = max_pages

    logger.info(
        f"Scraped first reviews page of {url}, scraping remaining {total_pages - 1} pages"
    )

    for page_num in range(2, total_pages + 1):
        page_url = Url.change_page(url, page=page_num)

        # Extract the apollocache property from __NEXT_DATA__ script tag
        apollo_cache = get_apollocache(page_url)

        if not apollo_cache:
            logger.error(f"No data in apollocache on page {page_num}")
            continue  # Skip this page and move on to the next one

        if apollo_cache:  # Check if the page was successfully scraped
            new_reviews = parse_reviews(apollo_cache)
            reviews.update(new_reviews)
        else:
            logger.error(f"Failed to scrape reviews on page {page_num}, {page_url}")

        # Add a delay
        await asyncio.sleep(1)

    logger.info(
        f"Scraping complete for {len(reviews)} reviews from {url} in {total_pages} pages"
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


# Stop the listener
listener.stop()

if __name__ == "__main__":

    # test script
    overview, reviews = asyncio.run(
        scrape_data(
            Url.reviews("NVIDIA", "7633"),
            max_pages=1,
        )
    )
    print("\n\n")
    print("Overview:", overview)
    print("\n\n")
    print("Reviews:", reviews)
