from sqlalchemy import func
from sqlalchemy import text

from db_utils import get_db
from models import Company, Review

test_companies_tickers = [
    "AAPL",  # 42000
    "GOOGL",  # 51000
    "MSFT",  # 54000
    "NVDA",  # 5500
    "AMD",  # 4800
    "INTC",  # 32000
    "PLTR",  # 733
    "MU",  # 6900
    "META",  # 18000
]

with get_db() as session:
    result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='review'")).fetchone()

if result:
    print("Review table exists.")
else:
    print("Review table does not exist.")

    # result = session.query(Company.employer_name, func.count(Review.id)).join(Review).group_by(Company.employer_name).all()

    # result = session.query(Company.ticker, Company.employer_id).filter(
    #     Company.is_gvkey == 1, 
    #     Company.url_new.isnot(None), 
    #     Company.ticker.isnot(None),
    #     Company.ticker.in_(test_companies_tickers)
    # ).all()

# ticker_to_id = {ticker: employer_id for ticker, employer_id in result}

# print(f"\nTicker to IDs: \n\n{ticker_to_id}\n\n")

# for company_name, review_count in result:
#     print(f"\nCompany: {company_name}, Review Count: {review_count}\n")

# Output:

ticker_to_ids = {
    'MSFT': 1651, 
    'AAPL': 1138, 
    'INTC': 1519, 
    'NVDA': 7633, 
    'MU': 1648, 
    'META': 40772, 
    'AMD': 15
}