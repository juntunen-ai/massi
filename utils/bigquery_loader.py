import logging
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from typing import Optional
from utils.bigquery_schema import get_bigquery_schema

logger = logging.getLogger(__name__)

class BigQueryLoader:
    """Class for loading Finnish government finance data into BigQuery."""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """
        Initialize BigQuery loader.
        
        Args:
            project_id (str): Google Cloud project ID
            dataset_id (str): BigQuery dataset ID
            table_id (str): BigQuery table ID
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    def create_dataset_if_not_exists(self) -> None:
        """Create the dataset if it doesn't exist."""
        try:
            self.client.get_dataset(self.dataset_id)
            logger.info(f"Dataset {self.dataset_id} already exists")
        except Exception:
            # Dataset does not exist, create it
            dataset = bigquery.Dataset(f"{self.project_id}.{self.dataset_id}")
            dataset.location = "EU"  # Set to appropriate location for Finnish data
            dataset = self.client.create_dataset(dataset)
            logger.info(f"Dataset {self.dataset_id} created")
    
    def create_table_if_not_exists(self) -> None:
        """Create the table if it doesn't exist with the appropriate schema."""
        try:
            self.client.get_table(self.table_ref)
            logger.info(f"Table {self.table_id} already exists")
        except Exception:
            # Table does not exist, create it
            schema = get_bigquery_schema()
            table = bigquery.Table(self.table_ref, schema=schema)
            
            # Add date partitioning by YearMonth
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.MONTH,
                field="YearMonth"  # Partition by the new DATE field
            )
            
            # Add clustering for common query patterns
            table.clustering_fields = ["Ha_Tunnus", "Momentti_TunnusP"]
            
            table = self.client.create_table(table)
            logger.info(f"Table {self.table_id} created with schema")
    
    def load_dataframe(self, df: pd.DataFrame, write_disposition: str = "WRITE_APPEND") -> Optional[str]:
        """
        Load a DataFrame into BigQuery.
        
        Args:
            df (pd.DataFrame): DataFrame to load
            write_disposition (str): BigQuery write disposition (WRITE_APPEND, WRITE_TRUNCATE, or WRITE_EMPTY)
            
        Returns:
            Optional[str]: Job ID if successful, None if failed
        """
        try:
            # Handle any data cleaning or transformation
            # Remove preprocessing to create the YearMonth field
            # if 'Vuosi' in df.columns and 'Kk' in df.columns:
            #     df['YearMonth'] = pd.to_datetime(df['Vuosi'].astype(str) + '-' + df['Kk'].astype(str).str.zfill(2) + '-01')
            
            # Convert numeric columns to strings where needed based on schema
            df['Tililuokka_Tunnus'] = df['Tililuokka_Tunnus'].astype(str)
            
            # Add conversion for LkpT_Tunnus as well
            df['LkpT_Tunnus'] = df['LkpT_Tunnus'].astype(str)
            
            # Handle type conversions for problematic columns
            type_conversion_columns = ['Tililuokka_Tunnus', 'LkpT_Tunnus', 'PaaluokkaOsasto_TunnusP', 
                                      'Luku_TunnusP', 'Momentti_TunnusP', 'TakpT_TunnusP', 
                                      'Ylatiliryhma_Tunnus', 'Tiliryhma_Tunnus', 'Tililaji_Tunnus']
            for col in type_conversion_columns:
                if col in df.columns and df[col].dtype != 'object':
                    df[col] = df[col].fillna('').astype(str)
            
            # Convert NaN values to None for proper NULL handling in BigQuery
            df = df.where(pd.notnull(df), None)
            
            # Load the data
            job_config = bigquery.LoadJobConfig(
                schema=get_bigquery_schema(),
                write_disposition=write_disposition
            )
            
            job = self.client.load_table_from_dataframe(df, self.table_ref, job_config=job_config)
            job.result()  # Wait for the job to complete
            
            logger.info(f"Loaded {len(df)} rows into {self.table_ref}")
            return job.job_id
            
        except GoogleAPIError as e:
            logger.error(f"BigQuery API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error loading data to BigQuery: {str(e)}")
            return None