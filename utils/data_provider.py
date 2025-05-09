"""
Real data provider for connecting to BigQuery.
"""

import pandas as pd
import logging
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from typing import Optional, List
from utils.secrets_manager import secrets_manager
import google.generativeai as genai
from schema_service import schema_service
from utils.errors import BigQueryError
from utils.config import PROJECT_ID, DATASET_ID, TABLE_ID
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Use centralized secrets manager for API key retrieval
api_key = secrets_manager.get_api_key_ai_studio()
genai.configure(api_key=api_key)

class DataProvider:
    """Provides real financial data from BigQuery."""

    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        """Initialize the data provider."""
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.client = bigquery.Client(project=project_id)
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"

    def execute_query(self, query: str) -> Optional[pd.DataFrame]:
        """
        Execute a SQL query and return results.

        Args:
            query (str): SQL query to execute

        Returns:
            Optional[pd.DataFrame]: Results DataFrame or None if query fails
        """
        try:
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
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
        return None

    def generate_example_data(self, query_type: str) -> pd.DataFrame:
        """
        Generate example data for specific query types.

        Args:
            query_type (str): Type of query

        Returns:
            pd.DataFrame: Example data
        """
        queries = {
            'military_budget_2022': """
                SELECT 
                  SUM(`Alkuperäinen_talousarvio`) as original_budget,
                  SUM(`Voimassaoleva_talousarvio`) as current_budget
                FROM 
                  `{table_ref}`
                WHERE 
                  Vuosi = 2022 
                  AND Ha_Tunnus = 26
            """,
            'defense_quarterly_2022_2023': """
                SELECT 
                  Vuosi as year,
                  CEIL(Kk/3) as quarter,
                  SUM(`Voimassaoleva_talousarvio`) as budget,
                  SUM(`Nettokertymä`) as spending
                FROM 
                  `{table_ref}`
                WHERE 
                  Vuosi IN (2022, 2023)
                  AND Ha_Tunnus = 26
                GROUP BY 
                  year, quarter
                ORDER BY 
                  year, quarter
            """,
            'education_budget_trend': """
                SELECT 
                  Vuosi as year,
                  SUM(`Alkuperäinen_talousarvio`) as original_budget,
                  SUM(`Voimassaoleva_talousarvio`) as current_budget,
                  SUM(`Nettokertymä`) as spending
                FROM 
                  `{table_ref}`
                WHERE 
                  Vuosi BETWEEN 2020 AND 2023
                  AND Ha_Tunnus = 29
                GROUP BY 
                  year
                ORDER BY 
                  year
            """,
            'top_ministries_2023': """
                SELECT 
                  Hallinnonala as ministry,
                  SUM(`Nettokertymä`) as spending
                FROM 
                  `{table_ref}`
                WHERE 
                  Vuosi = 2023
                GROUP BY 
                  ministry
                ORDER BY 
                  spending DESC
                LIMIT 5
            """
        }

        query = queries.get(query_type)
        if query:
            query = query.format(table_ref=self.table_ref)
            return self.execute_query(query) or pd.DataFrame()
        return pd.DataFrame()

    def get_available_years(self) -> List[int]:
        """Get available years in the data."""
        query = f"""
        SELECT DISTINCT Vuosi 
        FROM `{self.table_ref}`
        ORDER BY Vuosi
        """
        result = self.execute_query(query)
        if result is not None and not result.empty:
            return result['Vuosi'].tolist()
        return []

    def close(self):
        """Close the BigQuery client."""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("BigQuery client connection closed")