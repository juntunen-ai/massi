import os
import logging
import time
import pandas as pd
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import bigquery
import requests
import io
from typing import Dict, Any, Optional, List
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_pipeline.log"),
        logging.StreamHandler(sys.stdout)  # Explicitly add stdout handler
    ]
)
logger = logging.getLogger(__name__)

# Enhance logging to include more verbose details
logging.getLogger().setLevel(logging.DEBUG)  # Set root logger to DEBUG level

# Load environment variables
load_dotenv()

# Clear out any problematic credentials env var
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    logger.info("Unsetting GOOGLE_APPLICATION_CREDENTIALS to use application default credentials")
    del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

# Configuration
PROJECT_ID = os.getenv('PROJECT_ID')
DATASET_ID = os.getenv('DATASET_ID')
TABLE_ID = os.getenv('TABLE_ID')
PROGRESS_FILE = 'extraction_progress.json'
API_BASE_URL = "https://api.tutkihallintoa.fi/valtiontalous/v1/budjettitaloudentapahtumat"
REQUEST_DELAY = 3.0  # Seconds between requests to avoid rate limiting

class DataPipeline:
    """Pipeline for extracting financial data from Tutkihallintoa API and loading it to BigQuery."""
    
    def __init__(self):
        """Initialize the data pipeline."""
        logger.debug("Initializing DataPipeline class...")
        self.session = requests.Session()
        self.last_request_time = 0
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        self.table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        self.progress = self._load_progress()
        
    def _load_progress(self) -> Dict[str, Any]:
        """Load extraction progress from file or initialize if not exists."""
        logger.debug("Attempting to load progress from file...")
        try:
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
                logger.info(f"Loaded progress from {PROGRESS_FILE}")
                return progress
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info(f"No valid progress file found. Initializing new progress.")
            return {
                'last_extraction': None,
                'completed': {},
                'failed': {}
            }
    
    def _save_progress(self):
        """Save extraction progress to file."""
        self.progress['last_extraction'] = datetime.now().isoformat()
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f, indent=2)
        logger.info(f"Progress saved to {PROGRESS_FILE}")
    
    def _respect_rate_limit(self):
        """Ensure we wait enough time between requests to avoid rate limiting."""
        logger.debug("Checking rate limit before making API request...")
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < REQUEST_DELAY:
            sleep_time = REQUEST_DELAY - time_since_last_request
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def extract_month_data(self, year: int, month: int, ha_tunnus: str = '28') -> Optional[pd.DataFrame]:
        """
        Extract data for a specific year and month from the API.
        
        Args:
            year (int): Year to extract
            month (int): Month to extract (1-12)
            ha_tunnus (str): Administrative branch code
            
        Returns:
            Optional[pd.DataFrame]: Extracted data as DataFrame or None if failed
        """
        self._respect_rate_limit()
        
        params = {
            'yearFrom': year,
            'yearTo': year,
            'monthFrom': month,
            'monthTo': month,
            'hallinnonala': ha_tunnus
        }
        
        logger.info(f"Extracting data for {year}-{month:02d}, ha_tunnus={ha_tunnus}")
        logger.debug(f"API request parameters: {params}")
        
        try:
            response = self.session.get(API_BASE_URL, params=params)
            
            if not response.ok:
                logger.error(f"API request failed with status {response.status_code}: {response.text[:200]}")
                return None
            
            # Parse CSV data
            try:
                df = pd.read_csv(io.StringIO(response.text), sep=',')
                logger.info(f"Successfully extracted {len(df)} rows for {year}-{month:02d}")
                return df
            except Exception as e:
                logger.error(f"Failed to parse CSV response: {str(e)}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    
    def load_to_bigquery(self, df: pd.DataFrame) -> bool:
        """
        Load DataFrame to BigQuery.
        
        Args:
            df (pd.DataFrame): DataFrame to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        if df is None or df.empty:
            logger.warning("No data to load to BigQuery")
            return False
        
        try:
            # Handle NaN values
            df = df.where(pd.notnull(df), None)
            
            # Load data to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            
            logger.debug(f"Preparing to load DataFrame with {len(df)} rows to BigQuery table {self.table_ref}")
            job = self.bq_client.load_table_from_dataframe(
                df, self.table_ref, job_config=job_config
            )
            job.result()  # Wait for the job to complete
            
            logger.info(f"Successfully loaded {len(df)} rows to BigQuery")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data to BigQuery: {str(e)}")
            return False
    
    def process_month(self, year: int, month: int, ha_tunnus: str = '28') -> bool:
        """
        Process data for a specific month.
        
        Args:
            year (int): Year to process
            month (int): Month to process (1-12)
            ha_tunnus (str): Administrative branch code
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if already completed
        period_key = f"{year}-{month:02d}-{ha_tunnus}"
        if period_key in self.progress.get('completed', {}):
            logger.info(f"Period {period_key} already processed. Skipping.")
            return True
        
        # Extract data
        df = self.extract_month_data(year, month, ha_tunnus)
        
        if df is not None and not df.empty:
            # Load data to BigQuery
            if self.load_to_bigquery(df):
                self.progress['completed'][period_key] = True
                self._save_progress()
                return True
            else:
                self.progress['failed'][period_key] = True
                self._save_progress()
                return False
        else:
            self.progress['failed'][period_key] = True
            self._save_progress()
            return False

    def process_range(self, start_year: int, end_year: int, start_month: int, end_month: int, ha_tunnus: str = '28'):
        """
        Process data for a range of years and months.
        
        Args:
            start_year (int): Start year
            end_year (int): End year
            start_month (int): Start month (1-12)
            end_month (int): End month (1-12)
            ha_tunnus (str): Administrative branch code
        """
        current_period = 0
        for year in range(start_year, end_year + 1):
            for month in range(start_month, end_month + 1):
                self.process_month(year, month, ha_tunnus)
                current_period += 1
                # Save progress periodically
                if current_period % 5 == 0:
                    self._save_progress()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and load financial data to BigQuery")
    parser.add_argument("--start-year", type=int, default=2022, help="Start year for data extraction (default: 2022)")
    parser.add_argument("--end-year", type=int, default=2025, help="End year for data extraction (default: 2025)")
    parser.add_argument("--start-month", type=int, default=1, help="Start month for data extraction (default: 1)")
    parser.add_argument("--end-month", type=int, default=12, help="End month for data extraction (default: 12)")
    parser.add_argument("--ha-tunnus", type=str, default="28", help="Administrative branch code (default: 28)")

    args = parser.parse_args()

    # Set default values if arguments are not provided
    start_year = args.start_year if args.start_year else datetime.now().year
    end_year = args.end_year if args.end_year else datetime.now().year

    pipeline = DataPipeline()
    pipeline.process_range(
        start_year=start_year,
        end_year=end_year,
        start_month=args.start_month,
        end_month=args.end_month,
        ha_tunnus=args.ha_tunnus
    )