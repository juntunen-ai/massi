import json
import os

def get_table_schema():
    """Load schema from JSON file as dictionaries."""
    schema_path = os.path.join('data', 'schema.json')
    with open(schema_path, 'r') as f:
        return json.load(f)