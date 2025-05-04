"""
Query input component for the Streamlit UI.
"""

import streamlit as st
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class QueryInput:
    """Component for entering natural language queries."""
    
    def __init__(self, on_query_submit: Callable[[str], None]):
        """
        Initialize the query input component.
        
        Args:
            on_query_submit (Callable[[str], None]): Callback function when query is submitted
        """
        self.on_query_submit = on_query_submit
        
        # Example queries
        self.example_queries = [
            "What was the military budget for 2022?",
            "Compare defense spending between 2022 and 2023 by quarter",
            "How has the education budget changed from 2020 to 2023?",
            "Show me the top 5 ministries by spending in 2023",
            "What is the trend of government net cash flow in 2023 by month?",
            "How much has defense spending grown between 2020 and 2024?",
            "Compare budget utilization rates across ministries in 2023"
        ]
    
    def render(self):
        """Render the query input component."""
        st.title("Budjettihaukka")  # Changed from "Finnish Government Budget Explorer"
        st.markdown("""
        Ask questions about Finnish government budgets and finances in natural language.
        The system will convert your question to SQL, retrieve the data, and provide visualizations.
        """)

        # Query input with form
        with st.form(key="query_form"):
            query = st.text_area(
                "Enter your question about Finnish government finances:",
                height=100,
                placeholder="e.g., How has the defense budget changed from 2020 to 2023?"
            )

            submit_button = st.form_submit_button(label="Submit Query", use_container_width=True)

        # Process form submission
        if submit_button and query:
            self._process_query(query)

        # Example queries - OUTSIDE the form
        st.markdown("#### Example queries:")

        # Create 3 columns for example buttons
        example_cols = st.columns(3)

        for i, example in enumerate(self.example_queries):
            col_idx = i % 3
            with example_cols[col_idx]:
                if st.button(example, key=f"example_{i}", help=example, use_container_width=True):
                    # Use session state to store the selected example
                    st.session_state.selected_example = example
                    # Need to rerun to update the form with the selected example
                    st.rerun()

        # Process example selection
        if 'selected_example' in st.session_state:
            query = st.session_state.selected_example
            # Clear the selected example
            del st.session_state.selected_example
            # Process the query
            self._process_query(query)
    
    def _process_query(self, query: str):
        """
        Process a submitted query.
        
        Args:
            query (str): Natural language query
        """
        logger.info(f"Processing query: {query}")
        
        # Call the callback function with the query
        self.on_query_submit(query)
        
        # Store the query in session state for further use
        st.session_state.current_query = query