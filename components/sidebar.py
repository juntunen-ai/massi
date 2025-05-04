"""
Sidebar component for the Streamlit UI.
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Sidebar:
    """Component for the sidebar with filters and settings."""
    
    def __init__(self, available_years: List[int], on_filter_change: Callable[[Dict[str, Any]], None]):
        """
        Initialize the sidebar component.
        
        Args:
            available_years (List[int]): List of available years in the dataset
            on_filter_change (Callable[[Dict[str, Any]], None]): Callback function when filters change
        """
        self.available_years = available_years or []
        self.on_filter_change = on_filter_change
        
        # Administrative branches mapping (common ones)
        self.admin_branches = {
            "All": "All",
            "23": "Ministry of Finance",
            "24": "Ministry of Justice",
            "25": "Ministry of Interior",
            "26": "Ministry of Defense",
            "27": "Ministry of Social Affairs and Health",
            "28": "Ministry of Education",
            "29": "Ministry of Agriculture and Forestry",
            "30": "Ministry of Transport and Communications",
            "31": "Ministry of Economic Affairs and Employment",
            "32": "Ministry of Environment"
        }
    
    def render(self):
        """Render the sidebar component."""
        with st.sidebar:
            st.title("Filters & Settings")
            
            # Year filter
            self._render_year_filter()
            
            # Administrative branch filter
            self._render_branch_filter()
            
            # Aggregation level
            aggregation = st.selectbox(
                "Aggregation Level",
                options=["Year", "Quarter", "Month"],
                index=0,
                help="Select the time period granularity"
            )
            
            # Visualization preferences
            st.markdown("### Visualization")
            
            viz_type = st.selectbox(
                "Preferred Visualization",
                options=["Auto-detect", "Line Chart", "Bar Chart", "Pie Chart", "Table"],
                index=0,
                help="The system will try to use this visualization type when appropriate"
            )
            
            show_sql = st.checkbox("Show SQL Query", value=True, 
                                 help="Display the generated SQL query alongside results")
            
            # Apply button
            if st.button("Apply Filters", use_container_width=True):
                self._apply_filters(aggregation, viz_type, show_sql)
            
            # About section
            self._render_about_section()
    
    def _render_year_filter(self):
        """Render the year filter section."""
        st.markdown("### Time Period")
        
        # Get current year for defaults
        current_year = datetime.now().year
        
        # Default to last 3 years if available
        default_start_year = min(self.available_years) if self.available_years else current_year - 3
        default_end_year = max(self.available_years) if self.available_years else current_year
        
        # Year range slider
        year_range = st.slider(
            "Year Range",
            min_value=min(self.available_years) if self.available_years else 2010,
            max_value=max(self.available_years) if self.available_years else current_year,
            value=(default_start_year, default_end_year),
            step=1,
            help="Select the range of years to include in the analysis"
        )
        
        # Store in session state
        st.session_state.year_range = year_range
    
    def _render_branch_filter(self):
        """Render the administrative branch filter section."""
        st.markdown("### Administrative Branch")
        
        # Convert branch dict to more readable format for dropdown
        branch_options = [f"{name} ({code})" if code != "All" else name
                         for code, name in self.admin_branches.items()]
        
        selected_branch = st.selectbox(
            "Select Ministry",
            options=branch_options,
            index=0,
            help="Filter data by specific ministry/administrative branch"
        )
        
        # Extract the code from the selection
        if selected_branch != "All":
            # Extract code from format "Name (code)"
            branch_code = selected_branch.split("(")[1].split(")")[0]
        else:
            branch_code = "All"
        
        # Store in session state
        st.session_state.branch_code = branch_code
    
    def _apply_filters(self, aggregation: str, viz_type: str, show_sql: bool):
        """
        Apply selected filters.
        
        Args:
            aggregation (str): Selected aggregation level
            viz_type (str): Selected visualization type
            show_sql (bool): Whether to show SQL query
        """
        # Map dropdown values to expected filter values
        viz_mapping = {
            "Auto-detect": "auto",
            "Line Chart": "time_line",
            "Bar Chart": "bar",
            "Pie Chart": "pie",
            "Table": "table"
        }
        
        aggregation_mapping = {
            "Year": "yearly",
            "Quarter": "quarterly",
            "Month": "monthly"
        }
        
        # Build filter dict
        filters = {
            "year_start": st.session_state.year_range[0],
            "year_end": st.session_state.year_range[1],
            "branch_code": st.session_state.branch_code,
            "aggregation": aggregation_mapping.get(aggregation, "yearly"),
            "viz_type": viz_mapping.get(viz_type, "auto"),
            "show_sql": show_sql
        }
        
        logger.info(f"Applying filters: {filters}")
        
        # Call the callback function with filters
        self.on_filter_change(filters)
        
        # Store in session state for persistence
        st.session_state.filters = filters
    
    def _render_about_section(self):
        """Render the about section in the sidebar."""
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        Budjettihaukka allows you to explore Finnish government financial data using natural language queries.
        
        Data is sourced from the [Tutkihallintoa.fi](https://tutkihallintoa.fi/) API and covers government budget and spending data.
        
        Built with Streamlit, BigQuery, and Vertex AI.
        """)

        # Add feedback option
        st.markdown("### Feedback")
        with st.form(key="feedback_form"):
            feedback = st.text_area("Share your feedback:", height=100)
            submit_feedback = st.form_submit_button("Submit Feedback")
        
        if submit_feedback and feedback:
            # Here you would typically send the feedback to a database or email
            st.success("Thank you for your feedback!")
            logger.info(f"Received feedback: {feedback}")