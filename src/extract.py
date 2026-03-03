# import necessary libraries
from pathlib import Path
import logging
import requests
from datetime import datetime, timezone
import time
import json


# constants
BASE_URL = 'https://api.fda.gov/drug/shortages.json'
LIMIT = 100
RETRIES = 3
LOGS_DIR = Path('logs')

# setup
## Create necessary directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)

## Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'extract.log'),
        logging.StreamHandler() # Log to console as well
    ]
)


def extract_data(url:str, retries:int=RETRIES) -> dict | None:
    """ a function to fetch data from API with retry logic

    Args:
        url (str): API endpoint to fetch data from
        retries (int): number of retry attempts in case of failure

    Returns:
        dict: JSON response from the API if successful, None otherwise
    """

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            logging.info(f'Successfully fetched data from {url}')
            return response.json()
        # Handle specific exceptions
        except requests.exceptions.Timeout as e:
            logging.warning(f'Attempt {attempt + 1} timed out, retrying... ({e})')
            time.sleep(2 ** attempt) # Exponential backoff
        except requests.exceptions.HTTPError as e:
            if 500 <= e.response.status_code < 600: # Server errors
                logging.warning(f'Attempt {attempt + 1} failed with server error {e.response.status_code}, retrying... ({e})')
                time.sleep(2 ** attempt) # Exponential backoff
            else:
                logging.error(f'HTTP error occurred: {e}') # no retry for other HTTP errors
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            break
    logging.error(f"All {retries} attempts failed for {url}.")
    return None


def extract_all_data(base_url:str=BASE_URL, limit:int=LIMIT) -> tuple[list, dict| None, datetime]:
    """ a function to extract all data using pagination.

    Args:
        base_url (str): API endpoint to fetch data from
        limit (int): number of records to fetch per page

    Returns:
        tuple: (list of all records, API metadata if available, timestamp of extraction)
    """
    all_data = []
    skip = 0
    extracted_at = datetime.now(timezone.utc)
    api_meta = None

    while True:
        url = f'{base_url}?limit={limit}&skip={skip}'
        logging.info(f'Extracting data with skip={skip} and limit={limit}.')

        # Extract data from API
        data = extract_data(url)

        # Check if data is valid and contains results
        if not data or 'results' not in data:
            logging.info('No more data. Ending extraction.')
            break

        # Extract metadata from API if exists and not already extracted
        if api_meta is None and 'meta' in data:
            api_meta = data['meta']
            logging.info('API metadata extracted successfully.')

        # Extend all_data with results from current page
        results = data['results']
        all_data.extend(results)
        logging.info(f'Fetched {len(results)} records. Total so far: {len(all_data)}')

        # Check if we reached the last page
        if len(results) < limit:
            logging.info('Last page reached. Ending extraction.')
            break

        # Increment skip for next page
        skip += limit

    # Validate record count against API metadata if available
    api_total = api_meta.get('results', {}).get('total', 0) if api_meta else 0
    if api_total and api_total != len(all_data):
        logging.warning(f'Record count mismatch: fetched {len(all_data)}, API reported {api_total}')
    else:
        logging.info(f'Record count validated: {len(all_data)} records.')

    return all_data, api_meta, extracted_at


def main():
    logging.info('Starting data extraction process.')
    all_data, api_meta, extracted_at = extract_all_data()
    logging.info(f'Data extraction process completed. {len(all_data)} records extracted.')
    return all_data, api_meta, extracted_at


if __name__ == '__main__':
    main()

