import json
import os
from typing import Dict, List, Any
from functools import lru_cache
from google.cloud import bigquery
from .bigquery_schema import get_bigquery_schema

class SchemaService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._schema_dict = None
            cls._instance._schema_objects = None  # Corrected: assign to the instance
        return cls._instance

    @lru_cache(maxsize=1)
    def get_schema_dict(self) -> List[Dict[str, Any]]:
        """Get schema as a list of dictionaries."""
        if self._schema_dict is None:
            schema_path = os.path.join('data', 'schema.json')
            with open(schema_path, 'r') as f:
                self._schema_dict = json.load(f)
        return self._schema_dict

    @lru_cache(maxsize=1)  
    def get_schema_objects(self) -> List[bigquery.SchemaField]:
        """Get schema as BigQuery SchemaField objects."""
        if self._schema_objects is None:
            schema_dict = self.get_schema_dict()
            self._schema_objects = [
                bigquery.SchemaField(
                    name=field['name'],
                    field_type=field['type'],
                    mode=field.get('mode', 'NULLABLE'),
                    description=field.get('description', '')
                )
                for field in schema_dict
            ]
        return self._schema_objects

# Create singleton instance
schema_service = SchemaService()