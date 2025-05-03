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
        self.request_delay = 3.0  # Increased delay further
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
            if (content_length == 0):
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

    def test_simple_request(self):
        """
        Test a very simple request to see what the API returns.
        """
        # Try the simplest possible request with a single parameter
        simple_params = {'hallinnonala': '28'}
        return self.make_request(simple_params)

    def explore_years(self, start_year, end_year):
        """
        Explore data availability for a range of years.
        """
        results = {}
        
        # First, test a simple request without year params
        logger.info("Testing simple request without year parameters")
        simple_result = self.test_simple_request()
        
        if simple_result is None:
            logger.error("Simple request failed, API may be unavailable")
            return {"error": "API unavailable"}
        
        # Test with minimal parameter combinations to avoid rate limits
        required_params = [
            # Try with common administrative branches
            {'hallinnonala': '28'},  # Ministry of Defense
        ]
        
        for year in range(start_year, end_year + 1):
            logger.info(f"Exploring data for year {year}")
            year_results = {}

            for i, base_params in enumerate(required_params):
                params = base_params.copy()
                params.update({
                    'yearFrom': year,
                    'yearTo': year,
                    'monthFrom': 1,
                    'monthTo': 1
                })

                result = self.make_request(params)
                success = result is not None and isinstance(result, list) and len(result) > 0

                year_results[f"params_{i+1}"] = {
                    "params": params,
                    "success": success,
                    "count": len(result) if success and isinstance(result, list) else 0
                }

                if success and isinstance(result, list) and len(result) > 0:
                    year_results["sample"] = result[0]
                    year_results["fields"] = list(result[0].keys())
                    break

            results[str(year)] = year_results  # Convert year to string as key

        return results

def main():
    api = TutkihallintoaAPI()
    
    # First, test basic connectivity
    print("\n=== Testing API Connectivity ===")
    simple_result = api.test_simple_request()
    
    if simple_result is None:
        print("❌ API connectivity test failed. Please check the logs for details.")
        return
    
    print("✅ API connectivity test successful.")
    print(f"Sample response: {simple_result[:2] if isinstance(simple_result, list) else simple_result}")
    
    # If test was successful, proceed with exploration
    print("\n=== Exploring Years 2015-2024 ===")
    results = api.explore_years(2015, 2024)
    
    # Summarize findings
    print("\n=== Summary of Available Data ===")
    for year_str, year_data in results.items():
        # Check if year_data is a dictionary
        if not isinstance(year_data, dict):
            print(f"Year {year_str}: ERROR - Unexpected data type: {type(year_data)}")
            continue
            
        has_data = False
        for param_name, params in year_data.items():
            if param_name.startswith("params_") and isinstance(params, dict) and params.get("success", False):
                has_data = True
                break
        
        if has_data:
            print(f"Year {year_str}: Data AVAILABLE")
            # If we have sample data, show the fields
            if "fields" in year_data:
                print(f"  Fields: {year_data['fields']}")
                # If we have a sample, print it
                if "sample" in year_data:
                    print(f"  Sample data:")
                    print(json.dumps(year_data["sample"], indent=2, ensure_ascii=False)[:500] + "...")
        else:
            print(f"Year {year_str}: NO DATA")
    
    # Export detailed results to JSON for later analysis
    with open("api_exploration_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nDetailed results saved to api_exploration_results.json")

if __name__ == "__main__":
    main()