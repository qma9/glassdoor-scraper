import pandas as pd
import numpy as np

import logging
import re


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


if __name__ == "__main__":

    # TESTING
    url = "https://www.glassdoor.com/Reviews/Gazprom-Reviews-E6457.htm"

    url_new = transform_url(url)

    print(f"\nOld URL: {url}\nNew URL: {url_new}\n")

    employer_id = extract_id(url_new)

    print(f"Employer ID: {employer_id}\n")
