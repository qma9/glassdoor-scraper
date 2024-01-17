from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the URL for the database
URL_DB = os.environ.get("URL_DB")

# Create the engine and session
engine = create_engine(URL_DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the base class for the models
Base = declarative_base()
