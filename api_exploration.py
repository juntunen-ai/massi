import logging
from utils.api_client import TutkihallintoaAPI
import json

logging.basicConfig(level=logging.INFO)

def explore_api():
    """Explore the Tutkihallintoa API to understand available data."""
    
    api = TutkihallintoaAPI()
    
    # Get available years
    print("\n=== Checking Available Years ===")
    available_years = api.get_available_years()
    print(f"Available years: {available_years}")
    
    # Get sample data structure
    print("\n=== Exploring Data Structure ===")
    structure = api.sample_data_structure()
    print(f"Data structure sample:")
    print(json.dumps(structure, indent=2, ensure_ascii=False))
    
    # If we have available years, get sample data for most recent year/month
    if available_years:
        recent_year = available_years[-1]
        print(f"\n=== Sample Data from {recent_year}-01 ===")
        sample_df = api.get_monthly_data(recent_year, 1)
        if sample_df is not None:
            print(f"Retrieved {len(sample_df)} records")
            print("\nSample columns:")
            print(sample_df.columns.tolist())
            print("\nSample data (first 5 rows):")
            print(sample_df.head().to_string())
        
if __name__ == "__main__":
    explore_api()