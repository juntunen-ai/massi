import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_api_query():
    """Test a simple query to the API from March 2022 to March 2025."""
    
    BASE_URL = "https://api.tutkihallintoa.fi/valtiontalous/v1/budjettitaloudentapahtumat"
    
    # Parameters from March 2022 to March 2025 (exactly 3 years)
    params = {
        'yearFrom': 2022,
        'yearTo': 2025,
        'monthFrom': 3,
        'monthTo': 3,
        'hallinnonala': '28'  # Ministry of Defense
    }
    
    logger.info(f"Making API request with params: {params}")
    
    try:
        response = requests.get(BASE_URL, params=params)
        logger.info(f"Response status code: {response.status_code}")
        
        if response.ok:
            try:
                data = response.json()
                logger.info(f"Successful JSON response with {len(data) if isinstance(data, list) else 'non-list'} data")
                
                # Save the data to a file for inspection
                with open("api_test_result.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"Query successful! {'Received ' + str(len(data)) + ' records' if isinstance(data, list) else 'Response: ' + str(data)}")
                print("Results saved to api_test_result.json")
                
                # If we have list data, show a sample
                if isinstance(data, list) and len(data) > 0:
                    print("\nSample record:")
                    print(json.dumps(data[0], indent=2, ensure_ascii=False))
                    
                    print("\nAvailable fields:")
                    print(list(data[0].keys()))
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                print(f"Failed to parse API response as JSON: {str(e)}")
                
                # Print the raw response content for debugging
                print("\nRaw response content (first 500 characters):")
                print(response.text[:500])
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            print(f"API request failed with status {response.status_code}")
            print(f"Error message: {response.text}")

    except Exception as e:
        logger.error(f"Exception while making API request: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("=== Testing API with Query from March 2022 to March 2025 ===")
    test_simple_api_query()