from airflow.sdk import dag, task
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

from src.extract import main as extract
from src.load import main as load

# load environment variables from .env file
load_dotenv()

# constants
PROJECT_ID = os.getenv('PROJECT_ID')
GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
BQ_DATASET_NAME = os.getenv('BQ_DATASET_NAME')
BQ_TABLE_NAME = os.getenv('BQ_TABLE_NAME')


default_args = {
    'owner': 'airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=10),
    'email_on_failure': False
}


@dag(
    dag_id = 'fda_drug_shortage_pipeline',
    default_args = default_args,
    description = 'ELT pipeline for FDA drug shortage data',
    schedule = '@daily',
    start_date = datetime(2026,3,1),
    catchup = False,
    tags = ['de']
)


# tasks
def fda_drug_shortage_pipeline():
    
    @task
    def extract_task() -> dict:
        all_data, api_meta, extracted_at = extract()
        output = {
            'all_data': all_data,
            'api_meta': api_meta,
            'extracted_at': extracted_at.isoformat()
        }
        return output
    
    @task
    def load_to_gcs_task(output:dict) ->str:
        extracted_at = datetime.fromisoformat(output['extracted_at'])
        blob_path = load(output['all_data'], output['api_meta'], extracted_at)
        return blob_path
    
    # flow
    output = extract_task()
    blob_path = load_to_gcs_task(output)

   
    load_to_bq_task = GCSToBigQueryOperator(
        task_id='load_to_bq',
        bucket=GCS_BUCKET_NAME,
        source_objects=[blob_path],
        destination_project_dataset_table=f'{PROJECT_ID}:{BQ_DATASET_NAME}.{BQ_TABLE_NAME}',
        write_disposition='WRITE_APPEND',
        source_format='NEWLINE_DELIMITED_JSON',
        autodetect=True,
        time_partitioning={
            'type': 'DAY',
            'field': 'extracted_at'
        }
    )
    
    blob_path >> load_to_bq_task

fda_drug_shortage_pipeline()