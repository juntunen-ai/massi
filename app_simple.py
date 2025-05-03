"""
Simplified application file for Finnish Government Budget Explorer.
This version uses mock data instead of real API and database connections.
"""

import streamlit as st
import logging
import pandas as pd
import json
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import components
from components.query_input import QueryInput
from components.visualization_display import VisualizationDisplay
from components.sidebar import Sidebar

# Import utility functions
from utils.mock_data import MockDataProvider
from utils.simple_visualization import FinancialDataVisualizer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="Finnish Government Budget Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

class FinancialDataApp:
    """Main application class for Finnish Government Budget Explorer."""
    
    def __init__(self):
        """Initialize the application."""
        # Initialize mock data provider
        self.data_provider = MockDataProvider()
        
        # Initialize visualization component
        self.visualizer = FinancialDataVisualizer()
        
        # Initialize UI components
        self.query_input = QueryInput(on_query_submit=self.handle_query)
        self.visualization_display = VisualizationDisplay()
        
        # Load available years from mock data
        self.load_available_years()
    
    def load_available_years(self):
        """Load available years from mock data."""
        years = self.data_provider.get_available_years()
        st.session_state.available_years = years
        logger.info(f"Loaded available years: {years}")
        
        # Initialize sidebar
        self.sidebar = Sidebar(
            available_years=st.session_state.available_years,
            on_filter_change=self.handle_filter_change
        )

    # ...existing code...

if __name__ == "__main__":
    main()