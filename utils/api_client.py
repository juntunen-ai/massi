import requests
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import time
import io
from utils.secrets_manager import secrets_manager
import google.generativeai as genai
from utils.errors import APIError

# Use centralized secrets manager for API key retrieval
api_key = secrets_manager.get_api_key_ai_studio()
if not hasattr(genai, '_configured'):
        genai.configure(api_key=api_key)
        genai._configured = True

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Commenting out the original TutkihallintoaAPI class
# class TutkihallintoaAPI:
#     """Client for interacting with the Tutkihallintoa API for Finnish government financial data."""
#     ...existing code...

# Adding a dummy implementation of the TutkihallintoaAPI class
class TutkihallintoaAPI:
    """
    Dummy client that doesn't make actual API calls.
    API functionality has been disabled and replaced with this stub implementation.
    """
    
    def __init__(self):
        """Initialize the dummy API client."""
        logger.info("Initializing DISABLED API client - no API calls will be made")
    
    def get_available_years(self) -> List[int]:
        """
        Return a fixed list of years.
        
        Returns:
            List[int]: List of available years
        """
        logger.info("API DISABLED: Returning hardcoded list of years")
        return [2020, 2021, 2022, 2023, 2024]
    
    def make_request(self, params: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Dummy method that doesn't make actual API calls.
        
        Args:
            params (Dict[str, Any]): Query parameters
            
        Returns:
            None: Always returns None since API is disabled
        """
        logger.warning("API DISABLED: make_request() called but API is disabled")
        logger.info(f"Would have requested with params: {params}")
        return None
    
    def get_monthly_data(self, year: int, month: int) -> Optional[pd.DataFrame]:
        """
        Dummy method that doesn't make actual API calls.
        
        Args:
            year (int): Year to fetch
            month (int): Month to fetch (1-12)
            
        Returns:
            None: Always returns None since API is disabled
        """
        logger.warning(f"API DISABLED: get_monthly_data() called for {year}-{month} but API is disabled")
        return None

    def sample_data_structure(self) -> Dict[str, Any]:
        """
        Return a dummy data structure description.
        
        Returns:
            Dict[str, Any]: Dummy data structure info
        """
        logger.warning("API DISABLED: sample_data_structure() called but API is disabled")
        return {
            "note": "API is disabled. This is dummy data for development only.",
            "fields": [
                "Vuosi", "Kk", "Ha_Tunnus", "Hallinnonala", "Alkuperäinen_talousarvio",
                "Voimassaoleva_talousarvio", "Nettokertymä"
            ],
            "total_sample_items": 0
        }

    def test_api_with_required_params(self):
        """
        Dummy method that doesn't make actual API calls.
        """
        logger.warning("API DISABLED: test_api_with_required_params() called but API is disabled")
        return None

    def test_different_params(self):
        """
        Dummy method that doesn't make actual API calls.
        """
        logger.warning("API DISABLED: test_different_params() called but API is disabled")
        return {"note": "API is disabled. This is dummy data for development only."}

    def get_data_for_period(self, year_from: int, year_to: int, month_from: int, month_to: int, 
                           hallinnonala: str = '28') -> Optional[pd.DataFrame]:
        """
        Dummy method that doesn't make actual API calls.
        """
        logger.warning(f"API DISABLED: get_data_for_period() called for {year_from}-{month_from} to {year_to}-{month_to} but API is disabled")
        return None

    def get_data_by_year(self, year: int, hallinnonala: str = '28') -> Optional[pd.DataFrame]:
        """
        Dummy method that doesn't make actual API calls.
        """
        logger.warning(f"API DISABLED: get_data_by_year() called for {year} but API is disabled")
        return None