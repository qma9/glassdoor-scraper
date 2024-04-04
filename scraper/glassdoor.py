from graphql import parse, print_ast
from bs4 import BeautifulSoup
from requests import HTTPError, RequestException, ConnectionError, Timeout, TooManyRedirects
import requests

# import simplejson as json

from typing import Optional, Dict, Tuple
from datetime import datetime

import urllib3
import json
import re
import asyncio
from dotenv import load_dotenv
import sys
import os
import re
import time

# Disable SSL warnings for smartproxy
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load .env file
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from log.setup import logger
from utils import DateTimeEncoder, Url, clean_text


def get_apollo(url: str) -> dict | None:
    """
    Retrieves the apolloCache or apolloState object from a given Glassdoor URL's HTML.

    Args:
        url (str): The URL to fetch the apollo object from.

    Returns:
        dict | None: The apollo object as a dictionary, or None if the apollo object is not found.
    """
    # Modify proxy service credentials, headers, proxies, and request depending on proxy service used
    cred = {
        "username": os.getenv("SMART_USERNAME"),
        "password": os.getenv("SMART_PASSWORD"),
    }
    proxies = {
        "http": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
        "https": f'http://{cred["username"]}:{cred["password"]}@unblock.smartproxy.com:60000',
    }
    # Weirdly, smartproxy requires this header for js rendering, although the original HTML is returned
    headers = {"X-SU-Headles": "html"}

    http_attempts, max_http_attempts = 0, 10
    network_attempts, max_network_attempts = 0, 60
    while http_attempts < max_http_attempts and network_attempts < max_network_attempts:
        response = None
        try:
            # Change request depending on proxy service used
            response = requests.request(
                "GET", url, verify=False, proxies=proxies, headers=headers
            )
            response.raise_for_status()
            break
        except HTTPError as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'HTTP error: {e}', extra={"status_code": status_code, "URL": url})
            http_attempts += 1
            time.sleep(1)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'Network error: {e}', extra={"status_code": status_code, "URL": url})
            network_attempts += 1
            time.sleep(30)
        except RequestException as e:
            status_code = response.status_code if response else 'No response code'
            logger.error(f'Other request error: {e}', extra={"status_code": status_code, "URL": url})
            return None
        
    if http_attempts == max_http_attempts or network_attempts == max_network_attempts:
        return None

    ######################## TESTING ############################
    # print(f"\nStatus Code: {response.status_code}\n")

    ######################## TESTING ############################
    # print(f"URL: {url}\n")

    ######################## TESTING ############################
    # with open("scraper/structure/smartproxy_response.txt", "w", encoding="utf-8") as f:
    #     f.write(response.text)

    # Load the JSON string into dictionary
    # app_cache_json = json.loads(response.text)  # Oxylab's response

    # Parse the HTML with BeautifulSoup
    # soup = BeautifulSoup(app_cache_json["results"][0]["content"], "html.parser")  # Oxylab's response
    soup = BeautifulSoup(response.text, "html.parser")

    try:
        apollo_cache_str = ""
        # Find script tag that contains the apolloCache object
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})

        if script_tag:
            # Extract the JSON string from the script tag
            apollo_cache_str = script_tag.string
            logger.info(f"ApolloCache response", extra={"URL": url})

            ######################## TESTING ############################
            # print(f"ApolloCache response.\n")
        else:
            # Find script tag that contains the apolloState object
            script_tag = soup.find("script", string=re.compile("apolloState"))
            if script_tag:
                # Extract the apolloState object from the script tag
                match = re.search(
                    'apolloState":({.*?})};</script>', str(script_tag), re.DOTALL
                )  # added ( at beginning of apollostate and str() around script_tag
                if match:
                    apollo_cache_str = match.group(1)
                    logger.info("ApolloState response", extra={"URL": url})

                    ######################## TESTING ############################
                    # print(f"ApolloState response.\n")
                else:
                    raise ValueError("No apolloState object found in script tag")
            else:
                raise ValueError("No script tag with apolloState found")
    except ValueError as e:
        logger.error(f"No apollo object in response: {e}", extra={"URL": url})

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

    ######################## TESTING ############################
    # with open("scraper/structure/apollo_str.json", "w", encoding="utf-8") as f:
    #   apollo_cache_str_json = json.loads(apollo_cache_str)
    #   f.write(json.dumps(apollo_cache_str_json, indent=4))

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

    ######################## TESTING ############################
    # with open("scraper/structure/apollo.json", "w", encoding="utf-8") as f:
    #    f.write(json.dumps(apollo_cache, indent=4))

    return apollo_cache


def parse_overview(apollo_cache: dict) -> Dict[str, str | int]:
    """
    Parse the overview data from the Apollo cache and extract relevant information.

    Args:
        apollo_cache (dict): The Apollo cache containing the overview data.

    Returns:
        dict: A dictionary containing the parsed overview data. The keys include:
            - 'employer_id': The ID of the employer.
            - 'number_of_pages': The number of pages of reviews.
            - 'all_reviews_count': The total count of all reviews.
            - 'rated_reviews_count': The count of rated reviews.
            - 'overall_rating': The overall rating of the employer.
            - 'ceo_name': The name of the CEO.
            - 'ceo_rating': The rating of the CEO.
            - 'recommend_to_friend_rating': The rating for recommending to a friend.
            - 'culture_and_values_rating': The rating for culture and values.
            - 'diversity_and_inclusion_rating': The rating for diversity and inclusion.
            - 'career_opportunities_rating': The rating for career opportunities.
            - 'work_life_balance_rating': The rating for work-life balance.
            - 'senior_management_rating': The rating for senior management.
            - 'compensation_and_benefits_rating': The rating for compensation and benefits.
            - 'business_outlook_rating': The rating for business outlook.

        Note:
            If any key is not found in the overview data, it will be set to None.
    """
    overview_data = {}

    try:
        root_query = apollo_cache["ROOT_QUERY"]
        overview_data = next(
            (
                value
                for key, value in root_query.items()
                if key.startswith("employerReviewsRGid") 
                and isinstance(value, dict)
                and value.get("__typename") == "EmployerReviewsRG"
            ),
            {},
        )
    except KeyError as e:
        logger.error(f"ROOT_QUERY key not found in cache: {e}")

    # Employer ID outer for apollocache response
    employer_id = None
    for key, value in apollo_cache.items():
        if key.startswith("Employer:") and isinstance(value, dict):
            employer_id = value.get("id")
            break

    # Check for apollostate response?
    ceo_name = None
    for key, value in root_query.items():
        if key.startswith("Ceo:") and isinstance(value, dict):
            ceo_name = value.get("name").strip()
            break

    # If ceo_name is still None, check in apollo_cache, Note: for apollocache response
    if ceo_name is None:
        for key, value in apollo_cache.items():
            if key.startswith("Ceo:") and isinstance(value, dict):
                ceo_name = value.get("name").strip()
                break

    try:
        # Extract company overview information
        overview = {
            "employer_id": int(employer_id) or (
                    int(root_query["employerid"]["__ref"].split(":")[1])
                    if "employerid" in root_query
                else (
                    int(overview_data["employer"]["__ref"].split(":")[1])
                    if "employer" in overview_data
                    else None
                )
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
    """
    Parses the reviews data from the Apollo object and returns a dictionary of extracted review information.

    Args:
        apollo_cache (dict): The Apollo object containing the reviews data.

    Returns:
        dict: A dictionary of extracted review information, where the keys are review IDs and the values are dictionaries
              containing the review details.

    Raises:
        KeyError: If any required keys are not found in the cache.
    """
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
                "rating_senior_leadership": review["ratingSeniorLeadership"],
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
                    if "jobEndingYear" in review and review["jobEndingYear"] is not None
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
                "pros": clean_text(review["pros"]),
                "cons": clean_text(review["cons"]),
                "summary": clean_text(review["summary"]),
                "advice": clean_text(review["advice"]),
                "count_helpful": review["countHelpful"],
                "count_not_helpful": review["countNotHelpful"],
                "is_covid19": (
                    bool(review["isCovid19"]) if "isCovid19" in review else None
                ),
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
    """
    Scrapes overview and reviews from the given Glassdoor URL.

    Args:
        url (str): The URL to scrape reviews from.
        max_pages (Optional[int]): The maximum number of pages to scrape. Defaults to None.

    Returns:
        Tuple[Dict[str, int | float], Dict[str, Dict[str, str | int]]] | None: A tuple containing the overview and reviews
        dictionaries, or None if no reviews were scraped.
    """
    logger.info(f"Scraping reviews from {url}")

    total_pages = max_pages if max_pages else 20  
    overview = {}
    reviews = {}
    overview_parsed = False

    # Add country query filters to URL
    if "filter.countryId" not in url:
        url += f"?filter.countryId=1&filter.countryId=3"

    for page_num in range(1, total_pages + 1):
        page_url = url if page_num == 1 else Url.change_page(url, page=page_num)

        # Extract the apollocache or apollostate object
        apollo_cache = get_apollo(page_url)

        if not apollo_cache:
            logger.error(f"No data in apollo object on page {page_num}", extra={"URL": page_url})
            continue  # Skip this page and move on to the next one

        if not overview_parsed:  # If the overview has not been parsed yet, parse it
            overview = parse_overview(apollo_cache)
            total_pages = max_pages if max_pages else overview["number_of_pages"]  # Update total_pages with max_pages if provided, otherwise use number_of_pages
            overview_parsed = True

        # Parse the reviews and update the reviews dict
        new_reviews = parse_reviews(apollo_cache)
        reviews.update(new_reviews)

        # Add a delay
        await asyncio.sleep(1)

    if not reviews:
        return {}, {}  # Return empty dicts if no reviews were scraped

    logger.info(
        f"One scraping pass complete.",
        extra={"URL": url, "total_reviews": len(reviews), "total_pages": total_pages},
    )

    ######################## TESTING ############################
    # Create a structure/ directory in root to test the scraper
    # with open("scraper/structure/overview.json", "w") as f:
    #     f.write(json.dumps(overview, indent=4))
    # with open("scraper/structure/reviews.json", "w") as f:
    #     f.write(json.dumps(reviews, cls=DateTimeEncoder, indent=4))

    return overview, reviews


if __name__ == "__main__":

    # test script
    overview, reviews = asyncio.run(
        scrape_data(
            Url.reviews("Google", "9079"),   #   "NVIDIA", "7633", "Meta", "40772", 
            max_pages=2,
        )
    )
    # print("\n\n")
    # print("Overview:", overview)
    # print("\n\n")
    # print("Reviews:", reviews)
