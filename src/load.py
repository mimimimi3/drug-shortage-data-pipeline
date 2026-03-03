import os
import logging
from pathlib import Path
from datetime import datetime
from google.cloud import storage
from dotenv import load_dotenv
import json
from google.api_core.exceptions import GoogleAPIError

# load environment variables from .env file
load_dotenv()

# Constants
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
PROJECT_ID = os.getenv('PROJECT_ID')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')


LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)


## Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'load.log'),
        logging.StreamHandler() # Log to console as well
    ]
)

if not PROJECT_ID:
    logging.error('PROJECT_ID environment variable is not set. Please set it in the .env file.')
    raise ValueError('PROJECT_ID environment variable is not set.')

if not GCS_BUCKET_NAME:
    logging.error('GCS_BUCKET_NAME environment variable is not set. Please set it in the .env file.')
    raise ValueError('GCS_BUCKET_NAME environment variable is not set.')


# Initialize GCS client
storage_client = storage.Client(project=PROJECT_ID)


def generate_content(all_data:list, api_meta:dict, extracted_at:datetime) -> tuple[str, str, str, str]:
    """
    Generate content to be uploaded to GCS.
    Args:
        all_data (list): List of all records extracted from the API.
        api_meta (dict): Metadata about the API response
        extracted_at (datetime): Timestamp when the data was extracted.

    Returns:
        str: JSON string of the content to be uploaded to GCS.
    """
    date_path = extracted_at.strftime('year=%Y/month=%m/day=%d')
    file_date = extracted_at.strftime('%Y-%m-%d-%H-%M-%S')
    data_blob_name = f'raw_dataset/{date_path}/drug_shortages_{file_date}.ndjson'
    metadata_blob_name = f'raw_dataset/{date_path}/drug_shortages_{file_date}_metadata.json'
     
    data_content = '\n'.join(json.dumps({**record, 'extracted_at': extracted_at.isoformat()}) for record in all_data)
    metadata_content = json.dumps({
        'extraction_metadata': {
            'extracted_at': extracted_at.isoformat(),
            'source': 'OpenFDA API Drug Shortages Endpoint',
            'total_records': len(all_data)
        },
        'api_meta': api_meta,
    }, indent=2)
    
    logging.info(f'Generated content for GCS upload with {len(all_data)} records and metadata.')
    return data_content, data_blob_name, metadata_content, metadata_blob_name


def load_to_gcs(contents:str, destination_blob_name:str, content_type:str= 'application/x-ndjson', bucket_name:str=GCS_BUCKET_NAME) -> None:
    """
    Uploads a file to the bucket.
    Args:
        bucket_name (str): The name of the GCS bucket.
        contents (str): The content to be uploaded to GCS.
        destination_blob_name (str): The name of the destination blob in GCS.
    Returns:
        None
    """

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    try:
        blob.upload_from_string(contents, content_type = content_type)
    except GoogleAPIError as e:
        logging.error(f'Error uploading file to GCS: {e}')
        raise

    logging.info(f'File uploaded to {destination_blob_name} in bucket {bucket_name}.')


def main(all_data:list, api_meta:dict, extracted_at:datetime) -> str:
    logging.info('Starting load process...')
    data_contents, data_blob_name, metadata_contents, metadata_blob_name = generate_content(all_data, api_meta, extracted_at)
    load_to_gcs(contents=data_contents, destination_blob_name=data_blob_name, content_type = 'application/x-ndjson')
    load_to_gcs(contents=metadata_contents, destination_blob_name=metadata_blob_name, content_type = 'application/json')
    logging.info('Load process completed successfully.')
    return data_blob_name

if __name__ == "__main__":
    from src.extract import main as extract
    all_data, api_meta, extracted_at = extract()
    main(all_data, api_meta, extracted_at)