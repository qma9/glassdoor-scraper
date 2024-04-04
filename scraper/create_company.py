import pandas as pd
from dotenv import load_dotenv

import os
import sys

# Append the path to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()  # Load .env file

from database import engine, Company, get_db
from scraper.utils import get_unique_companies

# Create the Company table
Company.__table__.create(bind=engine, checkfirst=True)

# Load companies
df = pd.read_csv(os.getenv("COMPANY_NAMES"))

# Keep the observation with the lowest tier for each gvkey and drop tier column
df_unique = get_unique_companies(df)

with get_db() as session:

    # Iterate over DataFrame rows
    for index, row in df_unique.iterrows():
        # Create a Company object for each row
        company = Company(**row.to_dict())

        # Add the Company object to the session
        session.add(company)

    # Commit the session to the database
    session.commit()
