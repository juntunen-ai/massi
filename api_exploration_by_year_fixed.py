import requests
import logging
import time
import json
import pandas as pd
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TutkihallintoaAPI:
    """Client for interacting with the Tutkihallintoa API for Finnish government financial data."""
    
    BASE_URL = "https://api.tutkihallintoa.fi/valtiontalous/v1/budjettitaloudentapahtumat"
    
    def __init__(self):
        """Initialize the API client."""
        self.session = requests.Session()
        # Minimum time between requests in seconds to avoid rate limiting
        self.request_delay = 3.0
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        """Ensure we wait enough time between requests to avoid rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.info(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def make_request(self, params):
        """
        Make a request to the API with the given parameters and handle response carefully.
        """
        self._respect_rate_limit()
        
        try:
            logger.info(f"Making API request with params: {params}")
            response = self.session.get(self.BASE_URL, params=params)
            
            # Log response status
            logger.info(f"Response status code: {response.status_code}")
            
            # Check if response is successful (status code 200-299)
            if not response.ok:
                logger.warning(f"API returned non-success status code: {response.status_code}, response: {response.text[:200]}")
                return None
            
            # Try to get content length
            content_length = len(response.content)
            logger.info(f"Response content length: {content_length} bytes")
            
            # Check if response content is empty
            if content_length == 0:
                logger.warning("Response content is empty")
                return None
            
            # Log the first 200 characters of the response to help debug
            logger.info(f"Response preview: {response.text[:200]}...")
            
            try:
                data = response.json()
                
                if isinstance(data, list):
                    logger.info(f"API request successful, received {len(data)} records")
                else:
                    logger.info(f"API request successful, received non-list response: {data}")
                
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response content (first 500 bytes): {response.content[:500]}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    
    def test_with_year_range(self, year):
        """
        Test a request with a specific year.
        """
        # Include both year parameters and a hallinnonala (administrative branch)
        test_params = {
            'hallinnonala': '28',  # Ministry of Defense
            'yearFrom': year,
            'yearTo': year
        }
        return self.make_request(test_params)
    
    def explore_individual_years(self, years_to_check):
        """
        Explore data availability for individual years.
        """
        results = {}
        
        for year in years_to_check:
            logger.info(f"Checking data for year {year}")
            
            result = self.test_with_year_range(year)
            
            if result is not None and isinstance(result, list) and len(result) > 0:
                logger.info(f"Data available for year {year}: {len(result)} records")
                results[str(year)] = {
                    "available": True,
                    "count": len(result),
                    "sample": result[0] if len(result) > 0 else None,
                    "fields": list(result[0].keys()) if len(result) > 0 else []
                }
            else:
                logger.info(f"No data available for year {year}")
                results[str(year)] = {
                    "available": False
                }
        
        return results

def main():
    api = TutkihallintoaAPI()
    
    # List of years to check individually
    years_to_check = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    
    print("\n=== Exploring Individual Years ===")
    results = api.explore_individual_years(years_to_check)
    
    # Summarize findings
    print("\n=== Summary of Available Data ===")
    available_years = []
    
    for year_str, year_data in results.items():
        if year_data.get("available", False):
            available_years.append(year_str)
            print(f"Year {year_str}: Data AVAILABLE ({year_data.get('count', 0)} records)")
            
            # If we have fields info, display it
            if "fields" in year_data:
                print(f"  Fields: {', '.join(year_data['fields'])}")
            
            # If we have a sample, show a preview
            if "sample" in year_data:
                print(f"  Sample data:")
                print(json.dumps(year_data["sample"], indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print(f"Year {year_str}: NO DATA")
    
    print(f"\nAvailable years: {', '.join(available_years)}")
    
    # Export detailed results to JSON for later analysis
    with open("api_exploration_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nDetailed results saved to api_exploration_results.json")

if __name__ == "__main__":
    main()