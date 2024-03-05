# Glassdoor scraper

## Description

Scrapes Glassdoor company overview info and reviews using a proxy service. `scraper/companies.py` and `scraper/main.py` scripts trigger scraping for company ids and names and overview info and reviews, respectively. The scraped data is then stored in a SQLite database containing a company and reviews table.

See `design/design.png` for scraper's design diagram.

## Installation

To install all the required packages, run the following command:

```bash
pip3 install -r requirements.txt
```

## Usage

1. First run:

```bash
python3 scraper/companies.py
``` 
This will fill company id and name field in company table. Both company name and id are required to construct the URLs which the data is scraped from. Remember that the `scraper/companies.py` requires a list of company names. For those who already have company names and associated Glassdoor ids, this step can be skipped.


2. Second run:

```bash
python3 scraper/main.py
``` 

This will query all company ids and names from the company table and trigger the scraper to loop through all those companies scraping their overview info and reviews.