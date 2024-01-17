import pandas as pd

import os
import json
import logging


def get_db():
    """
    Get a database session.
    """
    from database.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    """
    return df.sort_values(["gvkey", "tier"], ascending=True).drop_duplicates(
        subset="gvkey", keep="first"
    )
