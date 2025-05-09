"""
Query input component for the Streamlit UI.
"""

import streamlit as st
from typing import Callable, Optional
import logging
import re
from utils.logger import setup_logger

logger = setup_logger(__name__)

class QueryInput:
    """Component for entering natural language queries."""
    
    def __init__(self, on_query_submit: Callable[[str], None]):
        """
        Initialize the query input component.
        
        Args:
            on_query_submit (Callable[[str], None]): Callback function when query is submitted
        """
        self.logger = setup_logger(__name__)
        self.logger.info("QueryInput component initialized")
        self.on_query_submit = on_query_submit
        
        # Define validation rules
        self.max_query_length = 500
        self.min_query_length = 3
        
        # Example queries
        self.example_queries = [
            "What was the defense budget for 2022?",
            "Compare defense spending between 2022 and 2023 by quarter",
            "How has the education budget changed from 2020 to 2023?",
            "Show me the top 5 ministries by spending in 2023",
            "What is the trend of government net cash flow in 2023 by month?",
            "How much has defense spending grown between 2020 and 2024?",
            "Compare budget utilization rates across ministries in 2023"
        ]
    
    def _validate_query(self, query: str) -> Optional[str]:
        """
        Validate the user query.
        
        Args:
            query (str): User input query
            
        Returns:
            Optional[str]: Error message if validation fails, None if valid
        """
        # Remove extra whitespace
        query = query.strip()
        
        # Check length
        if len(query) < self.min_query_length:
            return f"Query too short. Minimum {self.min_query_length} characters required."
        if len(query) > self.max_query_length:
            return f"Query too long. Maximum {self.max_query_length} characters allowed."
        
        # Check for suspicious patterns (basic SQL injection prevention)
        suspicious_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r';\s*UPDATE\s+SET',
            r';\s*TRUNCATE',
            r'/\*.*\*/',
            r'--.*$',
            r';\s*ALTER\s+TABLE'
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return "Query contains potentially unsafe content."
        
        # Check for minimum meaningful content
        if not re.search(r'\w+', query):
            return "Please enter a meaningful query."
        
        return None

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize the user query.
        
        Args:
            query (str): User input query
            
        Returns:
            str: Sanitized query
        """
        # Remove control characters but preserve Finnish characters
        query = re.sub(r'[\x00-\x1F\x7F]', '', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Preserve Finnish characters but remove others
        query = re.sub(r'[^\w\säöüÄÖÜéèêëîïôûç,.?!-]', '', query)
        
        return query

    def render(self):
        """Render the query input component with validation."""
        st.title("Budjettihaukka")
        st.markdown("""
        Ask questions about Finnish government budgets and finances in natural language.
        The system will convert your question to SQL, retrieve the data, and provide visualizations.
        """)

        # Query input with form
        with st.form(key="query_form"):
            query = st.text_area(
                "Enter your question about Finnish government finances:",
                height=100,
                placeholder="e.g., How has the defense budget changed from 2020 to 2023?",
                max_chars=self.max_query_length
            )

            submit_button = st.form_submit_button(label="Submit Query", use_container_width=True)

        # Process form submission with validation
        if submit_button:
            if query:
                # Validate query
                error_message = self._validate_query(query)
                if error_message:
                    st.error(error_message)
                else:
                    # Sanitize and process query
                    sanitized_query = self._sanitize_query(query)
                    self._process_query(sanitized_query)
            else:
                st.warning("Please enter a query.")

        # Example queries - OUTSIDE the form
        st.markdown("#### Example queries:")

        # Create 3 columns for example buttons
        example_cols = st.columns(3)

        for i, example in enumerate(self.example_queries):
            col_idx = i % 3
            with example_cols[col_idx]:
                # Use unique keys for each button
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    # Process example query directly (no validation needed)
                    self._process_query(example)

        # Display the selected example query in the text area if set
        if "query_form_query" in st.session_state:
            st.text_area(
                "Selected example:",
                value=st.session_state["query_form_query"],
                height=100,
                disabled=True
            )
    
    def _process_query(self, query: str):
        """
        Process a submitted query with structured logging.
        
        Args:
            query (str): Natural language query
        """
        self.logger.info(f"Processing query", extra={
            'query': query,
            'query_length': len(query)
        })

        # Store the query in session state before calling the callback
        st.session_state.current_query = query

        # Call the callback function with the query
        self.on_query_submit(query)

        # Force a rerun to update the display
        st.rerun()