# test_grounding.py
import unittest
import os
from unittest.mock import patch, MagicMock
import sys
import logging
import json

# Set up logging to capture output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestGroundingFeature(unittest.TestCase):
    """Test cases for grounding feature."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables if needed
        os.environ['PROJECT_ID'] = 'massi-financial-analysis'
        os.environ['DATASET_ID'] = 'finnish_finance_data'
        os.environ['TABLE_ID'] = 'budget_transactions'
    
    def test_grounding_disabled(self):
        """Test that grounding returns None when the feature flag is disabled."""
        from app import FinancialDataApp
        
        # Create app instance and disable grounding
        app = FinancialDataApp()
        if hasattr(app, 'use_grounding'):
            app.use_grounding = False
            
        # Test query
        test_query = "What was the military budget for 2022?"
        
        # Mock grounded processing
        with patch.object(app, '_process_grounded_query') as mock_process:
            result = getattr(app, '_process_grounded_query', lambda x: None)(test_query)
            
            # With grounding disabled, should return None
            self.assertIsNone(result)
    
    def test_grounding_enabled_with_error_logging(self):
        """Test that grounding is processed when the feature flag is enabled."""
        from app import FinancialDataApp
        
        app = FinancialDataApp()
        
        # Test query
        test_query = "What was the military budget for 2022?"
        
        try:
            # Enable grounding if possible
            if hasattr(app, 'use_grounding'):
                app.use_grounding = True
            
            # If grounded_query_processor exists, import and test directly
            try:
                from utils.grounded_query_processor import process_grounded_query
                
                print(f"\nTesting query: '{test_query}'")
                
                # Try to process the query
                result = process_grounded_query(test_query)
                
                print(f"Result type: {type(result)}")
                print(f"Result value: {result}")
                
                # Log more details about what we got
                if result is None:
                    print("Result is None - checking for errors in logs")
                    # Log the last few log entries if possible
                    if hasattr(logger, 'handlers'):
                        for handler in logger.handlers:
                            if hasattr(handler, 'baseFilename'):
                                print(f"Check log file: {handler.baseFilename}")
                
                # Even if it returns None, we want to understand why
                self.assertIsNotNone(result, "Grounding returned None - check logs for errors")
                
            except Exception as e:
                error_type = type(e).__name__
                error_message = str(e)
                
                print(f"\nError occurred:")
                print(f"Type: {error_type}")
                print(f"Message: {error_message}")
                
                # Check for specific error patterns
                if "Search Grounding is not supported" in error_message:
                    print("\nDIAGNOSIS: Search Grounding feature is not enabled")
                    print("This is a known issue - the API doesn't support this feature")
                    self.skipTest(f"Search Grounding not supported: {error_message}")
                elif "400" in error_message:
                    print("\nDIAGNOSIS: API returned 400 error")
                    print("Possible causes:")
                    print("1. Incorrect API configuration")
                    print("2. Missing permissions")
                    print("3. API endpoint not available")
                    self.fail(f"API Error 400: {error_message}")
                else:
                    print("\nUnexpected error occurred")
                    self.fail(f"{error_type}: {error_message}")
                    
        except ImportError as e:
            print(f"\nImport Error: {e}")
            self.skipTest("Grounded query processor module not available")


def detailed_diagnostic():
    """Run a detailed diagnostic to understand the grounding failure."""
    print("=== Detailed Grounding Diagnostic ===\n")
    
    # 1. Check imports and module structure
    print("1. Checking module structure...")
    try:
        import utils
        print(f"✓ Utils module location: {utils.__file__}")
        
        # List contents of utils directory
        import os
        utils_dir = os.path.dirname(utils.__file__)
        if os.path.exists(utils_dir):
            print(f"✓ Utils directory contents:")
            for file in os.listdir(utils_dir):
                if file.endswith('.py'):
                    print(f"  - {file}")
            
            # Check specifically for grounded_query_processor
            grounded_file = os.path.join(utils_dir, 'grounded_query_processor.py')
            if os.path.exists(grounded_file):
                print(f"✓ Found grounded_query_processor.py")
                # Show first few lines to understand structure
                with open(grounded_file, 'r') as f:
                    lines = [f.readline() for _ in range(10)]
                    print("  File preview:")
                    for i, line in enumerate(lines):
                        if line.strip():
                            print(f"    {i+1}: {line.strip()}")
            else:
                print(f"✗ grounded_query_processor.py not found at {grounded_file}")
    except Exception as e:
        print(f"✗ Error checking modules: {e}")
    
    # 2. Check authentication and project settings
    print("\n2. Checking authentication...")
    try:
        import google.auth
        credentials, project_id = google.auth.default()
        print(f"✓ Authentication successful (Project: {project_id})")
        
        # Check environment variables
        print("\nEnvironment variables:")
        for var in ['PROJECT_ID', 'DATASET_ID', 'TABLE_ID', 'GOOGLE_APPLICATION_CREDENTIALS']:
            value = os.environ.get(var, 'Not set')
            print(f"  {var}: {value}")
    except Exception as e:
        print(f"✗ Authentication error: {e}")
    
    # 3. Check API availability
    print("\n3. Checking API availability...")
    try:
        from google.cloud import aiplatform
        aiplatform.init(project=os.getenv('PROJECT_ID', 'massi-financial-analysis'))
        print("✓ Google Cloud AI Platform initialized")
        
        # Check if search is available
        print("\nChecking search functionality...")
        # This would attempt to use the search feature if it were available
        # Since it's not, we expect this to fail with the specific error
        
    except Exception as e:
        print(f"✗ API error: {e}")
    
    # 4. Attempt to trace the error
    print("\n4. Tracing the error...")
    try:
        # Simulate what the app does
        from app import FinancialDataApp
        app = FinancialDataApp()
        
        # Check if grounding is enabled by default
        print(f"App grounding enabled: {getattr(app, 'use_grounding', 'Not set')}")
        
        # Try to process a simple query and catch the exact error
        test_query = "What was the military budget for 2022?"
        print(f"\nTesting query: '{test_query}'")
        
        # Check if the method exists and what it does
        if hasattr(app, '_process_grounded_query'):
            print("✓ App has _process_grounded_query method")
        else:
            print("✗ App doesn't have _process_grounded_query method")
            
    except Exception as e:
        print(f"✗ Error tracing: {e}")
    
    # 5. Provide recommendations
    print("\n5. Recommendations:")
    print("Based on the logs showing '400 Search Grounding is not supported':")
    print("1. The Search Grounding feature is not available in your project")
    print("2. Comment out or disable grounding in your app:")
    print("   Option A: Set self.use_grounding = False")
    print("   Option B: Comment out calls to grounding functions")
    print("3. The app should fall back to regular query processing")


if __name__ == "__main__":
    # Run the detailed diagnostic first
    detailed_diagnostic()
    
    print("\n" + "="*50)
    print("Running unit tests...")
    print("="*50 + "\n")
    
    # Run the tests
    unittest.main(argv=[''], exit=False)