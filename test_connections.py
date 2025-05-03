import logging
import sys
import os
import pandas as pd
import io
import requests
from google.cloud import bigquery
from dotenv import load_dotenv
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# Clear out any problematic credentials env var
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    logger.info("Unsetting GOOGLE_APPLICATION_CREDENTIALS to use application default credentials")
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Load environment variables
load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID')
TABLE_ID = os.getenv('TABLE_ID')
API_BASE_URL = "https://api.tutkihallintoa.fi/valtiontalous/v1/budjettitaloudentapahtumat"

def test_api():
    """Test the API connection."""
    logger.info("Testing API connection...")
    
    # Use a simple query for June 2022
    params = {
        'yearFrom': 2022,
        'yearTo': 2022,
        'monthFrom': 6,
        'monthTo': 6,
        'hallinnonala': '28'
    }
    
    try:
        response = requests.get(API_BASE_URL, params=params)
        logger.info(f"API response status: {response.status_code}")
        
        if response.ok:
            try:
                # Try to parse as CSV
                df = pd.read_csv(io.StringIO(response.text), sep=',')
                logger.info(f"Successfully parsed API response with {len(df)} rows")
                logger.info(f"First few rows: {df.head(2).to_dict()}")
                return df
            except Exception as e:
                logger.error(f"Failed to parse API response: {str(e)}")
                logger.info(f"Response content (first 500 chars): {response.text[:500]}")
                return None
        else:
            logger.error(f"API request failed: {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Exception during API request: {str(e)}")
        return None

def test_bigquery():
    """Test BigQuery connection."""
    logger.info(f"Testing BigQuery connection to {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}...")
    
    try:
        client = bigquery.Client(project=PROJECT_ID)
        logger.info("Successfully created BigQuery client")
        
        # Test listing datasets
        datasets = list(client.list_datasets())
        logger.info(f"Found {len(datasets)} datasets in project {PROJECT_ID}")
        for dataset in datasets:
            logger.info(f"  - {dataset.dataset_id}")
        
        # Try to access the specific dataset
        if DATASET_ID:
            try:
                dataset_ref = client.dataset(DATASET_ID)
                dataset = client.get_dataset(dataset_ref)
                logger.info(f"Successfully accessed dataset {DATASET_ID}")
                
                # List tables in the dataset
                tables = list(client.list_tables(dataset_ref))
                logger.info(f"Found {len(tables)} tables in dataset {DATASET_ID}")
                for table in tables:
                    logger.info(f"  - {table.table_id}")
                
                # Try to access the specific table
                if TABLE_ID and TABLE_ID in [t.table_id for t in tables]:
                    table_ref = dataset_ref.table(TABLE_ID)
                    table = client.get_table(table_ref)
                    logger.info(f"Successfully accessed table {TABLE_ID}")
                    logger.info(f"Table has {table.num_rows} rows and {len(table.schema)} columns")
                    
                    # Run a sample query
                    query = f"SELECT COUNT(*) as row_count FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
                    query_job = client.query(query)
                    results = query_job.result()
                    
                    for row in results:
                        logger.info(f"Table row count: {row.row_count}")
                
                return True
            except Exception as e:
                logger.error(f"Error accessing dataset or table: {str(e)}")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error connecting to BigQuery: {str(e)}")
        return False

def test_bigquery_cli():
    """Test BigQuery connection using the bq command-line tool."""
    logger.info(f"Testing BigQuery connection to {PROJECT_ID}.{DATASET_ID}.{TABLE_ID} using bq CLI...")

    try:
        # Check if bq command is available
        try:
            subprocess.run(["bq", "version"], check=True, capture_output=True, text=True)
            logger.info("bq command is available")
        except Exception as e:
            logger.error(f"bq command not found: {str(e)}")
            logger.error("Please make sure Google Cloud SDK is installed and in your PATH")
            return False

        # List datasets in the project
        try:
            result = subprocess.run(
                ["bq", "ls", f"--project_id={PROJECT_ID}"], 
                check=True, capture_output=True, text=True
            )
            logger.info(f"Datasets in project {PROJECT_ID}:")
            logger.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error listing datasets: {e.stderr}")
            return False

        # Check if our dataset exists
        try:
            result = subprocess.run(
                ["bq", "ls", f"--project_id={PROJECT_ID}", f"{PROJECT_ID}:{DATASET_ID}"], 
                capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info(f"Dataset {DATASET_ID} exists")
                logger.info(f"Tables in dataset {DATASET_ID}:")
                logger.info(result.stdout)
            else:
                logger.error(f"Dataset {DATASET_ID} does not exist or is not accessible")
                logger.error(result.stderr)
                return False
        except Exception as e:
            logger.error(f"Error checking dataset: {str(e)}")
            return False

        # Check if our table exists
        try:
            result = subprocess.run(
                ["bq", "show", f"--project_id={PROJECT_ID}", f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}"], 
                capture_output=True, text=True
            )

            if result.returncode == 0:
                logger.info(f"Table {TABLE_ID} exists")
                logger.info("Table information:")
                logger.info(result.stdout)
            else:
                logger.error(f"Table {TABLE_ID} does not exist or is not accessible")
                logger.error(result.stderr)
                return False
        except Exception as e:
            logger.error(f"Error checking table: {str(e)}")
            return False

        return True
    except Exception as e:
        logger.error(f"Error testing BigQuery connection: {str(e)}")
        return False

def main():
    logger.info("Starting connection tests...")
    
    # Test API
    df = test_api()
    api_success = df is not None
    
    # Test BigQuery with client library
    bq_success = test_bigquery()

    # Test BigQuery with CLI
    bq_cli_success = test_bigquery_cli()
    
    # Summary
    logger.info("\nTest results summary:")
    logger.info(f"API connection: {'SUCCESS' if api_success else 'FAILED'}")
    logger.info(f"BigQuery connection (client): {'SUCCESS' if bq_success else 'FAILED'}")
    logger.info(f"BigQuery connection (CLI): {'SUCCESS' if bq_cli_success else 'FAILED'}")
    
    if api_success and bq_success and bq_cli_success:
        logger.info("All connections successful!")
        
        if df is not None and not df.empty:
            # Try to load a small sample to BigQuery
            logger.info("Attempting to load 10 rows of sample data to BigQuery...")
            
            try:
                client = bigquery.Client(project=PROJECT_ID)
                table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
                
                # Take just 10 rows for testing
                sample_df = df.head(10)
                
                # Load to BigQuery
                job_config = bigquery.LoadJobConfig(
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                )
                
                job = client.load_table_from_dataframe(
                    sample_df, table_ref, job_config=job_config
                )
                job.result()  # Wait for the job to complete
                
                logger.info(f"Successfully loaded {len(sample_df)} rows to BigQuery")
            except Exception as e:
                logger.error(f"Error loading sample data to BigQuery: {str(e)}")
    else:
        logger.error("Some connection tests failed. Please check the logs.")

if __name__ == "__main__":
    main()