import pandas as pd
import numpy as np

from typing import Optional, List
from enum import Enum
import logging
import re
import json
import datetime


def configure_logging():
    """
    Sets up the logging configuration for the application.
    It configures the logging level to INFO, sets the log message format,
    and adds two handlers: a StreamHandler to log messages to the console,
    and a FileHandler to log messages to a file named "logfile.log".
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("logfile.log")],
    )


def get_unique_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the observation with the lowest tier for each gvkey.
    Drop the tier column and rename the employer column to employer_name.
    """
    return (
        df.sort_values(["gvkey", "tier"], ascending=True)
        .drop_duplicates(subset="gvkey", keep="first")
        .drop_duplicates(subset="employer", keep="first")
        .drop(columns=["tier"])
        .rename(columns={"employer": "employer_name"})
    )


def get_unique_queries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop the idcompanies and Unamed: 5 columns.
    Rename company column to employer_name and gvkey column to is_gvkey.
    Convert is_gvkey column to boolean type, replacing NaN values with 0.
    """
    df = df.drop(columns=["idcompanies", "Unnamed: 5"]).rename(
        columns={"company": "employer_name", "url": "url_old", "gvkey": "is_gvkey"}
    )
    df["is_gvkey"] = df["is_gvkey"].fillna(0).astype(bool)
    return df


def transform_url(url: str) -> str | None:
    """
    Transform overview or old reviews url to the proper reviews url.
    """
    if "/Reviews/" in url:
        return url

    match_id = re.search(r"-EI_IE(\d+)\.", url)
    match_name = re.search(r"Working-at-([\w%-]+)-E", url)
    if match_id and match_name:
        employer_id = match_id.group(1)
        employer_name = match_name.group(1)
        return f"https://www.glassdoor.com/Reviews/{employer_name}-Reviews-E{employer_id}.htm"
    else:
        return None


def extract_id(url: str) -> int | None:
    """
    Extract the employer id from the url.
    """
    if url is not None:
        match = re.search(r"-E(\d+)", url)
        if match:
            return int(match.group(1))
    return np.nan


def clean_text(text: str) -> str | None:
    """
    Clean text fields by removing escape characters, special characters, and converting to lowercase.
    """
    
    if text is None:
        return None

    contractions_expansions = {
        "ain't": "am not",
        "aren't": "are not",
        "can't": "cannot",
        "can't've": "cannot have",
        "'cause": "because",
        "could've": "could have",
        "couldn't": "could not",
        "couldn't've": "could not have",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hadn't've": "had not have",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'd've": "he would have",
        "he'll": "he will",
        "he'll've": "he will have",
        "he's": "he is",
        "how'd": "how did",
        "how'd'y": "how do you",
        "how'll": "how will",
        "how's": "how is",
        "I'd": "I would",
        "I'd've": "I would have",
        "I'll": "I will",
        "I'll've": "I will have",
        "I'm": "I am",
        "I've": "I have",
        "isn't": "is not",
        "it'd": "it had",
        "it'd've": "it would have",
        "it'll": "it will",
        "it'll've": "it will have",
        "it's": "it is",
        "let's": "let us",
        "ma'am": "madam",
        "mayn't": "may not",
        "might've": "might have",
        "mightn't": "might not",
        "mightn't've": "might not have",
        "must've": "must have",
        "mustn't": "must not",
        "mustn't've": "must not have",
        "needn't": "need not",
        "needn't've": "need not have",
        "o'clock": "of the clock",
        "oughtn't": "ought not",
        "oughtn't've": "ought not have",
        "shan't": "shall not",
        "sha'n't": "shall not",
        "shan't've": "shall not have",
        "she'd": "she would",
        "she'd've": "she would have",
        "she'll": "she will",
        "she'll've": "she will have",
        "she's": "she is",
        "should've": "should have",
        "shouldn't": "should not",
        "shouldn't've": "should not have",
        "so've": "so have",
        "so's": "so is",
        "that'd": "that would",
        "that'd've": "that would have",
        "that's": "that is",
        "there'd": "there had",
        "there'd've": "there would have",
        "there's": "there is",
        "they'd": "they would",
        "they'd've": "they would have",
        "they'll": "they will",
        "they'll've": "they will have",
        "they're": "they are",
        "they've": "they have",
        "to've": "to have",
        "wasn't": "was not",
        "we'd": "we had",
        "we'd've": "we would have",
        "we'll": "we will",
        "we'll've": "we will have",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what'll've": "what will have",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "when's": "when is",
        "when've": "when have",
        "where'd": "where did",
        "where's": "where is",
        "where've": "where have",
        "who'll": "who will",
        "who'll've": "who will have",
        "who's": "who is",
        "who've": "who have",
        "why's": "why is",
        "why've": "why have",
        "will've": "will have",
        "won't": "will not",
        "won't've": "will not have",
        "would've": "would have",
        "wouldn't": "would not",
        "wouldn't've": "would not have",
        "y'all": "you all",
        "y'alls": "you alls",
        "y'all'd": "you all would",
        "y'all'd've": "you all would have",
        "y'all're": "you all are",
        "y'all've": "you all have",
        "you'd": "you had",
        "you'd've": "you would have",
        "you'll": "you you will",
        "you'll've": "you you will have",
        "you're": "you are",
        "you've": "you have"
    }

    # Expand contractions
    contractions_pattern = re.compile('({})'.format('|'.join(contractions_expansions.keys())), 
                                      flags=re.IGNORECASE)
    
    def expand_match(contraction):
        """
        Get contraction match and expand it.
        """
        match = contraction.group(0)
        return contractions_expansions.get(match.lower())
    
    text = contractions_pattern.sub(expand_match, text)
    text = re.sub(r'\s', ' ', text)   # replace escape characters with a space
    text = re.sub(r'[^\w\s]', ' ', text)   # replace special characters with a space
    text = re.sub(r'\s+', ' ', text)   # replace multiple spaces with a single space
    return text.lower()   # convert to lowercase


class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return super().default(o)
    

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
            f"https://www.glassdoor.com/Reviews/{employer}-Reviews-E{employer_id}.htm"
        )
        if regions:
            region_queries = "&".join(f"filter.countryId={region.value}" for region in regions)
            url += f"?{region_queries}"

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

    # TESTING
    url = "https://www.glassdoor.com/Reviews/Gazprom-Reviews-E6457.htm"

    url_new = transform_url(url)

    print(f"\nOld URL: {url}\nNew URL: {url_new}\n")

    employer_id = extract_id(url_new)

    print(f"Employer ID: {employer_id}\n")
