import logging
from utils.api_client import TutkihallintoaAPI
import json
import pandas as pd

logging.basicConfig(level=logging.INFO)

def explore_api():
    """Explore the Tutkihallintoa API to understand available data."""
    
    api = TutkihallintoaAPI()
    
    # First, test with more specific parameters
    print("\n=== Testing API with Required Parameters ===")
    test_result = api.test_api_with_required_params()
    
    if test_result:
        print(f"API test successful! Received {len(test_result)} records")
        
        # Show sample data structure
        if len(test_result) > 0:
            sample = test_result[0]
            print("\nSample data structure:")
            print(json.dumps(sample, indent=2, ensure_ascii=False))
            
            # Show all available fields
            print("\nAvailable fields:")
            print(list(sample.keys()))
            
            # If we have multiple records, convert to DataFrame for easier analysis
            if len(test_result) > 1:
                df = pd.DataFrame(test_result)
                print("\nDataFrame Info:")
                print(df.info())
                
                print("\nSample DataFrame (first 5 rows):")
                print(df.head().to_string())
                
                # Check for year/date fields
                time_fields = [col for col in df.columns if any(time_term in col.lower() 
                                                             for time_term in ['year', 'month', 'date', 'vuosi', 'kuukausi'])]
                if time_fields:
                    print("\nTime-related fields:")
                    print(time_fields)
                    for field in time_fields:
                        print(f"\nUnique values in {field}:")
                        print(df[field].unique())
    else:
        print("API test failed. Trying different parameter combinations...")
        
        # Test different parameter combinations
        test_results = api.test_different_params()
        print("\nResults of testing different parameters:")
        print(json.dumps(test_results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    explore_api()