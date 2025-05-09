"""
Simple test script for BigQuery connectivity.
"""

import logging
import sys
from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "massi-financial-analysis"
DATASET_ID = "finnish_finance_data"
TABLE_ID = "budget_transactions"

def test_bigquery_connection():
    """Test BigQuery connection and run a simple query."""
    logger.info("Testing BigQuery connection...")
    
    try:
        # Create a client
        client = bigquery.Client(project=PROJECT_ID)
        logger.info("✅ Successfully created BigQuery client")
        
        # Test with a simple query
        query = f"""
        SELECT COUNT(*) as row_count 
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        """
        
        logger.info(f"Running query: {query}")
        query_job = client.query(query)
        results = query_job.result()
        
        for row in results:
            logger.info(f"✅ Query successful! Table has {row.row_count} rows.")
        
        # Get available years
        years_query = f"""
        SELECT DISTINCT Vuosi as year
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        ORDER BY year
        """
        
        logger.info("Checking available years...")
        years_job = client.query(years_query)
        years_results = years_job.result()
        
        years = [row.year for row in years_results]
        logger.info(f"✅ Available years: {years}")
        
        return True
    except Exception as e:
        logger.error(f"❌ BigQuery test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_bigquery_connection()
    sys.exit(0 if success else 1)