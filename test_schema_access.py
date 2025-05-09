import unittest

class TestSchemaAccess(unittest.TestCase):
    """Test how schema is accessed in the application."""
    
    def test_centralized_schema_access(self):
        """Test accessing schema through the centralized method."""
        from utils.bigquery_schema import get_bigquery_schema
        
        # Test that the schema function works
        schema = get_bigquery_schema()
        
        self.assertIsNotNone(schema)
        self.assertIsInstance(schema, list)
        self.assertGreater(len(schema), 0)
        
        print(f"Schema loaded successfully with {len(schema)} fields")
        
        # Show some field information
        for i, field in enumerate(schema[:3]):  # Show first 3 fields
            print(f"Field {i+1}: {field.name} ({field.field_type})")
    
    def test_schema_service_pattern(self):
        """Test if a schema service pattern exists in the code."""
        
        # Check if there's a schema service module
        try:
            # Look for schema service imports in modules
            import utils
            
            # Try to find schema_service
            has_schema_service = hasattr(utils, 'schema_service')
            print(f"Utils has schema_service: {has_schema_service}")
            
            # Check what's available in utils
            utils_contents = dir(utils)
            print(f"Utils module contents: {utils_contents}")
            
            # Specifically look for schema-related attributes
            schema_related = [item for item in utils_contents if 'schema' in item.lower()]
            if schema_related:
                print(f"Schema-related items in utils: {schema_related}")
            else:
                print("No schema-related items found in utils")
                
        except Exception as e:
            print(f"Error exploring schema service: {e}")
    
    def test_find_schema_service_reference(self):
        """Try to find where schema_service is referenced."""
        import os
        import re
        
        # Search through Python files for schema_service references
        project_dir = os.path.dirname(os.path.abspath(__file__))
        schema_service_refs = []
        
        for root, dirs, files in os.walk(project_dir):
            # Skip virtual environment and other unnecessary directories
            if '.venv' in root or '__pycache__' in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            # Search for schema_service
                            matches = re.finditer(r'schema_service', content)
                            for match in matches:
                                # Get context around the match
                                start = max(0, match.start() - 50)
                                end = min(len(content), match.end() + 50)
                                context = content[start:end]
                                line_num = content[:match.start()].count('\n') + 1
                                
                                schema_service_refs.append({
                                    'file': file_path,
                                    'line': line_num,
                                    'context': context
                                })
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        # Print the results
        if schema_service_refs:
            print(f"Found {len(schema_service_refs)} references to schema_service:")
            for ref in schema_service_refs:
                print(f"\nFile: {ref['file']}")
                print(f"Line: {ref['line']}")
                print(f"Context: ...{ref['context']}...")
        else:
            print("No references to schema_service found")

if __name__ == "__main__":
    unittest.main()