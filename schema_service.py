"""
Schema service for Finnish government financial data.
Provides the BigQuery schema definition for the budget transactions table.
"""

from utils.bigquery_schema import get_bigquery_schema

# Initialize the schema
schema_service = get_bigquery_schema()