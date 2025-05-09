class FinancialDataError(Exception):
    """Base exception for the Financial Data Explorer."""
    pass

class APIError(FinancialDataError):
    """Error in API communication."""
    pass

class BigQueryError(FinancialDataError):
    """Error in BigQuery operations."""
    pass

class SQLGenerationError(FinancialDataError):
    """Error in SQL generation from natural language."""
    pass

class DataProcessingError(FinancialDataError):
    """Error in data processing or transformation."""
    pass