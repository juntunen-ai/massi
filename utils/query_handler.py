import logging
from .nl_to_sql import NLToSQLConverter
from .real_data_provider import RealDataProvider
from .bigquery_schema import get_bigquery_schema

schema_service = get_bigquery_schema()

logger = logging.getLogger(__name__)

class QueryHandler:
    def __init__(self, config):
        self.nl_converter = NLToSQLConverter()
        self.data_provider = RealDataProvider(project_id="massi-financial-analysis", 
                                              dataset_id="finnish_finance_data", 
                                              table_id="budget_transactions")
        self.schema = get_bigquery_schema()
    
    def process_query(self, query: str):
        """Process a natural language query end-to-end."""
        try:
            # Convert to SQL
            sql, explanation = self.nl_converter.generate_sql(query)
            
            # Execute SQL
            result = self.data_provider.execute_query(sql)
            
            return {
                'sql': sql,
                'explanation': explanation,
                'result': result
            }
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}", exc_info=True)
            raise