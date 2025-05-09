import os
from utils.config import PROJECT_ID, DATASET_ID, TABLE_ID
from google.cloud import bigquery, secretmanager
import json
import google.auth
import subprocess
import logging
import sys
from utils.bigquery_loader import BigQueryLoader

# Project details
project_id = PROJECT_ID
dataset_id = DATASET_ID
table_id = TABLE_ID
secret_id = os.getenv('SECRET_ID', 'massi-service-account-key')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

# Configuration
PROJECT_ID = "massi-financial-analysis"
DATASET_ID = "finnish_finance_data"
TABLE_ID = "budget_transactions"
LOCATION = "EU"  # Set to EU for Finnish data

def run_command(cmd, check=True):
    """Run a shell command and log the output."""
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"Command succeeded: {result.stdout}")
        return True, result.stdout
    else:
        error_msg = f"Command failed (exit code {result.returncode}): {result.stderr}"
        logger.error(error_msg)
        if check:
            raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
        return False, error_msg

def check_gcloud_auth():
    """Check if gcloud is authenticated."""
    logger.info("Checking gcloud authentication...")
    try:
        success, output = run_command(["gcloud", "auth", "list"])
        if "No credentialed accounts" in output:
            logger.error("No credentialed accounts found. Please run 'gcloud auth login'")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking gcloud auth: {str(e)}")
        return False

def create_dataset():
    """Create BigQuery dataset if it doesn't exist."""
    logger.info(f"Creating dataset {DATASET_ID} in project {PROJECT_ID}...")
    try:
        # Check if dataset exists
        success, output = run_command(
            ["bq", "ls", f"--project_id={PROJECT_ID}", f"{PROJECT_ID}:{DATASET_ID}"], 
            check=False
        )
        
        if success:
            logger.info(f"Dataset {DATASET_ID} already exists")
            return True
        
        # Create dataset
        success, output = run_command([
            "bq", "mk", 
            "--dataset", 
            f"--location={LOCATION}", 
            f"--description=Finnish government financial data",
            f"{PROJECT_ID}:{DATASET_ID}"
        ])
        
        return success
    except Exception as e:
        logger.error(f"Error creating dataset: {str(e)}")
        return False

# Add a function to create a table using a schema file
def create_table_with_schema_file():
    """Create BigQuery table using a schema file."""
    logger.info(f"Creating table {TABLE_ID} in dataset {DATASET_ID} using schema file...")
    try:
        schema_file_path = os.path.join(os.getcwd(), 'data', 'schema.json')

        # Check if table exists
        success, output = run_command(
            ["bq", "show", f"--project_id={PROJECT_ID}", f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}"], 
            check=False
        )

        if success:
            logger.info(f"Table {TABLE_ID} already exists")
            return True

        # Create table using schema file
        success, output = run_command([
            "bq", "mk", 
            "--table", 
            f"--time_partitioning_field=Vuosi", 
            f"--clustering_fields=Ha_Tunnus,Momentti_TunnusP",
            f"{PROJECT_ID}:{DATASET_ID}.{TABLE_ID}", 
            schema_file_path
        ])

        return success
    except Exception as e:
        logger.error(f"Error creating table with schema file: {str(e)}")
        return False

def update_env_file():
    """Update .env file with configuration."""
    logger.info("Updating .env file...")
    try:
        with open(".env", "w") as f:
            f.write(f"# Google Cloud project info\n")
            f.write(f"PROJECT_ID={PROJECT_ID}\n")
            f.write(f"DATASET_ID={DATASET_ID}\n")
            f.write(f"TABLE_ID={TABLE_ID}\n\n")
            f.write(f"# Vertex AI settings\n")
            f.write(f"REGION=europe-west4\n")
            f.write(f"MODEL_NAME=gemini-1.5-pro\n\n")
            f.write(f"# Application settings\n")
            f.write(f"DEBUG_MODE=True\n")
            f.write(f"LOG_LEVEL=INFO\n")
        
        logger.info(".env file updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating .env file: {str(e)}")
        return False

# Update the main function to use the new table creation method
def main():
    logger.info("Setting up BigQuery infrastructure...")
    
    # Check gcloud authentication
    if not check_gcloud_auth():
        logger.error("Please authenticate with gcloud first: gcloud auth login")
        return False
    
    # Create dataset
    if not create_dataset():
        logger.error("Failed to create dataset")
        return False
    
    # Create table using schema file
    if not create_table_with_schema_file():
        logger.error("Failed to create table")
        return False
    
    # Update .env file
    if not update_env_file():
        logger.error("Failed to update .env file")
        return False
    
    logger.info("BigQuery setup completed successfully!")
    logger.info(f"Project: {PROJECT_ID}")
    logger.info(f"Dataset: {DATASET_ID}")
    logger.info(f"Table: {TABLE_ID}")
    
    return True

def get_bigquery_client():
    """Get an authenticated BigQuery client using the best available credentials."""
    try:
        # First try to use application default credentials
        credentials, detected_project = google.auth.default()
        if not project_id:
            project = detected_project
        else:
            project = project_id

        client = bigquery.Client(credentials=credentials, project=project)
        print("Successfully authenticated using application default credentials")
        return client
    except Exception as e:
        print(f"Could not use application default credentials: {str(e)}")

        # Try using Secret Manager
        try:
            secret_client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = secret_client.access_secret_version(request={"name": name})
            service_account_key_json = response.payload.data.decode("UTF-8")
            service_account_info = json.loads(service_account_key_json)

            client = bigquery.Client.from_service_account_info(service_account_info)
            print("Successfully authenticated using Secret Manager credentials")
            return client
        except Exception as secret_e:
            print(f"Error retrieving credentials from Secret Manager: {str(secret_e)}")

            # Fall back to project ID only, which may work if running in a GCP environment
            print("Falling back to project ID only authentication")
            return bigquery.Client(project=project_id)

def setup_bigquery_infrastructure():
    """Set up BigQuery dataset and table for Finnish financial data."""

    # Get authenticated client
    client = get_bigquery_client()

    # Create dataset
    dataset_ref = f"{project_id}.{dataset_id}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "EU"  # Set to EU for Finnish data
    dataset.description = "Finnish government financial data"

    try:
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"Dataset {dataset_ref} created/confirmed successfully")
    except Exception as e:
        print(f"Dataset creation error: {str(e)}")
        return

    # Define table schema
    schema = [
        # Date fields
        bigquery.SchemaField("Vuosi", "INTEGER", description="Year"),
        bigquery.SchemaField("Kk", "INTEGER", description="Month"),

        # Administrative structure
        bigquery.SchemaField("Ha_Tunnus", "INTEGER", description="Administrative branch code"),
        bigquery.SchemaField("Hallinnonala", "STRING", description="Administrative branch name"),
        bigquery.SchemaField("Tv_Tunnus", "INTEGER", description="Accounting unit code"),
        bigquery.SchemaField("Kirjanpitoyksikkö", "STRING", description="Accounting unit name"),

        # Budget structure
        bigquery.SchemaField("PaaluokkaOsasto_TunnusP", "STRING", description="Main class/section code"),
        bigquery.SchemaField("PaaluokkaOsasto_sNimi", "STRING", description="Main class/section name"),
        bigquery.SchemaField("Luku_TunnusP", "STRING", description="Chapter code"),
        bigquery.SchemaField("Luku_sNimi", "STRING", description="Chapter name"),
        bigquery.SchemaField("Momentti_TunnusP", "STRING", description="Moment code"),
        bigquery.SchemaField("Momentti_sNimi", "STRING", description="Moment name"),
        bigquery.SchemaField("TakpT_TunnusP", "STRING", description="Budget account code"),
        bigquery.SchemaField("TakpT_sNimi", "STRING", description="Budget account name"),
        bigquery.SchemaField("TakpTr_sNimi", "STRING", description="Budget account group name"),

        # Accounting structure
        bigquery.SchemaField("Tililuokka_Tunnus", "STRING", description="Account class code"),
        bigquery.SchemaField("Tililuokka_sNimi", "STRING", description="Account class name"),
        bigquery.SchemaField("Ylatiliryhma_Tunnus", "STRING", description="Parent account group code"),
        bigquery.SchemaField("Ylatiliryhma_sNimi", "STRING", description="Parent account group name"),
        bigquery.SchemaField("Tiliryhma_Tunnus", "STRING", description="Account group code"),
        bigquery.SchemaField("Tiliryhma_sNimi", "STRING", description="Account group name"),
        bigquery.SchemaField("Tililaji_Tunnus", "STRING", description="Account type code"),
        bigquery.SchemaField("Tililaji_sNimi", "STRING", description="Account type name"),
        bigquery.SchemaField("LkpT_Tunnus", "STRING", description="Business accounting code"),
        bigquery.SchemaField("LkpT_sNimi", "STRING", description="Business accounting name"),

        # Financial values
        bigquery.SchemaField("Alkuperäinen_talousarvio", "FLOAT", description="Original budget"),
        bigquery.SchemaField("Lisätalousarvio", "FLOAT", description="Supplementary budget"),
        bigquery.SchemaField("Voimassaoleva_talousarvio", "FLOAT", description="Current budget"),
        bigquery.SchemaField("Käytettävissä", "FLOAT", description="Available"),
        bigquery.SchemaField("Alkusaldo", "FLOAT", description="Opening balance"),
        bigquery.SchemaField("Nettokertymä_ko_vuodelta", "FLOAT", description="Net accumulation for the year"),
        bigquery.SchemaField("NettoKertymaAikVuosSiirrt", "FLOAT", description="Net accumulation from previous years"),
        bigquery.SchemaField("Nettokertymä", "FLOAT", description="Net accumulation total"),
        bigquery.SchemaField("Loppusaldo", "FLOAT", description="Closing balance")
    ]

    # Create table with schema
    table_ref = f"{dataset_ref}.{table_id}"
    table = bigquery.Table(table_ref, schema=schema)

    # Add partitioning by year for better query performance
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.YEAR,
        field="Vuosi"  # Partition by year
    )

    # Add clustering for common query patterns
    table.clustering_fields = ["Ha_Tunnus", "Momentti_TunnusP"]

    try:
        table = client.create_table(table, exists_ok=True)
        print(f"Table {table_ref} created/confirmed successfully")
        print(f"Full path to the table: {project_id}.{dataset_id}.{table_id}")
    except Exception as e:
        print(f"Table creation error: {str(e)}")

def initialize_bigquery():
    """Initialize BigQuery dataset and table"""
    # Configuration
    project_id = "massi-financial-analysis"
    dataset_id = "finnish_finance_data"
    table_id = "budget_transactions"
    
    logger.info("Initializing BigQuery resources...")
    
    # Create loader instance
    loader = BigQueryLoader(project_id, dataset_id, table_id)
    
    # Create dataset if it doesn't exist
    logger.info("Creating dataset if it doesn't exist...")
    loader.create_dataset_if_not_exists()
    
    # Create table if it doesn't exist
    logger.info("Creating table if it doesn't exist...")
    loader.create_table_if_not_exists()
    
    logger.info("BigQuery initialization complete!")

if __name__ == "__main__":
    # Unset credentials env var to use application default credentials
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        logger.info("Unsetting GOOGLE_APPLICATION_CREDENTIALS to use application default credentials")
        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    
    initialize_bigquery()
    setup_bigquery_infrastructure()
    success = main()
    sys.exit(0 if success else 1)