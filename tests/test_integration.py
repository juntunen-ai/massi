import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.schema_service import schema_service  # Use the singleton
from utils.query_handler import QueryHandler
from utils.config_service import config

def test_schema_loading():
    schema_dict = schema_service.get_schema_dict()
    assert isinstance(schema_dict, list)
    assert len(schema_dict) > 0
    assert 'name' in schema_dict[0]
    print("✓ Schema loading test passed")

def test_query_handler():
    handler = QueryHandler(config=config)
    result = handler.process_query("What was the defense budget in 2022?")
    assert 'sql' in result
    assert 'explanation' in result
    assert result['sql'] is not None
    print("✓ Query handler test passed")

if __name__ == "__main__":
    test_schema_loading()
    test_query_handler()
    print("All tests passed!")