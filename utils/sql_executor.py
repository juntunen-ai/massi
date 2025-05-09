"""
SQL executor for running BigQuery queries and returning results
"""

import logging
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from typing import Optional, Dict, Any, Union
from utils.secrets_manager import secrets_manager
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Use centralized secrets manager for API key retrieval
api_key = secrets_manager.get_api_key_ai_studio()
if not hasattr(genai, '_configured'):
    genai.configure(api_key=api_key)
    genai._configured = True

class SQLExecutor:
    """Class for executing SQL queries against BigQuery."""
    
    def __init__(self, project_id: str):
        """
        Initialize the SQL executor.
        
        Args:
            project_id (str): Google Cloud project ID
        """
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        
    def execute_query(self, sql_query: str, max_results: int = 10000) -> Optional[pd.DataFrame]:
        """
        Execute a SQL query and return results as DataFrame.
        
        Args:
            sql_query (str): SQL query to execute
            max_results (int): Maximum number of results to return
            
        Returns:
            Optional[pd.DataFrame]: Query results as DataFrame or None if query failed
        """
        try:
            # Sanitize SQL for Finnish characters
            sql_query = self._sanitize_sql(sql_query)
            
            logger.info(f"Executing SQL query: {sql_query}")
            
            # Configure query job
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True
            )
            
            # Run the query
            query_job = self.client.query(sql_query, job_config=job_config)
            
            # Get the results
            results = query_job.result(max_results=max_results)
            
            # Convert to DataFrame
            df = results.to_dataframe()
            
            logger.info(f"Query executed successfully. Returned {len(df)} rows.")
            return df
            
        except GoogleAPIError as e:
            logger.error(f"BigQuery API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return None
            
    def get_query_info(self, sql_query: str) -> Dict[str, Any]:
        """
        Get information about a query without executing it.
        
        Args:
            sql_query (str): SQL query to analyze
            
        Returns:
            Dict[str, Any]: Information about the query
        """
        try:
            # Configure dry run job
            job_config = bigquery.QueryJobConfig(
                dry_run=True,
                use_query_cache=False
            )
            
            # Start job
            query_job = self.client.query(sql_query, job_config=job_config)
            
            # Return info
            return {
                "bytes_processed": query_job.total_bytes_processed,
                "estimated_cost_usd": query_job.total_bytes_processed / (1024**4) * 5,  # Approx. $5 per TB
                "is_cached": query_job.cache_hit
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query: {str(e)}")
            return {
                "error": str(e)
            }
    
    def execute_query_with_parameters(self, sql_query: str, 
                                      params: Dict[str, Union[str, int, float, bool]], 
                                      max_results: int = 10000) -> Optional[pd.DataFrame]:
        """
        Execute a parametrized SQL query.
        
        Args:
            sql_query (str): SQL query with parameters
            params (Dict[str, Union[str, int, float, bool]]): Parameter values
            max_results (int): Maximum number of results to return
            
        Returns:
            Optional[pd.DataFrame]: Query results as DataFrame or None if query failed
        """
        try:
            logger.info(f"Executing parametrized SQL query: {sql_query}")
            
            # Configure parametrized query
            job_config = bigquery.QueryJobConfig(
                use_query_cache=True,
                query_parameters=[
                    bigquery.ScalarQueryParameter(name, self._get_param_type(value), value)
                    for name, value in params.items()
                ]
            )
            
            # Run the query
            query_job = self.client.query(sql_query, job_config=job_config)
            
            # Get the results
            results = query_job.result(max_results=max_results)
            
            # Convert to DataFrame
            df = results.to_dataframe()
            
            logger.info(f"Parametrized query executed successfully. Returned {len(df)} rows.")
            return df
            
        except GoogleAPIError as e:
            logger.error(f"BigQuery API error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error executing parametrized query: {str(e)}")
            return None
    
    def _get_param_type(self, value: Union[str, int, float, bool]) -> str:
        """
        Get BigQuery parameter type for a Python value.
        
        Args:
            value: Python value
            
        Returns:
            str: BigQuery parameter type
        """
        if isinstance(value, str):
            return 'STRING'
        elif isinstance(value, bool):
            return 'BOOL'
        elif isinstance(value, int):
            return 'INT64'
        elif isinstance(value, float):
            return 'FLOAT64'
        else:
            return 'STRING'  # Default to string

    def _sanitize_sql(self, sql_query: str) -> str:
        """
        Sanitize SQL query for Finnish characters and type mismatches.
        
        Args:
            sql_query (str): SQL query
            
        Returns:
            str: Sanitized SQL query
        """
        # Ensure Finnish columns are properly escaped
        finnish_columns = {
            'Alkuperäinen_talousarvio': '`Alkuperäinen_talousarvio`',
            'Voimassaoleva_talousarvio': '`Voimassaoleva_talousarvio`',
            'Nettokertymä': '`Nettokertymä`',
            'Käytettävissä': '`Käytettävissä`',
            'Loppusaldo': '`Loppusaldo`'
        }
        
        for col, quoted_col in finnish_columns.items():
            # Replace unquoted references
            sql_query = sql_query.replace(f' {col} ', f' {quoted_col} ')
            sql_query = sql_query.replace(f'.{col} ', f'.{quoted_col} ')
            sql_query = sql_query.replace(f'({col})', f'({quoted_col})')
        
        return sql_query