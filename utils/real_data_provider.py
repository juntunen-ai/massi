import logging
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from typing import Optional

logger = logging.getLogger(__name__)

class RealDataProvider:
    def __init__(self, project_id: str = "massi-financial-analysis", 
                 dataset_id: str = "finnish_finance_data", 
                 table_id: str = "budget_transactions"):
        """Initialize the real data provider."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        # Log startup with note about API being disabled
        logger.info("Initialized RealDataProvider - API access is disabled, using pre-loaded BigQuery data")

    def _prepare_sql_query(self, query: str) -> str:
        """
        Prepare a SQL query by properly handling Finnish characters.
        
        Args:
            query (str): Original SQL query
            
        Returns:
            str: Prepared SQL query
        """
        # List of column names with Finnish characters
        finnish_columns = [
            "Nettokertymä",
            "Lisätalousarvio",
            "Käytettävissä",
            "Kirjanpitoyksikkö",
            "Loppusaldo"
        ]
        
        # Add backticks to Finnish column names
        for col in finnish_columns:
            # Only replace if not already backticked
            if f"`{col}`" not in query and col in query:
                query = query.replace(col, f"`{col}`")
        
        return query

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute a SQL query and return results.
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            Optional[pd.DataFrame]: Results DataFrame or None if query fails
        """
        try:
            # Prepare the query by handling Finnish characters
            query = self._prepare_sql_query(query)
            
            logger.info(f"Executing query: {query[:100]}...")
            
            # Configure query job
            job_config = bigquery.QueryJobConfig(use_query_cache=True)
            
            # Run the query
            query_job = self.client.query(query, job_config=job_config)
            
            # Get the results
            results = query_job.result()
            
            # Convert to DataFrame
            df = results.to_dataframe()
            
            logger.info(f"Query returned {len(df)} rows")
            return df
            
        except GoogleAPIError as e:
            logger.error(f"BigQuery API error: {str(e)}")
            logger.error(f"Query that failed: {query}")
            return None
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            logger.error(f"Query that failed: {query}")
            return None

    def get_schema(self) -> list:
        """Get the schema of the BigQuery table."""
        query = f"""
        SELECT column_name, data_type
        FROM `{self.project_id}.{self.dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{self.table_id}'
        """
        try:
            result = self.execute_query(query)
            if result is not None and not result.empty:
                return [{"name": row["column_name"], "type": row["data_type"]} 
                        for _, row in result.iterrows()]
            # Fallback to hardcoded schema if query fails
            return [
                {"name": "Vuosi", "type": "INTEGER"},
                {"name": "Kk", "type": "INTEGER"},
                {"name": "Ha_Tunnus", "type": "INTEGER"},
                {"name": "Hallinnonala", "type": "STRING"},
                {"name": "Alkuperäinen_talousarvio", "type": "FLOAT"},
                {"name": "Voimassaoleva_talousarvio", "type": "FLOAT"},
                {"name": "Nettokertymä", "type": "FLOAT"}
            ]
        except Exception as e:
            logger.error(f"Error getting schema: {str(e)}")
            return []

    def get_available_years(self) -> list:
        """Get available years in the data from BigQuery (not from API)."""
        query = f"""
        SELECT DISTINCT Vuosi 
        FROM `{self.table_ref}`
        ORDER BY Vuosi
        """
        result = self.execute_query(query)
        if result is not None and not result.empty:
            return result['Vuosi'].tolist()
        return [2020, 2021, 2022, 2023, 2024]  # Fallback to default years if query fails