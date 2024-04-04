# Glassdoor scraper

## Description

Scrape Glassdoor **company overview information** and **reviews** using a proxy service. 

`scraper/companies.py` scrapes search results from Glassdoor search URL by using company name as query parameter. First fetches company names from the `employer_name` field in `Company` table in SQLite database in `output/` directory (must be added to root by user). It then iterates through those company names using each name as the query in Glassdoor search URL. Then updates `employer_id` in Company table from best match in search results. Finally, builds Glassdoor reviews URLs from `employer_name` and `employer_id`, stored as `url_new` in `Company` table.

`scraper/main.py` runs `scrape_data()` function from `scraper/glassdoor.py`. First, fetches all previously built URLs from `Company` table. Then iterates through all URLs and scrapes the overview and reviews data from either an apolloCache or apolloSate object in the source HTML, as served by the server. Note that JavaScript client-side rendering is avoided on purpose, hence why `requests` package is used to send request, not e.g. `playwright`. This is done because the apollo objects, which are GraphQL cache objects, are cleared from the DOM after page load. Then overview and reviews data is parsed into dictionaries which are committed to the database's `Company` and `Review` tables, respectively. 

See `design/design.png` for scraper's design diagram.

## Installation

First, initialize a virtual environment in project root. virtualenv was used originally, hence the `requirements.txt` file.
Use at least python version 3.11.8 (last run version). Version 3.12.* was used previously and should work too.

If wondering how to activate virtual environment or VScode or toher editor doesn't pick it up, run this command if virtual environment is named `.venv`.

```bash
source .venv/bin/activate
```

To install all the required packages, run the following command after activating virtual environment:

```bash
pip install -r requirements.txt
```

## Usage

**Note**: Rename `example.env` to `.env` and add your chosen proxy service's credentials to the corresponding environment variables or add new ones. 

**IMPORTANT**:
Choose a product that automatically solves CAPTCHAS and creates headers as well as rotating IPs. A basic residential proxy network will NOT work for scraping Glassdoor.

Here are some options:
- Oxylab's Web Scraper API (1 week free trial for testing)
- Smartproxy's Site Unblocker* (no free trial)
- Brightdata's Web Unlocker ($10 free credit for testing)

The rates for these services vary, some charge per GB and some charge per CPM (1000 requests).

*Strangely, Smartproxy requires that JavaScript rendering be enabled with the `{"X-SU-Headles": "html"}` header, although the original HTML is still returned by `requests` get request.
 

0. Before running any of the code, create a SQLite database with a `Company` table following the structure found in `scraper/database/models.py` in a directory called `output/` within the project root. 

Then fill the `employer_name` field in `Company` table with company names to be scraped.


1. First run:

```bash
python scraper/companies.py
``` 
This will fill `employer_id` field in company table. Both `employer_id` and `employer_name` are required to construct the URLs which data is scraped from.


2. Second run:

**Note**: Modify the query database filter in `get_all_urls` to include only `Company.url_new.isnot(None)`. Other logic was used to filter for publicly traded North American companies with gvkeys and tickers from a larger database of private and public companies.

```bash
python scraper/main.py
``` 

This will query all company ids, names, and URLs from the `Company` table and trigger the scraper looping through all the companies in the database and scrape their overview information and reviews.