import logging
import os
from datetime import datetime
import time
import pandas as pd
from utils.api_client import TutkihallintoaAPI
from utils.bigquery_loader import BigQueryLoader

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_financial_data():
    """Fetch data from Tutkihallintoa API month by month and load it into BigQuery."""
    # BigQuery configuration
    project_id = "massi-financial-analysis"
    dataset_id = "finnish_finance_data"
    table_id = "budget_transactions"
    
    # Create API client
    api_client = TutkihallintoaAPI()
    
    # Create BigQuery loader
    bq_loader = BigQueryLoader(project_id, dataset_id, table_id)
    
    # Ensure the dataset and table exist
    bq_loader.create_dataset_if_not_exists()
    bq_loader.create_table_if_not_exists()
    
    # Define the start and end dates
    start_year = 2022
    start_month = 4
    end_year = 2024
    end_month = 4
    
    # Define the administrative branches (ministries)
    hallinnonala_codes = [
        '23',  # Ministry of Finance
        '24',  # Ministry of Education and Culture
        '25',  # Ministry of Justice  
        '26',  # Ministry of Interior
        '27',  # Ministry of Defense
        '28',  # Ministry of Agriculture and Forestry
        '29',  # Ministry of Transport and Communications
        '30',  # Ministry of Economic Affairs and Employment
        '31',  # Ministry of Social Affairs and Health
        '32',  # Ministry of the Environment
        '33'   # Prime Minister's Office
    ]
    
    # Initialize counter for monitoring progress
    total_records_loaded = 0
    
    for hallinnonala in hallinnonala_codes:
        logger.info(f"Processing data for administrative branch {hallinnonala}")
        
        current_year = start_year
        current_month = start_month
        
        # Loop through each month in the range
        while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
            logger.info(f"Processing data for branch {hallinnonala}, {current_year}-{current_month:02d}...")
            
            # First, make a basic query with just hallinnonala and the date
            params = {
                'yearFrom': current_year,
                'yearTo': current_year,
                'monthFrom': current_month,
                'monthTo': current_month,
                'hallinnonala': hallinnonala
            }
            
            df = api_client.make_request(params)
            
            if df is not None and not df.empty:
                logger.info(f"Fetched {len(df)} rows for branch {hallinnonala}, {current_year}-{current_month:02d}")
                
                # Load data to BigQuery
                job_id = bq_loader.load_dataframe(df, write_disposition="WRITE_APPEND")
                
                if job_id:
                    logger.info(f"Successfully loaded {len(df)} rows for branch {hallinnonala}, {current_year}-{current_month:02d} to BigQuery (job_id: {job_id})")
                    total_records_loaded += len(df)
                else:
                    logger.error(f"Failed to load data for branch {hallinnonala}, {current_year}-{current_month:02d} to BigQuery")
            else:
                logger.warning(f"No data available for branch {hallinnonala}, {current_year}-{current_month:02d}")
            
            # Move to the next month
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1
            
            # Add a small delay between API calls to respect rate limits
            time.sleep(2)  # 2 seconds delay
    
    logger.info(f"Total records loaded into BigQuery: {total_records_loaded}")

if __name__ == "__main__":
    # Unset credentials env var to use application default credentials
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        logger.info("Unsetting GOOGLE_APPLICATION_CREDENTIALS to use application default credentials")
        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    
    logger.info("Starting financial data load process for Apr 2022 to Apr 2024...")
    start_time = datetime.now()
    
    try:
        load_financial_data()
        logger.info("Financial data load process completed successfully!")
    except Exception as e:
        logger.error(f"Error in financial data load process: {str(e)}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Process duration: {duration}")