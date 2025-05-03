import requests
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import time
import io

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
        self.request_delay = 1.0
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

    def get_available_years(self) -> List[int]:
        """
        Determine the range of available years in the dataset.
        
        Returns:
            List[int]: List of available years
        """
        # Start with current year and work backwards
        current_year = datetime.now().year
        available_years = []
        
        # Try each year from present back to 2000
        # We'll stop once we get an empty response
        for year in range(current_year, 1999, -1):
            params = {
                'yearFrom': year,
                'yearTo': year,
                'monthFrom': 1,
                'monthTo': 1
            }
            
            logger.info(f"Checking data availability for year {year}")
            response = self.make_request(params)
            
            # If we get data, add the year to our list
            if response is not None and not response.empty:
                available_years.append(year)
                logger.info(f"Data available for year {year}")
            else:
                logger.info(f"No data available for year {year}")
                # If we get 3 consecutive years with no data, assume we've reached the limit
                if len(available_years) > 0 and available_years[-1] != year + 1:
                    break
        
        return sorted(available_years)
    
    def make_request(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Make a request to the API with the given parameters and return result as DataFrame.
        
        Args:
            params (Dict[str, Any]): Query parameters
            
        Returns:
            Optional[pd.DataFrame]: API response as DataFrame or None if request failed
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
            
            # Parse CSV data
            try:
                # Use pandas to read CSV data from the response content
                df = pd.read_csv(io.StringIO(response.text), sep=',')
                logger.info(f"Successfully parsed CSV data with {len(df)} rows and {len(df.columns)} columns")
                return df
            except Exception as e:
                logger.error(f"Failed to parse CSV response: {str(e)}")
                logger.error(f"Response content (first 500 bytes): {response.content[:500]}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
    
    def get_monthly_data(self, year: int, month: int) -> Optional[pd.DataFrame]:
        """
        Get data for a specific year and month.
        
        Args:
            year (int): Year to fetch
            month (int): Month to fetch (1-12)
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the data or None if request failed
        """
        params = {
            'yearFrom': year,
            'yearTo': year,
            'monthFrom': month,
            'monthTo': month
        }
        
        return self.make_request(params)

    def sample_data_structure(self) -> Dict[str, Any]:
        """
        Get a sample of the data structure by fetching a small amount of recent data.
        
        Returns:
            Dict[str, Any]: Information about the data structure
        """
        # Get the most recent year with data
        available_years = self.get_available_years()
        
        if not available_years:
            return {"error": "No data available"}
        
        recent_year = available_years[-1]
        
        # Get January data for the most recent year
        params = {
            'yearFrom': recent_year,
            'yearTo': recent_year,
            'monthFrom': 1,
            'monthTo': 1,
            # Limit results if possible
        }
        
        response = self.make_request(params)
        
        if response is None or response.empty:
            return {"error": "No sample data available"}
        
        # Get the first item as a sample
        sample_item = response.iloc[0].to_dict()
        
        # Create a structure report
        structure = {
            "sample_item": sample_item,
            "fields": list(sample_item.keys()),
            "total_sample_items": len(response)
        }
        
        return structure

    def test_api_with_required_params(self):
        """
        Test the API with different parameter combinations to find what's required.
        """
        # Test with a hallinnonala (administrative branch) parameter
        # Common hallinnonala values: 23 (Ministry of Finance), 28 (Ministry of Defense)
        params = {
            'hallinnonala': '28',  # Try with Ministry of Defense
            'yearFrom': 2022,
            'yearTo': 2022,
            'monthFrom': 1,
            'monthTo': 12
        }
        
        return self.make_request(params)

    def test_different_params(self):
        """Test different parameter combinations to understand what works."""
        test_cases = [
            # Test case 1: Just hallinnonala (administrative branch)
            {'hallinnonala': '28'},
            
            # Test case 2: Hallinnonala with year range
            {'hallinnonala': '28', 'yearFrom': 2022, 'yearTo': 2022},
            
            # Test case 3: Pääluokka (main class)
            {'paaluokka': '28'},
            
            # Test case 4: Luku (chapter)
            {'luku': '2810'},
            
            # Test case 5: Momentti (budget moment)
            {'momentti': '281001'}
        ]
        
        results = {}
        for i, params in enumerate(test_cases):
            logger.info(f"Testing case {i+1}: {params}")
            result = self.make_request(params)
            results[f"case_{i+1}"] = {
                "params": params,
                "success": result is not None,
                "data_length": len(result) if result is not None and not result.empty else 0
            }
        
        return results

    def get_data_for_period(self, year_from: int, year_to: int, month_from: int, month_to: int, 
                           hallinnonala: str = '28') -> Optional[pd.DataFrame]:
        """
        Get data for a specific time period.
        
        Args:
            year_from (int): Start year
            year_to (int): End year
            month_from (int): Start month
            month_to (int): End month
            hallinnonala (str): Administrative branch code (default: '28' - Ministry of Defense)
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the data or None if request failed
        """
        params = {
            'yearFrom': year_from,
            'yearTo': year_to,
            'monthFrom': month_from,
            'monthTo': month_to,
            'hallinnonala': hallinnonala
        }
        
        return self.make_request(params)

    def get_data_by_year(self, year: int, hallinnonala: str = '28') -> Optional[pd.DataFrame]:
        """
        Get data for a specific year.
        
        Args:
            year (int): Year to fetch
            hallinnonala (str): Administrative branch code (default: '28' - Ministry of Defense)
            
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the data or None if request failed
        """
        return self.get_data_for_period(year, year, 1, 12, hallinnonala)