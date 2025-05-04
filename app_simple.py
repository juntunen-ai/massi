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
from utils.visualization import FinancialDataVisualizer

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
    
    def handle_query(self, query: str):
        """
        Handle natural language query submission.
        
        Args:
            query (str): Natural language query
        """
        logger.info(f"Handling query: {query}")
        
        # Show processing indicator
        with st.spinner("Processing your query..."):
            # Step 1: Generate mock SQL
            sql, explanation, mock_query_type = self._generate_sql_from_nl(query)
            
            # Step 2: Execute query on mock data
            if mock_query_type != "default":
                result_df = self.data_provider.generate_example_data(mock_query_type)
            else:
                result_df = self.data_provider.execute_query(sql)
            
            if result_df is None or result_df.empty:
                explanation = "The query returned no data. Please try a different question or time period."
                self.visualization_display.render_results(query, sql, explanation, None)
                return
            
            # Step 3: Determine visualization type
            viz_type, viz_title = self._recommend_visualization(query, result_df)
            
            # Step 4: Generate natural language explanation of results
            result_explanation = self._explain_results(query, sql, result_df)
            
            # Store the explanation in session state for display
            st.session_state.result_explanation = result_explanation
            
            # Step 5: Display results
            self.visualization_display.render_results(
                query, sql, explanation, result_df, viz_type, viz_title
            )
    
    def _generate_sql_from_nl(self, query: str) -> tuple:
        """
        Generate SQL from natural language query (simplified mock version).
        
        Args:
            query (str): Natural language query
            
        Returns:
            tuple: (SQL query, explanation)
        """
        # Map common question patterns to SQL templates
        query_lower = query.lower()
        
        if "military budget" in query_lower and "2022" in query_lower:
            sql = """
            SELECT 
              SUM(Alkuperäinen_talousarvio) as original_budget,
              SUM(Voimassaoleva_talousarvio) as current_budget
            FROM 
              budget_data
            WHERE 
              Vuosi = 2022 
              AND Ha_Tunnus = 26
            """
            explanation = "This query calculates the total original and current defense budget for 2022."
            mock_query_type = "military_budget_2022"
            
        elif "defense spending" in query_lower and "quarter" in query_lower and "2022" in query_lower and "2023" in query_lower:
            sql = """
            SELECT 
              Vuosi as year,
              CEIL(Kk/3) as quarter,
              SUM(Voimassaoleva_talousarvio) as budget,
              SUM(Nettokertymä) as spending
            FROM 
              budget_data
            WHERE 
              Vuosi IN (2022, 2023)
              AND Ha_Tunnus = 26
            GROUP BY 
              year, quarter
            ORDER BY 
              year, quarter
            """
            explanation = "This query compares defense spending between 2022 and 2023 by quarter, showing both the budget and actual spending."
            mock_query_type = "defense_quarterly_2022_2023"
            
        elif "education budget" in query_lower and "2020" in query_lower and "2023" in query_lower:
            sql = """
            SELECT 
              Vuosi as year,
              SUM(Alkuperäinen_talousarvio) as original_budget,
              SUM(Voimassaoleva_talousarvio) as current_budget,
              SUM(Nettokertymä) as spending
            FROM 
              budget_data
            WHERE 
              Vuosi BETWEEN 2020 AND 2023
              AND Ha_Tunnus = 28
            GROUP BY 
              year
            ORDER BY 
              year
            """
            explanation = "This query shows the development of the education budget from 2020 to 2023, including original budget, current budget, and actual spending."
            mock_query_type = "education_budget_trend"
            
        elif "top 5 ministries" in query_lower and "2023" in query_lower:
            sql = """
            SELECT 
              Hallinnonala as ministry,
              SUM(Nettokertymä) as spending
            FROM 
              budget_data
            WHERE 
              Vuosi = 2023
            GROUP BY 
              ministry
            ORDER BY 
              spending DESC
            LIMIT 5
            """
            explanation = "This query identifies the top 5 ministries by spending in 2023."
            mock_query_type = "top_ministries_2023"
            
        else:
            # Default query
            sql = """
            SELECT 
              Vuosi as year,
              SUM(Voimassaoleva_talousarvio) as budget,
              SUM(Nettokertymä) as spending
            FROM 
              budget_data
            GROUP BY 
              year
            ORDER BY 
              year
            """
            explanation = "This is a default query that shows the total budget and spending by year."
            mock_query_type = "default"
        
        return sql, explanation, mock_query_type

    def _explain_results(self, query: str, sql: str, df: pd.DataFrame) -> str:
        """
        Generate natural language explanation of results (mock version).
        
        Args:
            query (str): Original natural language query
            sql (str): SQL query used
            df (pd.DataFrame): Result DataFrame
            
        Returns:
            str: Explanation of results
        """
        # Default explanation
        explanation = "Here are the results of your query. "
        
        # Extract some basic statistics
        if len(df) > 0:
            if 'year' in df.columns or 'Vuosi' in df.columns:
                year_col = 'year' if 'year' in df.columns else 'Vuosi'
                min_year = df[year_col].min()
                max_year = df[year_col].max()
                explanation += f"The data covers the period from {min_year} to {max_year}. "
            
            # If we have budget and spending columns
            if 'budget' in df.columns and 'spending' in df.columns:
                total_budget = df['budget'].sum()
                total_spending = df['spending'].sum()
                utilization = (total_spending / total_budget) * 100
                
                explanation += f"The total budget was {total_budget:,.2f} euros, with actual spending of {total_spending:,.2f} euros, "
                explanation += f"representing a budget utilization rate of {utilization:.1f}%. "
                
                # Check for trend
                if len(df) > 1 and 'year' in df.columns:
                    first_year = df.iloc[0]['year']
                    last_year = df.iloc[-1]['year']
                    first_spending = df.iloc[0]['spending']
                    last_spending = df.iloc[-1]['spending']
                    
                    change = (last_spending - first_spending) / first_spending * 100
                    if change > 0:
                        explanation += f"Spending increased by {change:.1f}% from {first_year} to {last_year}."
                    else:
                        explanation += f"Spending decreased by {abs(change):.1f}% from {first_year} to {last_year}."
            
            # If we have original_budget and current_budget
            elif 'original_budget' in df.columns and 'current_budget' in df.columns:
                total_original = df['original_budget'].sum()
                total_current = df['current_budget'].sum()
                change = (total_current - total_original) / total_original * 100
                
                explanation += f"The original budget was {total_original:,.2f} euros, which was adjusted to {total_current:,.2f} euros, "
                explanation += f"representing a {change:.1f}% change."
        
        return explanation

    def _recommend_visualization(self, query: str, df: pd.DataFrame) -> tuple:
        """
        Recommend visualization type (mock version).
        
        Args:
            query (str): Original natural language query
            df (pd.DataFrame): Result DataFrame
            
        Returns:
            tuple: (viz_type, viz_title)
        """
        viz_type = "table"  # Default
        
        # Time series detection
        time_cols = [col for col in df.columns if col.lower() in ['year', 'vuosi', 'quarter', 'month', 'kk']]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # Determine visualization type
        if time_cols and numeric_cols:
            # Time series data
            if len(df) > 1:
                if len(numeric_cols) > 1:
                    viz_type = "time_multi_line"
                else:
                    viz_type = "time_line"
            else:
                viz_type = "single_value"
        elif len(df) <= 10 and numeric_cols:
            # Small number of categories
            viz_type = "pie"
        elif len(df) > 10 and numeric_cols:
            viz_type = "bar"
        
        # Generate a title based on the query
        viz_title = query.strip().capitalize()
        
        return viz_type, viz_title

    def handle_filter_change(self, filters: Dict[str, Any]):
        """
        Handle filter changes from sidebar.
        
        Args:
            filters (Dict[str, Any]): Updated filters
        """
        logger.info(f"Filter change: {filters}")
        
        # Apply filters to current query if one exists
        if 'current_query' in st.session_state:
            # Modify the query to incorporate filters
            query = st.session_state.current_query
            
            # Run the query again with new filters
            self.handle_query(query)
    
    def run(self):
        """Run the application."""
        # Render sidebar
        self.sidebar.render()
        
        # Main content area
        self.query_input.render()
        
        # If there's a current result in session state, display it
        if 'current_query' in st.session_state and 'result_explanation' in st.session_state:
            # We would need to reconstruct the state here
            # This is left as an exercise for a more complete implementation
            pass

def main():
    """Main entry point for the application."""
    app = FinancialDataApp()
    app.run()

if __name__ == "__main__":
    main()