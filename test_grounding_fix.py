import unittest
import os

class TestGroundingFix(unittest.TestCase):
    """Test that the schema fix resolves the issue."""
    
    def test_app_initialization_with_schema(self):
        """Test that FinancialDataApp initializes with schema."""
        from app import FinancialDataApp
        
        try:
            app = FinancialDataApp()
            
            # Check if schema attribute exists
            self.assertTrue(hasattr(app, 'schema'), "App should have schema attribute")
            
            # Check if schema is not None
            self.assertIsNotNone(app.schema, "Schema should not be None")
            
            # Check if schema has expected structure
            self.assertIsInstance(app.schema, list, "Schema should be a list")
            self.assertGreater(len(app.schema), 0, "Schema should not be empty")
            
            print(f"Schema loaded successfully with {len(app.schema)} fields")
            
        except Exception as e:
            self.fail(f"App initialization failed: {e}")
    
    def test_handle_query_without_schema_error(self):
        """Test that handle_query doesn't crash due to missing schema."""
        from app import FinancialDataApp
        
        try:
            app = FinancialDataApp()
            
            # Test that handle_query doesn't crash with schema error
            test_query = "What was the military budget for 2022?"
            
            # We expect it might still fail on grounding, but not on schema
            try:
                app.handle_query(test_query)
            except AttributeError as e:
                self.fail(f"Schema error still present: {e}")
            except Exception as e:
                # Other errors are acceptable for now
                print(f"Query failed with non-schema error: {e}")
                
        except Exception as e:
            self.fail(f"Test setup failed: {e}")

if __name__ == "__main__":
    unittest.main()