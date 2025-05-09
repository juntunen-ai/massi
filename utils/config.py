"""
Centralized configuration management for the Finnish Government Budget Explorer.
"""

import os
import json
from dotenv import load_dotenv
from .auth import GoogleCloudAuth

# Load environment variables once at import
load_dotenv()

# Application configuration
PROJECT_ID = os.getenv('PROJECT_ID', 'massi-financial-analysis')
DATASET_ID = os.getenv('DATASET_ID', 'finnish_finance_data')
TABLE_ID = os.getenv('TABLE_ID', 'budget_transactions')
REGION = os.getenv('REGION', 'europe-west4')
MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-1.5-pro')
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Add authentication check
def check_authentication() -> bool:
    """Check if properly authenticated for Google Cloud."""
    auth = GoogleCloudAuth()
    return auth.is_authenticated()

# Add to the config file
def get_authenticated_project_id() -> str:
    """Get the authenticated project ID."""
    auth = GoogleCloudAuth()
    _, project_id = auth.get_credentials()
    return project_id or PROJECT_ID

def get_schema() -> list:
    """Load schema from data/schema.json file."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'schema.json')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # Convert BigQuery schema format to our expected format
        schema = []
        for field in schema_data:
            schema.append({
                "name": field["name"],
                "type": field["type"],
                "description": field.get("description", "")
            })
        
        return schema
    except Exception as e:
        print(f"Error loading schema: {e}")
        # Fallback to basic schema if file not found
        return [
            {"name": "Vuosi", "type": "INTEGER", "description": "Year"},
            {"name": "Kk", "type": "INTEGER", "description": "Month"},
            {"name": "Ha_Tunnus", "type": "INTEGER", "description": "Administrative branch code"},
            {"name": "Hallinnonala", "type": "STRING", "description": "Administrative branch name"},
        ]