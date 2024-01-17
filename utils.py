import os
import json
import logging


def load_auth():
    """
    Load authentication credentials from auth.json
    """
    FILE = os.path.join("scraper", "auth.json")
    with open(FILE, "r") as f:
        return json.load(f)


def get_db():
    """
    Instatiate database session
    """
    from database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def configure_logging():
    """
    Configure logging
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("logfile.log")],
    )
