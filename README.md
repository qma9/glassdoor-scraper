# Glassdoor scraper

## Description

Scrapes Glassdoor company overview info and reviews using Bright Data's proxy network through playwright. FastAPI endpoints `companies/` and `glassdoor/` trigger scraping for company ids, names and overview info, reviews respectively. The scraped data is then stored in a MySQL database containing a company and reviews table.

## Installation

To install all the required packages, run the following command:

```bash
pip3 install -r requirements.txt
```

## Usage

1. First run `python3 scraper/companies.py` to obtain company ids. Both company names and ids are required to construct the URLs which the data is scraped from. Remember that the `companies/` endpoint requires a list of company names in the request body. For those who already have company names and associated Glassdoor ids this step can be skipped.

2. Second run `python3 app.py` which will query all company ids and names from the company table and trigger the scraper to loop through all companies of interest scraping their overview info and reviews.