from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from contextlib import contextmanager
from dotenv import load_dotenv
import os


# Load environment variables
load_dotenv()


# Create the engine and session
engine = create_engine(
    os.environ.get("URL_DB"), connect_args={"check_same_thread": False}
)
SessionFactory = sessionmaker(autocommit=False, bind=engine)  # autoflush=False

# Create the base class for the models
Base = declarative_base()


@contextmanager
def get_db():
    """
    Get a database session.
    """
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
